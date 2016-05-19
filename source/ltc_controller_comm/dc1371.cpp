#include <chrono>
#include <thread>
#include <exception>
#include <fstream>
#define WINDOWS_LEAN_AND_MEAN
#include <Windows.h>
#include "dc1371.hpp"
#include "utilities.hpp"

namespace linear {

    using std::string;
    using std::to_string;
    using std::ifstream;
    using std::ios;
    using std::make_pair;
    using std::this_thread::sleep_for;
    using std::chrono::milliseconds;
    using std::make_unique;

    const DWORD ANSWER_SIGNTURE = 0x52446839;    // 9hDR -- answr signature
    const DWORD PASSWORD_SIGNTURE = 0x4B74694C;    // LitK -- passwd for commnds
    const char* PASSW_STRGTURE = "Litk";        // PASSW_SIGN as a string
    const DWORD PSTCH_IDLETURE = 0x1D497C11;    // idle code return

    enum : BYTE {
        READ = 0x80,
        WRITE = 0x00,
        ABORT = 0xF8,
    };

    // BOARD_RESET args
    enum : BYTE {
        DFU_LOADER = 0,
        RESET_BOARD = 1,
        DETACH = 2,
    };

    enum : BYTE {
        TRIGGER_NONE = 0,
        TRIGGER_START = 1,
        TRIGGER_STOP = 2,
    };

#undef ENUM_START
#define ENUM_START const string Dc1371Error::strings[NUM_ERRORS] = {
#undef ENUM
#define ENUM(name, value) #name
    ENUM_DECLARATION;

    // Other constants

    const int SAMPLE_SIZE = 2;
    const int KILOSAMPLES = 1024;
    const int MAX_TOTAL_SAMPLES = 1024 * KILOSAMPLES;
    const string Dc1371::DESCRIPTION = "DC1371A ADC Controller board";

#define SPI_MUST_NOT_BE_TOO_LARGE(offset, maximum) if ((offset) > (maximum)) { throw invalid_argument("SPI transaction too large."); }

    bool Dc1371::IsDc1371(char drive_letter) {
        const int DRIVE_STRINGS_SIZE = 20;
        char root_path_name[DRIVE_STRINGS_SIZE] = " :\\";
        char volume_name[DRIVE_STRINGS_SIZE] = "";
        char file_system_name[DRIVE_STRINGS_SIZE] = "";
        DWORD dummy_value;

        root_path_name[0] = drive_letter;
        if (!GetVolumeInformationA(root_path_name, volume_name, DRIVE_STRINGS_SIZE, &dummy_value,
                                   &dummy_value, &dummy_value, file_system_name, DRIVE_STRINGS_SIZE)) {
            return false;
        }
        return _strcmpi(volume_name, "pstache") == 0;
    }

    LccControllerInfo Dc1371::MakeControllerInfo(char drive_letter) {
        auto info = Controller::MakeControllerInfo(Type::DC1371, DESCRIPTION, "", drive_letter);
        {
            Dc1371 dc1371(info);
            CopyToBuffer(info.serial_number, sizeof(info.serial_number),
                         dc1371.GetSerialNumber().c_str());
        }
        return info;
    }

    int Dc1371::GetNumControllers(int max_controllers) {
        MUST_BE_POSITIVE(max_controllers);
        MUST_NOT_BE_LARGER(max_controllers, MAX_CONTROLLERS);

        int num_controllers = 0;
        for (char drive_letter = 'D'; drive_letter <= 'Z'; drive_letter++) {
            if (IsDc1371(drive_letter)) {
                ++num_controllers;
                if (num_controllers >= max_controllers) {
                    break;
                }
            }
        }
        return num_controllers;
    }

    vector<LccControllerInfo> Dc1371::ListControllers(int max_controllers) {
        MUST_BE_POSITIVE(max_controllers);
        MUST_NOT_BE_LARGER(max_controllers, MAX_CONTROLLERS);

        vector<LccControllerInfo> info_list;
        for (char drive_letter = 'D'; drive_letter <= 'Z'; drive_letter++) {
            if (IsDc1371(drive_letter)) {
                info_list.push_back(MakeControllerInfo(drive_letter));
                if (info_list.size() >= unsigned(max_controllers)) {
                    break;
                }
            }
        }
        return info_list;
    }

