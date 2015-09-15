#include <chrono>
#include <thread>
#include <exception>
#include <fstream>
#define WINDOWS_LEAN_AND_MEAN
#include <Windows.h>
#include "dc1371.hpp"
#include "utilities.hpp"

#define thread_local __declspec( thread ) static

namespace linear {

    using std::string;
    using std::to_string;
    using std::ifstream;
    using std::ios;
    using std::make_pair;
    using std::this_thread::sleep_for;
    using std::chrono::milliseconds;

    const DWORD QUERY_SIGNATURE = 0x36644851;    // QHd6 -- query signature
    const DWORD ANSWER_SIGNTURE = 0x52446839;    // 9hDR -- answr signature
    const DWORD PASSWORD_SIGNTURE = 0x4B74694C;    // LitK -- passwd for commnds
    const char* PASSW_STRGTURE = "Litk";        // PASSW_SIGN as a string
    const DWORD PSTCH_IDLETURE = 0x1D497C11;    // idle code return

    enum class Opcode : BYTE {
        // RW suffix means read or write (depending on byte param)

        NONE = 0,
        COMMAND_RESET = 's',
        GET_DEMO_ID = 'i',
        ALLOW_WRITES = 'e',  // set/clear allow_writes
        BOARD_RESET = 'b',  // board reset and other operations
        GET_INFO = 'c',

        LOAD_FPGA_RAW = 'f',
        LOAD_FPGA = 'j',
        COLLECT = 'g',  // capture ADC data
        READY_FPGA = 'h', // get the FPGA ready to collect
        READ_SRAM = 'a',
        WRITE_SRAM = 'd',

        DEMO_ID_EERPOM_RW = 'k',
        ATMEL_EEPROM_RW = 'n',
        ATMEL_MSD_FLASH_RW = 'o',
        FPGA_REG_RW = 'l',
        FPGA_LIST_RW = 'm', // Read or write a list of FPGA registers
        TEST_RW = 'p', // test and performance commands
        CHIT_CHAT = 'q', // "I don't know (I/O test?)"
        SPI = 'r',
        I2C = 't',
        CONFIG = 'u',
    };

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
    const int BLOCK_SIZE = 512;
    const int MAX_BLOCKS = 32;
    const int SAMPLE_SIZE = 2;
    const int KILOSAMPLES = 1024;
    const int MAX_TOTAL_SAMPLES = 1024 * KILOSAMPLES;
    const string Dc1371::DESCRIPTION = "DC1371A ADC Controller board";

#define SPI_MUST_NOT_BE_TOO_LARGE(offset, maximum) if ((offset) > (maximum)) { throw invalid_argument("SPI transaction too large."); }

    struct CommandHeader {
        DWORD   signature;
        Opcode  opcode;
        BYTE    byte_param;
        WORD    word_param;
        union {
            DWORD value;
            BYTE    bytes[4];
            struct { BYTE byte_0, byte_1, byte_2, byte_3; };
            struct { WORD word_0, word_1; };
        } dword_param_1;
        union {
            DWORD value;
            BYTE    bytes[4];
            struct { BYTE byte_0, byte_1, byte_2, byte_3; };
            struct { WORD word_0, word_1; };
        } dword_param_2;
        CommandHeader(Opcode opcode) : signature(QUERY_SIGNATURE), opcode(opcode) { }
        BYTE GetStatus() { return byte_param; }
        WORD GetLength() { return word_param; }
        void SetLength(WORD length) { word_param = length; }
        void SetNumBlocks(WORD num_blocks) { word_param = num_blocks; }
        void SetAddress(WORD address) { dword_param_1.word_0; }
        void SetTail(WORD tails) { dword_param_1.word_0; }
    };

    const int COMMAND_DATA_SIZE = BLOCK_SIZE - sizeof(CommandHeader);
    //    For commands that carry some data in the CMDB block, we limit
    //    the max amount so that some space is available behind db[] for
    //    various uses at the receiving end.  Also, it's convenient to
    //    have it be the EEPROM page size, which is 16 bytes. So...
    //
    const int MAX_COMMAND_DATA = COMMAND_DATA_SIZE - 16;

