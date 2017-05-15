#include "dc890.hpp"
#include <experimental/filesystem>
#include <fstream>
#include <regex>

namespace linear {
using std::regex;
using std::regex_search;
using std::smatch;
using std::ifstream;
using std::experimental::filesystem::path;
using std::experimental::filesystem::exists;
using std::experimental::filesystem::directory_iterator;

Dc890::FpgaLoad Dc890::GetFpgaLoadIdFromFile(const string& fpga_filename) {
    // File names are "dcmosr1.sqz", "dlvdsr1.sqz", "s1407r3.sqz", "s1408r3.sqz",
    // "s2308r1.sqz" and "s2366r2.sqz", plus there are two built-in loads "cmos" and "lvds"

    if (CompareI(fpga_filename, "cmos")) {
        return FpgaLoad(2, 0);
    } else if (CompareI(fpga_filename, "lvds")) {
        return FpgaLoad(1, 0);
    }
    auto fpga_path = FpgaGetPath(fpga_filename);
    auto stem_str  = fpga_path.stem().u8string();
    int  revision  = Last<char>(stem_str) - '0';

    if (CompareFileNameStart(stem_str, "dcmos")) { return FpgaLoad(9, revision); }
    if (CompareFileNameStart(stem_str, "dlvds")) { return FpgaLoad(10, revision); }

    auto number = strtol(stem_str.c_str() + 1, nullptr, 10);
    switch (number) {
        case 1407:
            return FpgaLoad(5, revision);
        case 1408:
            return FpgaLoad(6, revision);
        case 2308:
            return FpgaLoad(7, revision);
        case 2366:
            return FpgaLoad(8, revision);
        default:
            throw invalid_argument(fpga_filename + " is not a valid FPGA load file");
    }
}

bool Dc890::FpgaGetIsLoaded(const string& fpga_filename) {
    auto load = GetFpgaLoadIdFromFile(fpga_filename);

    const uint8_t FPGA_LOAD_TYPE_ADDRESS = 5;
    const uint8_t FPGA_LOAD_TYPE_SIZE    = 2;
    const int     NUM_CHARS              = 2 * FPGA_LOAD_TYPE_SIZE + 1;

    uint8_t data[FPGA_LOAD_TYPE_SIZE];
    char    buffer[NUM_CHARS];

    Flush();

    safe_sprintf(buffer, "Q %X%X", FPGA_LOAD_TYPE_ADDRESS, FPGA_LOAD_TYPE_SIZE);
    Write(buffer, narrow<DWORD>(strlen(buffer)));
    auto num_read = Read(buffer, NUM_CHARS);
    if (num_read != NUM_CHARS) { throw HardwareError("Not all bytes of the FPGA register read."); }
    int result = HexToBytes(buffer, data, FPGA_LOAD_TYPE_SIZE);
    if (result < FPGA_LOAD_TYPE_SIZE) {
        throw HardwareError("Encountered invalid hex chars in register read.");
    }

    uint8_t revision = data[0] & 0x1F;
    uint8_t load_id  = data[1];

    return (load_id == load.load_id) && (load_id < 3 || revision == load.revision);
}

void Dc890::FpgaPageBuffer::Reset(const path& fpga_path) {
    total_bytes = 0;
    page_bytes  = 0;
    delete file;
    file = new ifstream(fpga_path.native(), std::ios::binary | std::ios::in);
    if (file->bad()) {
        delete file;
        file = nullptr;
    }
}

void Dc890::FpgaPageBuffer::Reset() {
    delete file;
    file        = nullptr;
    total_bytes = 0;
    page_bytes  = 0;
}

bool Dc890::FpgaPageBuffer::GetPage(char data[FPGA_PAGE_SIZE]) {
    char byte;
    while (file->get(byte)) {
        if (total_bytes == FPGA_SIZE) {
            throw runtime_error("Expanded file too large (bad or corrupted squeeze file?)");
        }
        buffer[page_bytes] = byte;
        ++page_bytes;
        ++total_bytes;
        if (byte == 0) {
            if (!file->get(byte)) {
                throw runtime_error("Error reading squeeze file (bad or corrupted?)");
            }
            uint8_t count = byte - 1;
            while (count != 0) {
                if (total_bytes == FPGA_SIZE) {
                    throw runtime_error("Expanded file too large (bad or corrupted squeeze file?)");
                }
                buffer[page_bytes] = 0;
                --count;
                ++page_bytes;
                ++total_bytes;
            }
        }
        if (page_bytes >= FPGA_PAGE_SIZE) {
            memcpy(data, buffer, FPGA_PAGE_SIZE);
            for (int i = FPGA_PAGE_SIZE; i < page_bytes; ++i) {
                buffer[i - FPGA_PAGE_SIZE] = buffer[i];
            }
            page_bytes -= FPGA_PAGE_SIZE;
            return true;
        }
    }
    if (total_bytes != FPGA_SIZE) {
        throw runtime_error("Expanded file too small (bad or corrupted squeeze file?)");
    }
    return false;
}

int Dc890::FpgaFileToFlashChunked(const path& fpga_path) {
    if (!fpga_load_started) {
        fpga_load_started  = true;
        fpga_page_index    = 0;
        fpga_load_progress = NUM_FPGA_PAGES;
        Write("E 3", 3);
        const int MAX_ERASE_TIME = 6000;
        SetTimeouts(MAX_ERASE_TIME);
        Read(fpga_page_data, 4);
        SetTimeouts();

        if (fpga_page_data[0] != 'A') { throw HardwareError("Did not receive ACK on SRAM erase."); }

        fpga_page_buffer.Reset(fpga_path);
    }

    if (!fpga_page_buffer) { throw runtime_error("Unable to open file " + fpga_path.u8string()); }

    const int BANK_ID = 3;
    if (fpga_page_buffer.GetPage(fpga_page_data)) {
        auto header =
                string("F ") + ToHex(narrow<uint16_t>(BANK_ID * NUM_FPGA_PAGES + fpga_page_index));
        Write(header.c_str(), narrow<DWORD>(header.size()));
        Write(fpga_page_data, FPGA_PAGE_SIZE);
        Read(fpga_page_data, 4);
        if (fpga_page_data[0] != 'A') { throw HardwareError("Did not receive ACK on SRAM write."); }
        ++fpga_page_index;
        --fpga_load_progress;
        return fpga_load_progress;
    } else {
        return 0;
    }
}

const int BANK_BUFFER_SIZE = 200;
const int BYTES_PER_BANK   = 9;
bool      Dc890::FpgaFlashToLoaded(uint16_t load_id, uint8_t revision) {
    // read the bank population data. Its 32 bits per bank, sent as 8 hex chars per bank,
    // separated by a space, first word is number of banks

    // get # banks
    Write("V", 1);
    char buffer[BANK_BUFFER_SIZE];
    Read(buffer, 4);
    int  num_banks = strtol(buffer, nullptr, 16);
    auto num_read  = Read(buffer, BYTES_PER_BANK * num_banks);
    if (num_banks == 0 || num_read != BYTES_PER_BANK * num_banks) {
        Close();
        throw HardwareError("Error reading bank information");
    }
    buffer[BYTES_PER_BANK * num_banks] = '\0';
    auto banks_hex                     = SplitString(buffer);
    bool found_load                    = false;
    int  bank;
    for (bank = 0; bank < num_banks; bank++) {
        uint16_t type = HexToByte(banks_hex[bank].c_str());
        uint8_t  rev  = HexToByte(banks_hex[bank].c_str() + 2);
        if (type == load_id) {
            if (type < 3 || rev == revision) {
                found_load = true;
                break;
            }
        }
    }

    if (!found_load) { return false; }

    bool needs_power = (HexToByte(banks_hex[bank].c_str() + 4) & 0x04) != 0;
    if (needs_power) {
        Write("s 0", 3);
        Read(buffer, 3);
        auto flag = strtol(buffer, nullptr, 16);
        if ((flag & 0x01) == 0) {
            throw HardwareError("The DC890 needs to be powered to load the FPGA.");
        }
    }

    const int FPGA_LOAD_TIMEOUT = 2000;
    // now load from FLASH into FPGA.  This is done directly with the 'e' command.
    SetTimeouts(FPGA_LOAD_TIMEOUT);
    safe_sprintf(buffer, "e %X\n", bank);
    Write(buffer, narrow<DWORD>(strlen(buffer)));
    num_read = Read(buffer, 4);
    if (num_read != 4 || buffer[0] != 'A') {
        throw HardwareError("Did not get an ACK when loading FPGA from flash.");
    }
    return true;
}

void Dc890::FpgaCancelLoad() {
    Reset();
    fpga_load_started  = false;
    fpga_load_progress = NUM_FPGA_PAGES;
    fpga_page_index    = 0;
    fpga_page_buffer.Reset();
    Close();
}

static std::tuple<bool, string> FindFpgaFile(const path& fpga_path) {
    auto directory = fpga_path.parent_path();
    auto stem_str  = fpga_path.stem().u8string();
    for (auto&& p : directory_iterator(directory)) {
        if (CompareFileNameStart(p.path().stem().u8string(), stem_str)) {
            return std::make_tuple(true, p.path().u8string());
        }
    }
    return std::make_tuple(false, "");
}

path Dc890::FpgaGetPath(const string& fpga_filename) {
    if (CompareI(fpga_filename, "cmos") || CompareI(fpga_filename, "lvds")) {
        return fpga_filename;
    }
    auto fpga_path = path(fpga_filename);
    if (exists(fpga_path)) { return fpga_path; }

    if (fpga_path.has_parent_path()) {
        auto result = FindFpgaFile(fpga_path);
        if (std::get<0>(result)) { return std::get<1>(result); }
    }

    auto location = GetInstallPath().append("fpga_loads");

    auto result = FindFpgaFile(location.append(fpga_filename));
    if (std::get<0>(result)) { return std::get<1>(result); }

    throw invalid_argument("Invalid load file name.");
}

int Dc890::FpgaLoadFileChunked(const path& fpga_path) {
    auto fpga_str = fpga_path.u8string();
    if (!fpga_load_started) {
        auto load         = GetFpgaLoadIdFromFile(fpga_str);
        auto flash_result = FpgaFlashToLoaded(load.load_id, load.revision);

        if ((load.load_id == 1 || load.load_id == 2) && !flash_result) {
            Close();
            throw HardwareError(
                    "Couldn't find builtin load but load routine did not report error.");
        }

        if (flash_result) { return 0; }
    }
    auto progress = FpgaFileToFlashChunked(fpga_path);
    if (progress == 0) {
        fpga_load_started = false;
        auto load         = GetFpgaLoadIdFromFile(fpga_str);
        bool is_loaded    = FpgaFlashToLoaded(load.load_id, load.revision);
        if (!is_loaded) {
            Close();
            throw HardwareError(
                    "Couldn't find load in flash but load routine did not report error.");
        }
    }
    return progress;
}

void Dc890::GpioSendByte(uint8_t byte) {
    // some IO expander boards get into a weird sleep state when power droops, so we send
    // 0 to 0xFF (which means the read bit is set, but oh well) just to wake it up before
    // the real command is sent.
    string buffer = "MIsSFFS00sS40S" + ToHex(byte) + "p";
    Write(buffer.c_str(), narrow<DWORD>(buffer.size()));
}

void Dc890::SpiSend(uint8_t* values, int num_values) {
    SpiSetCsState(SpiCsState::LOW);
    SpiSendNoChipSelect(values, num_values);
    SpiSetCsState(SpiCsState::HIGH);
}

void Dc890::SpiSendAtAddress(uint8_t address, uint8_t values[], int num_values) {
    SpiSetCsState(SpiCsState::LOW);
    SpiSendNoChipSelect(&address, 1);
    SpiSendNoChipSelect(values, num_values);
    SpiSetCsState(SpiCsState::HIGH);
}

void Dc890::SpiSetCsState(SpiCsState chip_select_level) {
    if (sck_bit_mask == 0 && sdi_bit_mask == 0 && base_byte == 0 && cs_bit_mask == 0) {
        throw invalid_argument(
                "Need to set SPI bits and base byte before doing SPI transactions over I2C");
    }
    if (chip_select_level == SpiCsState::HIGH) {
        base_byte |= cs_bit_mask;
    } else if (chip_select_level == SpiCsState::LOW) {
        base_byte &= ~cs_bit_mask;
    } else {
        throw invalid_argument("chip_select_level must be HIGH or LOW");
    }
    return GpioSendByte(base_byte);
}

void Dc890::SpiSendNoChipSelect(uint8_t* values, int num_values) {
    if (sck_bit_mask == 0 && sdi_bit_mask == 0 && base_byte == 0 && cs_bit_mask == 0) {
        throw invalid_argument(
                "Need to set SPI bits and base byte before doing SPI transactions over I2C");
    }

    uint8_t value     = base_byte & ~sck_bit_mask & ~sdi_bit_mask;
    string  sck_low_0 = ToHex(value);
    value             = base_byte & ~sck_bit_mask | sdi_bit_mask;
    string sck_low_1  = ToHex(value);
    value             = base_byte | sck_bit_mask & ~sdi_bit_mask;
    string sck_high_0 = ToHex(value);
    value             = base_byte | sck_bit_mask | sdi_bit_mask;
    string sck_high_1 = ToHex(value);

    string clock_out_0 = "S" + sck_low_0 + "S" + sck_high_0 + "S" + sck_low_0;
    string clock_out_1 = "S" + sck_low_1 + "S" + sck_high_1 + "S" + sck_low_1;

    for (int i = 0; i < num_values; ++i) {
        string  buffer = "MIsS40";
        uint8_t value  = values[i];
        for (int j = 0; j < 8; ++j) {
            buffer += value & 0x80 ? clock_out_1 : clock_out_0;
            value <<= 1;
        }
        buffer += 'p';
        Write(buffer.c_str(), narrow<DWORD>(buffer.size()));
    }
}
}