    string Dc1371::GetSerialNumber() {
        Reset();
        Command command(Opcode::GET_INFO);
        CommandFile command_file(drive_letter);
        command_file.Write(command);
        char buffer[LCC_MAX_SERIAL_NUMBER_SIZE];
        CheckCommandResult(command, command_file, reinterpret_cast<uint8_t*>(buffer),
            LCC_MAX_SERIAL_NUMBER_SIZE);
        return string(buffer);
    }

    void Dc1371::Reset() {
        CommandFile(drive_letter).Write(Command(Opcode::COMMAND_RESET));
    }

    uint8_t GetFpgaLoadIdFromFile(string fpga_filename) {
        // File names are "S2157.sqz", "S2175.sqz", "S2195.sqz", "S2274.sqz", "S9011.sqz"
        
        auto fpga_path = Path(ToUtf16(fpga_filename));

        if ((fpga_path.BaseName()[0] & 0xDF) != 'S') {
            throw invalid_argument(fpga_filename + "is not a valid FPGA load file");
        }

        long number = strtol(fpga_filename.c_str() + 1, nullptr, 10);

        switch (number) {
        case 2274:
            return 1;
        case 2175:
            return 2;
        case 2157:
            return 3;
        case 9011:
            return 4;
        case 2195:
            return 5;
        default:
            throw invalid_argument(fpga_filename + "is not a valid FPGA load file");
        }
    }

    bool Dc1371::FpgaGetIsLoaded(uint8_t fpga_load_id) {
        Command command(Opcode::READY_FPGA);
        command.header.byte_param = fpga_load_id;
        CommandFile command_file(drive_letter);
        command_file.Write(command);
        auto result = GetCommandResult(command, command_file);
        if (result == Dc1371Error::FPGA_ID_ERROR) {
            return false;
        } else if (result == Dc1371Error::OK) {
            return true;
        } else {
            throw Dc1371Error("DC1371 returned unexpected status", result);
        }
    }

    bool Dc1371::FpgaGetIsLoaded(const string& fpga_filename) {
        auto load_id = GetFpgaLoadIdFromFile(fpga_filename);
        return FpgaGetIsLoaded(load_id);
    }

    void Dc1371::FpgaStartLoadFile(const string& fpga_filename) {
        fpga_load_started = true;
        auto load_id = GetFpgaLoadIdFromFile(fpga_filename);
        auto path = Path(ToUtf16(fpga_filename));
        auto path_string = path.Fullpath();

        if (!DoesFileExist(path_string)) {
            auto location = GetPathFromRegistry(L"SOFTWARE\\Linear Technology\\LinearLabTools");
            path = Path(location + L"fpga_loads", path.BaseName(), L".sqz");
            if (!DoesFileExist(path.Fullpath())) {
                throw runtime_error("Could not find file " + ToUtf8(path.Fullpath()));
            }
            path_string = path.Fullpath();
        }

        auto size = GetFileSize(path_string);
        if (size < 1) {
            throw runtime_error("Could not read file (or is empty) " + ToUtf8(path.Fullpath()));
        }

        // Original code calclulates a "tail" which is the last block and may be partial.
        // However the actual file read and send loop assumes the tail is a full block.
        // The implmementation of the squeeze algorithm pads to a full block so this code
        // assumes a full tail throughout.
        auto num_blocks = Narrow<WORD>(size / BLOCK_SIZE);

        Command command(Opcode::LOAD_FPGA);
        command.header.SetNumBlocks(num_blocks);
        command.header.SetTail(BLOCK_SIZE);

        fpga_load_info = make_unique<FpgaLoadInfo>(path_string, load_id,
            num_blocks, drive_letter);

        try {
            fpga_load_info->command_file.Write(command);
        } catch (HardwareError&) {
            fpga_load_info.reset();
            throw;
        }
    }