    struct Dc1371::Command {
        CommandHeader header;
        BYTE data[COMMAND_DATA_SIZE];
        Command(Opcode opcode) : header(opcode) {
            memset(data, 0, COMMAND_DATA_SIZE);
        }
        void Reset(Opcode opcode) {
            memset(this, 0, sizeof(Command));
            header.opcode = opcode;
        }
    };

    class Dc1371::CommandFile {
        HANDLE file = INVALID_HANDLE_VALUE;
        CommandFile(const CommandFile& other) = delete;
    public:
        CommandFile(char drive_letter) {
            char file_name[10] = " :\\pipe.0";
            file_name[0] = drive_letter;
            file = CreateFileA(file_name, GENERIC_READ | GENERIC_WRITE, 0, nullptr,
                OPEN_EXISTING, FILE_FLAG_NO_BUFFERING | FILE_FLAG_WRITE_THROUGH, nullptr);
            if (file == INVALID_HANDLE_VALUE) {
                throw HardwareError("Error opening DC1371A command interface.");
            }
        }
        CommandFile(CommandFile&& other) : file(other.file) {
            other.file = INVALID_HANDLE_VALUE;
        }
        ~CommandFile() {
            Close();
        }
        void Close() {
            if (file != INVALID_HANDLE_VALUE) {
                SetFilePointer(file, 0, nullptr, FILE_BEGIN);
                SetEndOfFile(file);
                CloseHandle(file);
                file = INVALID_HANDLE_VALUE;
            }
        }

        void Write(Command& command) {
            SetFilePointer(file, 0, nullptr, FILE_BEGIN);
            DWORD num_written;
            if (!WriteFile(file, &command, BLOCK_SIZE, &num_written, nullptr)) {
                throw HardwareError("Error writing to DC1371A command interface.");
            }
        }

        void Read(Command& command) {
            SetFilePointer(file, 0, nullptr, FILE_BEGIN);
            DWORD num_read;
            if (!ReadFile(file, &command, BLOCK_SIZE, &num_read, nullptr)) {
                throw HardwareError("Error reading from DC1371A command interface.");
            }
        }
    };

    class Dc1371::BlockFile {
        HANDLE file = INVALID_HANDLE_VALUE;
        BlockFile(const CommandFile& other) = delete;
    public:
        BlockFile(char drive_letter) {
            char file_name[10] = " :\\pipe.1";
            file_name[0] = drive_letter;
            file = CreateFileA(file_name, GENERIC_READ | GENERIC_WRITE, 0, nullptr,
                OPEN_EXISTING, FILE_FLAG_NO_BUFFERING | FILE_FLAG_WRITE_THROUGH, nullptr);
            if (file == INVALID_HANDLE_VALUE) {
                throw HardwareError("Error opening DC1371A block interface.");
            }
        }
        BlockFile(BlockFile&& other) : file(other.file) {
            other.file = INVALID_HANDLE_VALUE;
        }
        ~BlockFile() {
            Close();
        }
        void Close() {
            if (file != INVALID_HANDLE_VALUE) {
                CloseHandle(file);
                file = INVALID_HANDLE_VALUE;
            }
        }
        void Write(const BYTE data[], int num_bytes) {
            SetFilePointer(file, 0, nullptr, FILE_BEGIN);
            DWORD num_written;
            if (!WriteFile(file, data, num_bytes, &num_written, nullptr)) {
                throw HardwareError("Error writing to DC1371A block interface.");
            }
        }
        void Write(const char data[], int num_chars) {
            SetFilePointer(file, 0, nullptr, FILE_BEGIN);
            DWORD num_written;
            if (!WriteFile(file, data, num_chars, &num_written, nullptr)) {
                throw HardwareError("Error writing to DC1371A block interface.");
            }
        }
        void Read(BYTE data[], int num_bytes) {
            SetFilePointer(file, 0, nullptr, FILE_BEGIN);
            DWORD num_read;
            if (!ReadFile(file, data, num_bytes, &num_read, nullptr)) {
                throw HardwareError("Error reading from DC1371A block interface.");
            }
        }
        void Read(char data[], int num_chars) {
            SetFilePointer(file, 0, nullptr, FILE_BEGIN);
            DWORD num_read;
            if (!ReadFile(file, data, num_chars, &num_read, nullptr)) {
                throw HardwareError("Error reading from DC1371A block interface.");
            }
        }
    };