    void Dc1371::FpgaLoadChunk() {
        try {
            auto send_blocks = Min(MAX_BLOCKS, fpga_load_info->num_blocks);
            auto send_bytes = send_blocks * BLOCK_SIZE;
            ifstream input(fpga_load_info->path, ios::binary | ios::beg);
            if (!input.seekg(fpga_load_info->offset, ios::beg)) {
                throw runtime_error("Error reading file " + ToUtf8(fpga_load_info->path));
            }
            if (!input.read(fpga_load_info->data.data(), send_bytes)) {
                throw runtime_error("Error reading file " + ToUtf8(fpga_load_info->path));
            }
            fpga_load_info->offset += send_bytes;

            fpga_load_info->block_file.Write(fpga_load_info->data.data(), send_bytes);
            fpga_load_info->num_blocks -= send_blocks;

            Command command(Opcode::LOAD_FPGA);
            if (fpga_load_info->num_blocks == 0) {
                CheckCommandResult(command, fpga_load_info->command_file);
            } else {
                auto status = GetCommandResult(command, fpga_load_info->command_file);
                if (status != Dc1371Error::GOT_ACK) {
                    throw Dc1371Error("DC1371A reported an error.", status);
                }
            }
        } catch (HardwareError&) {
            fpga_load_info.reset();
            throw;
        }
    }

    void Dc1371::FpgaFinishLoadFile() {
        auto load_id = fpga_load_info->load_id;
        fpga_load_info.reset();
        FpgaGetIsLoaded(load_id);
        fpga_load_started = false;
    }

    int Dc1371::FpgaLoadFileChunked(const string& fpga_filename) {
        if (!fpga_load_started) {
            FpgaStartLoadFile(fpga_filename);
        } else {
            FpgaLoadChunk();
            if (fpga_load_info->num_blocks == 0) {
                FpgaFinishLoadFile();
                return 0;
            }
        }
        return fpga_load_info->num_blocks;
    }

    void Dc1371::FpgaCancelLoad() {
        fpga_load_info.reset();
        fpga_load_started = false;
        Reset();
    }

    void Dc1371::DataStartCollect(int total_samples, Trigger trigger) {
        BYTE trigger_value = LCC_TRIGGER_NONE;
        switch (trigger) {
        case Trigger::NONE:
            initialize_ram = true;
            break;
        case Trigger::START_POSITIVE_EDGE:
            trigger_value = LCC_TRIGGER_START_POSITIVE_EDGE;
            initialize_ram = true;
            break;
        case Trigger::DC1371_STOP_NEGATIVE_EDGE:
            trigger_value = LCC_TRIGGER_DC1371_STOP_NEGATIVE_EDGE;
            initialize_ram = false;
            break;
        default:
            throw invalid_argument(
                "trigger must be NONE, START_ON_POSITIVE_EDGE or DC1371_STOP_ON_NEGATIVE_EDGE.");
        }

        auto total_bytes = total_samples * SAMPLE_SIZE;

        MUST_NOT_BE_SMALLER(total_samples, KILOSAMPLES);
        MUST_NOT_BE_LARGER(total_samples, MAX_TOTAL_SAMPLES);
        if (total_samples % KILOSAMPLES != 0) {
            throw invalid_argument("Number of samples must be a multiple of 1024.");
        }
        
        collect_command_file = make_unique<CommandFile>(drive_letter);
        try {
            Command command(Opcode::COMMAND_RESET);
            collect_command_file->Write(command);

            command.Reset(Opcode::CONFIG);
            // the bit in the high byte enables setting the generic_config, the bit in the low byte
            // enables setting the demo_config
            command.header.word_param = 0x0101;
            command.header.dword_param_1.value = generic_config;
            command.header.dword_param_2.value = demo_config;
            collect_command_file->Write(command);

            command.Reset(Opcode::COLLECT);
            command.header.byte_param = trigger_value;
            command.header.SetLength(total_samples / KILOSAMPLES);
            collect_command_file->Write(command);

            collect_started = true;
        } catch (HardwareError&) {
            collect_command_file.reset();
            throw;
        }
    }