    int Dc1371::GetNumControllers(int max_controllers) {
        MUST_BE_POSITIVE(max_controllers);
        MUST_NOT_BE_LARGER(max_controllers, MAX_CONTROLLERS);

        const int DRIVE_STRINGS_SIZE = 20;
        char root_path_name[DRIVE_STRINGS_SIZE] = " :\\";
        char volume_name[DRIVE_STRINGS_SIZE] = "";
        char file_system_name[DRIVE_STRINGS_SIZE] = "";
        DWORD dummy_value;

        int num_controllers = 0;
        for (char drive_letter = 'D'; drive_letter <= 'Z'; drive_letter++) {
            root_path_name[0] = drive_letter;
            if (!GetVolumeInformationA(root_path_name, volume_name, DRIVE_STRINGS_SIZE, &dummy_value,
                &dummy_value, &dummy_value, file_system_name, DRIVE_STRINGS_SIZE)) {
                continue;
            }
            if (_strcmpi(volume_name, "pstache") == 0) {
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

        const int DRIVE_STRINGS_SIZE = 20;
        char root_path_name[DRIVE_STRINGS_SIZE] = " :\\";
        char volume_name[DRIVE_STRINGS_SIZE] = "";
        char file_system_name[DRIVE_STRINGS_SIZE] = "";
        DWORD dummy_value;

        vector<LccControllerInfo> info_list;
        for (char drive_letter = 'D'; drive_letter <= 'Z'; drive_letter++) {
            root_path_name[0] = drive_letter;
            if (!GetVolumeInformationA(root_path_name, volume_name, DRIVE_STRINGS_SIZE, &dummy_value,
                &dummy_value, &dummy_value, file_system_name, DRIVE_STRINGS_SIZE)) {
                continue;
            }
            if (_strcmpi(volume_name, "pstache") == 0) {
                auto info = Controller::MakeControllerInfo(Type::DC1371, DESCRIPTION, "", drive_letter);
                {
                    Dc1371 dc1371(info);
                    CopyToBuffer(info.serial_number, sizeof(info.serial_number), 
                        dc1371.GetSerialNumber().c_str());
                }
                info_list.push_back(info);
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

    int Dc1371::FpgaLoadFileChunked(const string& fpga_filename) {
        auto load_id = GetFpgaLoadIdFromFile(fpga_filename);
        auto fpga_path = Path(ToUtf16(fpga_filename));
        auto fpga_path_string = fpga_path.Fullpath();

        if (!DoesFileExist(fpga_path_string)) {
            auto location = GetPathFromRegistry(L"SOFTWARE\\Linear Technology\\LinearLabTools");
            fpga_path = Path(location + L"fpga_loads", fpga_path.BaseName(), L".sqz");
            if (!DoesFileExist(fpga_path.Fullpath())) {
                throw runtime_error("Could not find file " + ToUtf8(fpga_path.Fullpath()));
            }
            fpga_path_string = fpga_path.Fullpath();
        }

        auto size = GetFileSize(fpga_path_string);
        if (size < 1) {
            throw runtime_error("Could not read file (or is empty) " + ToUtf8(fpga_path.Fullpath()));
        }
        
        ifstream fpga_file(fpga_path_string, std::ios::binary | std::ios::beg);
        if (!fpga_file) {
            throw runtime_error("Could not open file " + ToUtf8(fpga_path.Fullpath()));
        }

        // Original code calclulates a "tail" which is the last block and may be partial.
        // However the actual file read and send loop assumes the tail is a full block.
        // The implmementation of the squeeze algorithm pads to a full block so this code
        // assumes a full tail throughout.
        auto num_blocks = WORD(size / BLOCK_SIZE);

        Command command(Opcode::LOAD_FPGA);
        command.header.word_param = num_blocks;

        CommandFile command_file(drive_letter);
        BlockFile block_file(drive_letter);

        command_file.Write(command);

        std::vector<char> data(Min(MAX_BLOCKS, int(num_blocks)) * BLOCK_SIZE);
        while (num_blocks > 0) {
            auto send_blocks = Min(MAX_BLOCKS, int(num_blocks));
            auto send_bytes = send_blocks * BLOCK_SIZE;
            if (!fpga_file.read(data.data(), send_bytes)) {
                throw runtime_error("Error reading file " + ToUtf8(fpga_path.Fullpath()));
            }

            block_file.Write(data.data(), send_bytes);
            
            num_blocks -= send_blocks;
            if (num_blocks == 0) {
                CheckCommandResult(command, command_file);
            } else {
                auto status = GetCommandResult(command, command_file);
                if (status != Dc1371Error::GOT_ACK) {
                    throw Dc1371Error("DC1371A reported an error.", status);
                }
            }
        }
        command_file.Close();
        try {
            FpgaGetIsLoaded(load_id);
        } catch (HardwareError&) {
            sleep_for(milliseconds(50));
            FpgaGetIsLoaded(load_id);
        }
        return 0;
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
        
        Command command(Opcode::CONFIG);
        // the bit in the high byte enables setting the generic_config, the bit in the low byte
        // enables setting the demo_config
        command.header.word_param = 0x0101;
        command.header.dword_param_1.value = generic_config;
        command.header.dword_param_2.value = demo_config;

        CommandFile command_file(drive_letter);
        command_file.Write(command);
        command.Reset(Opcode::COLLECT);
        command.header.byte_param = trigger_value;
        command.header.SetLength(total_samples / KILOSAMPLES);
        command_file.Write(command);
    }

    bool Dc1371::DataIsCollectDone() {
        CommandFile command_file(drive_letter);
        Command command(Opcode::COLLECT);
        command_file.Write(command);
        auto status = GetCommandResult(command, command_file);
        if (status == Dc1371Error::GOT_NAK) {
            return false;
        } else if (status == Dc1371Error::OK) {
            return true;
        } else {
            throw Dc1371Error("The DC1371 gave an unexpected status", status);
        }
    }

    void Dc1371::DataCancelCollect() {
        Reset();
    }

    int Dc1371::ReadBytes(uint8_t data[], int total_bytes) {
        // guarantee the running_abortable_operation flag gets cleared on exit
        auto& reading_flag = is_reading; // can't capture a field
        auto raii_reading_flag = MakeRaiiCleanup([&reading_flag] { reading_flag = false; });
        is_reading = true;

        MUST_NOT_BE_NULL(data);
        MUST_BE_POSITIVE(total_bytes);
        MUST_NOT_BE_LARGER(total_bytes, 2 * MAX_TOTAL_SAMPLES);

        CommandFile command_file(drive_letter);
        BlockFile block_file(drive_letter);
        Command command(Opcode::READ_SRAM);
        command.header.byte_param = initialize_ram ? 0x01 : 0x00;
        initialize_ram = false;
        int bytes_read = 0;
        int total_blocks = total_bytes / BLOCK_SIZE;
        int bytes_in_extra_block = total_bytes - (total_blocks * BLOCK_SIZE);
        while (total_blocks > 0) {
            if (abort_read) {
                return LCC_ERROR_ABORTED;
            }
            WORD num_blocks = Min(MAX_BLOCKS, total_blocks);
            int block_bytes = num_blocks * BLOCK_SIZE;
            command.header.word_param = num_blocks;
            command_file.Write(command);
            command.header.byte_param = 0x00;
            block_file.Read(data, block_bytes);

            total_blocks -= num_blocks;
            data += block_bytes;
            bytes_read += block_bytes;
        }
        if (bytes_in_extra_block > 0) {
            if (abort_read) {
                return LCC_ERROR_ABORTED;
            }
            // this case means the user put in a data size that was smaller than the collect size
            // and not a multiple of 256 samples, so we read one block and put part of it into the
            // data.
            command.header.word_param = 1;
            command_file.Write(command);
            uint8_t last_block[BLOCK_SIZE];
            block_file.Read(last_block, BLOCK_SIZE);
            memcpy_s(data, bytes_in_extra_block, last_block, bytes_in_extra_block);

            bytes_read += bytes_in_extra_block;
        }
        return bytes_read;
    }

    void Dc1371::DataCancelReceive() {
        abort_read = true;
        int i;
        for (i = 0; is_reading && i < 1000; ++i) {
            sleep_for(milliseconds(5));
        }
        abort_read = false;
        if (i == 1000) {
            try {
                Reset();
            } catch (...) { }
            throw HardwareError("Abort operation timed out.");
        } else {
            Reset();
        }
    }
    
    void Dc1371::SpiBufferLowerChipSelect(Command& command, int& offset) {
        const int CHIP_SELECT_DOWN_COMMAND_SIZE = 3;
        SPI_MUST_NOT_BE_TOO_LARGE(offset + CHIP_SELECT_DOWN_COMMAND_SIZE, MAX_COMMAND_DATA);
        auto spi_chars = reinterpret_cast<char*>(command.data + offset);
        sprintf_s(spi_chars, MAX_COMMAND_DATA - offset, "s%02d", int(chip_select));
        offset += CHIP_SELECT_DOWN_COMMAND_SIZE;
    }

    void  Dc1371::SpiBufferRaiseChipSelect(Command& command, int& offset) {
        const int CHIP_SELECT_UP_COMMAND_SIZE = 1;
        SPI_MUST_NOT_BE_TOO_LARGE(offset + CHIP_SELECT_UP_COMMAND_SIZE, MAX_COMMAND_DATA);
        command.data[offset] = 'p';
        ++offset;
    }

    void  Dc1371::SpiBufferSendOrTranceive(Command& command, int& offset,
            uint8_t send_values[], int num_values, bool is_send) {
        int command_size = 2 * num_values + 1;
        SPI_MUST_NOT_BE_TOO_LARGE(command_size, MAX_COMMAND_DATA);
        auto spi_chars = reinterpret_cast<char*>(command.data + offset);
        *spi_chars = is_send ? 'w' : 't';
        ++spi_chars;
        char hex[3];
        for (int i = 0; i < num_values; ++i) {
            sprintf_s(hex, "%02X", send_values[i]);
            spi_chars[0] = hex[0];
            spi_chars[1] = hex[1];
            spi_chars += 2;
        }
        offset += command_size;
    }

    void Dc1371::SpiBufferReceive(Command& command, int& offset, int num_values) {
        const int RECEIVE_COMMAND_SIZE = 3;
        SPI_MUST_NOT_BE_TOO_LARGE(offset + RECEIVE_COMMAND_SIZE, MAX_COMMAND_DATA);
        auto spi_chars = reinterpret_cast<char*>(command.data + offset);
        sprintf_s(spi_chars, sizeof(command.data) - offset, "r%02X", num_values);
        offset += RECEIVE_COMMAND_SIZE;
    }

    void Dc1371::SpiDoTransaction(Command& command, uint8_t* receive_values, int num_values) {
        CommandFile command_file(drive_letter);
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
                std::to_string(uint8_t(command.header.opcode)) + ").");
        }

        auto result = command.header.GetStatus();
        if ((result == Dc1371Error::OK) && (data != nullptr) && (num_data > 0)) {
            memcpy_s(data, num_data, command.data, Min(num_data, int(command.header.GetLength())));
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

    const int MAX_SPI_READ_BYTES = (MAX_COMMAND_DATA - 1) / 2;
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

        Command command(Opcode::DEMO_ID_EERPOM_RW);
        command.header.byte_param = READ;
        command.header.word_param = buffer_size;
        command.header.SetAddress((eeprom_address << 1) | 0x01);
        CommandFile command_file(drive_letter);
        command_file.Write(command);

        CheckCommandResult(command, command_file, reinterpret_cast<uint8_t*>(buffer), buffer_size);
    }

}