    bool Dc1371::DataIsCollectDone() {
        if (!collect_started) {
            throw invalid_argument("No collect was started");
        }
        try {
            Command command(Opcode::COLLECT);
            auto status = GetCommandResult(command, *(collect_command_file.get()));
            if (status == Dc1371Error::GOT_NAK) {
                return false;
            } else if (status == Dc1371Error::OK) {
                collect_command_file.reset();
                return true;
            } else {
                throw Dc1371Error("The DC1371 gave an unexpected status", status);
            }
        } catch (HardwareError&) {
            collect_command_file.reset();
            throw;
        }
    }

    void Dc1371::DataCancelCollect() {
        collect_started = false;
        collect_command_file.reset();
        Reset();
    }

    int Dc1371::ReadBytes(uint8_t data[], int total_bytes) {
        MUST_NOT_BE_NULL(data);
        MUST_BE_POSITIVE(total_bytes);
        MUST_NOT_BE_LARGER(total_bytes, 2 * MAX_TOTAL_SAMPLES);

        int total_blocks = total_bytes / BLOCK_SIZE;
        if ((total_bytes - total_blocks * BLOCK_SIZE) != 0) {
            throw invalid_argument("total_bytes must be a multiple of 512");
        }

        CommandFile command_file(drive_letter);
        BlockFile block_file(drive_letter);
        Command command(Opcode::READ_SRAM);
        command.header.byte_param = initialize_ram ? 0x01 : 0x00;
        initialize_ram = false;
        command.header.SetNumBlocks(total_blocks);
        command_file.Write(command);
        int bytes_read = 0;

        while (total_blocks > 0) {
            // these get changed by CheckCommandResult
            command.header.opcode = Opcode::READ_SRAM;
            command.header.byte_param = 0x00;

            WORD num_blocks = Min(MAX_BLOCKS, total_blocks);
            int block_bytes = num_blocks * BLOCK_SIZE;
            block_file.Read(data, block_bytes);
            
            total_blocks -= num_blocks;
            data += block_bytes;
            bytes_read += block_bytes;

            if (total_blocks == 0) {
                CheckCommandResult(command, command_file);
            } else {
                auto status = GetCommandResult(command, command_file);
                if (status != Dc1371Error::GOT_ACK) {
                    throw Dc1371Error("expected ACK during read", status);
                }
            }
        }
        return bytes_read;
    }
    
    void Dc1371::SpiBufferLowerChipSelect(Command& command, int& offset) {
        const int CHIP_SELECT_DOWN_COMMAND_SIZE = 3;
        SPI_MUST_NOT_BE_TOO_LARGE(offset + CHIP_SELECT_DOWN_COMMAND_SIZE, MAX_COMMAND_DATA);
        char* spi_chars = command.data + offset;
        sprintf_s(spi_chars, MAX_COMMAND_DATA - offset, "s%02d", Narrow<int>(chip_select));
        offset += CHIP_SELECT_DOWN_COMMAND_SIZE;
    }

    void  Dc1371::SpiBufferRaiseChipSelect(Command& command, int& offset) {
        const int CHIP_SELECT_UP_COMMAND_SIZE = 2;
        SPI_MUST_NOT_BE_TOO_LARGE(offset + CHIP_SELECT_UP_COMMAND_SIZE, MAX_COMMAND_DATA);
        command.data[offset] = 'p';
        ++offset;
        command.data[offset] = '\0';
        ++offset;
    }

    void  Dc1371::SpiBufferSendOrTranceive(Command& command, int& offset,
            uint8_t send_values[], int num_values, bool is_send) {
        int command_size = 2 * num_values + 1;
        SPI_MUST_NOT_BE_TOO_LARGE(command_size, MAX_COMMAND_DATA);
        char* spi_chars = command.data + offset;
        *spi_chars = is_send ? 'w' : 't';
        ++spi_chars;
        for (int i = 0; i < num_values; ++i) {
            sprintf_s(spi_chars, 3, "%02X", send_values[i]);
            spi_chars += 2;
        }
        offset += command_size;
    }

    void Dc1371::SpiBufferReceive(Command& command, int& offset, int num_values) {
        const int RECEIVE_COMMAND_SIZE = 3;
        SPI_MUST_NOT_BE_TOO_LARGE(offset + RECEIVE_COMMAND_SIZE, MAX_COMMAND_DATA);
        char* spi_chars = command.data + offset;
        sprintf_s(spi_chars, sizeof(command.data) - offset, "r%02X", num_values);
        offset += RECEIVE_COMMAND_SIZE;
    }

    void Dc1371::SpiDoTransaction(Command& command, uint8_t* receive_values, int num_values) {
        CommandFile command_file(drive_letter);
        command.header.word_param = Narrow<WORD>(strlen(command.data));
        command_file.Write(command);
        CheckCommandResult(command, command_file, receive_values, num_values);
    }

    void Dc1371::CheckCommandResult(Command& command, CommandFile& command_file,
            uint8_t* receive_values, int num_values) {
        auto status = GetCommandResult(command, command_file, receive_values, num_values);
        if (status != Dc1371Error::OK) {
            throw Dc1371Error("DC1371A reported an error.", status);
        }
    }

    uint8_t Dc1371::GetCommandResult(Command& command, CommandFile& command_file,
            uint8_t* data, int num_data) {
        auto original_opcode = command.header.opcode;
        command.Reset(Opcode::NONE);

        command_file.Read(command);

        if (command.header.signature != ANSWER_SIGNTURE) {
            throw HardwareError("DC1371A response signature was invalid.");
        }
        if (command.header.opcode != original_opcode) {
           throw HardwareError("DC1371A response opcode mismatch (got " +
                std::to_string(Narrow<uint8_t>(command.header.opcode)) + ").");
        }

        auto result = command.header.GetStatus();
        if ((result == Dc1371Error::OK) && (data != nullptr) && (num_data > 0)) {
            memcpy_s(data, num_data, command.data, Min(num_data, Narrow<int>(command.header.GetLength())));
        }
        return result;
    }

    void Dc1371::SpiSend(uint8_t values[], int num_values) {
        MUST_NOT_BE_NULL(values);
        MUST_BE_POSITIVE(num_values);

        Command command(Opcode::SPI);
        int offset = 0;
        SpiBufferLowerChipSelect(command, offset);
        SpiBufferSendOrTranceive(command, offset, values, num_values, true);
        SpiBufferRaiseChipSelect(command, offset);

        CommandFile command_file(drive_letter);
        command_file.Write(command);
        CheckCommandResult(command, command_file);
    }

    void Dc1371::SpiReceive(uint8_t values[], int num_values) {
        MUST_NOT_BE_NULL(values);
        MUST_BE_POSITIVE(num_values);
        MUST_NOT_BE_LARGER(num_values, MAX_SPI_READ_BYTES);

        Command command(Opcode::SPI);
        int offset = 0;
        SpiBufferLowerChipSelect(command, offset);
        SpiBufferReceive(command, offset, num_values);
        SpiBufferRaiseChipSelect(command, offset);

        CommandFile command_file(drive_letter);
        command_file.Write(command);
        CheckCommandResult(command, command_file, values, num_values);
    }

    void Dc1371::SpiTransceive(uint8_t send_values[], uint8_t receive_values[], int num_values) {
        MUST_NOT_BE_NULL(send_values);
        MUST_NOT_BE_NULL(receive_values);
        MUST_BE_POSITIVE(num_values);
        MUST_NOT_BE_LARGER(num_values, MAX_SPI_READ_BYTES);

        Command command(Opcode::SPI);
        int offset = 0;
        SpiBufferLowerChipSelect(command, offset);
        SpiBufferSendOrTranceive(command, offset, send_values, num_values, false);
        SpiBufferRaiseChipSelect(command, offset);

        CommandFile command_file(drive_letter);
        command_file.Write(command);
        CheckCommandResult(command, command_file, receive_values, num_values);
    }

    void Dc1371::SpiSendAtAddress(uint8_t address, uint8_t* values, int num_values) {
        MUST_NOT_BE_NULL(values);
        MUST_BE_POSITIVE(num_values);

        Command command(Opcode::SPI);
        int offset = 0;
        SpiBufferLowerChipSelect(command, offset);
        SpiBufferSendOrTranceive(command, offset, &address, 1, true);
        SpiBufferSendOrTranceive(command, offset, values, num_values, true);
        SpiBufferRaiseChipSelect(command, offset);
        SpiDoTransaction(command, nullptr, 0);
    }
    void Dc1371::SpiReceiveAtAddress(uint8_t address, uint8_t* values, int num_values) {
        MUST_NOT_BE_NULL(values);
        MUST_BE_POSITIVE(num_values);
        MUST_NOT_BE_LARGER(num_values, MAX_SPI_READ_BYTES);

        Command command(Opcode::SPI);
        int offset = 0;
        SpiBufferLowerChipSelect(command, offset);
        SpiBufferSendOrTranceive(command, offset, &address, 1, true);
        SpiBufferReceive(command, offset, num_values);
        SpiBufferRaiseChipSelect(command, offset);
        SpiDoTransaction(command, values, num_values);
    }

    void Dc1371::SpiSetCsState(SpiCsState chip_select_state) {
        Command command(Opcode::SPI);
        int offset = 0;
        if (chip_select_state == SpiCsState::LOW) {
            SpiBufferLowerChipSelect(command, offset);
        } else if (chip_select_state == SpiCsState::HIGH) {
            SpiBufferRaiseChipSelect(command, offset);
        } else {
            throw invalid_argument("chip_select_state must be HIGH or LOW");
        }
        return SpiDoTransaction(command, nullptr, 0);
    }

    void Dc1371::SpiSendNoChipSelect(uint8_t values[], int num_values) {
        MUST_NOT_BE_NULL(values);
        MUST_BE_POSITIVE(num_values);
        Command command(Opcode::SPI);
        int offset = 0;
        SpiBufferSendOrTranceive(command, offset, values, num_values, true);
        SpiDoTransaction(command, nullptr, 0);
    }

    void Dc1371::SpiReceiveNoChipSelect(uint8_t values[], int num_values) {
        MUST_NOT_BE_NULL(values);
        MUST_BE_POSITIVE(num_values);
        MUST_NOT_BE_LARGER(num_values, MAX_SPI_READ_BYTES);

        Command command(Opcode::SPI);
        int offset = 0;
        SpiBufferReceive(command, offset, num_values);
        SpiDoTransaction(command, values, num_values);
    }

    void Dc1371::SpiTransceiveNoChipSelect(uint8_t send_values[], uint8_t receive_values[],
            int num_values) {
        MUST_NOT_BE_NULL(send_values);
        MUST_NOT_BE_NULL(receive_values);
        MUST_BE_POSITIVE(num_values);
        MUST_NOT_BE_LARGER(num_values, MAX_SPI_READ_BYTES);

        Command command(Opcode::SPI);
        int offset = 0;
        SpiBufferSendOrTranceive(command, offset, send_values, num_values, false);
        SpiDoTransaction(command, receive_values, num_values);
    }

    void Dc1371::EepromReadString(char * buffer, int buffer_size) {
        MUST_NOT_BE_NULL(buffer);
        MUST_BE_POSITIVE(buffer_size);

        Command command(Opcode::GET_DEMO_ID);
        CommandFile command_file(drive_letter);
        command_file.Write(command);
        CheckCommandResult(command, command_file, reinterpret_cast<uint8_t*>(buffer), buffer_size);
        buffer[Min(Narrow<int>(command.header.GetLength()), buffer_size - 1)] = '\0';
    }

}