#pragma once
#include <vector>
#include <string>
#include <cstdint>
#include <memory>
#include "i_collect.hpp"
#include "i_reset.hpp"
#include "i_data_endian.hpp"
#include "i_data_receive.hpp"
#include "i_spi.hpp"
#include "i_fpga_load.hpp"
#include "controller.hpp"
#include "error.hpp"

using std::string;
using std::vector;
using std::unique_ptr;

namespace linear {

    class Dc1371Error : public HardwareError {
    public:
        Dc1371Error(const string& message, int error_code) : HardwareError(message, error_code) { }
        string FullMessage() override {
            if (error_code < BAD_NEGATIVE) {
                error_code = BAD_NEGATIVE;
            } else if (error_code > BAD_TOO_LARGE) {
                error_code = BAD_TOO_LARGE;
            }
            return (string(what()) + " (DC1371 error code: " + strings[error_code + 1] + ")");
        }
#undef ENUM_DECLARATION
#define ENUM_DECLARATION       \
    ENUM_START                 \
    ENUM(BAD_NEGATIVE,   -1),  \
    ENUM(OK,              0),  \
    ENUM(GOT_ACK,         1),  \
    ENUM(GOT_NAK,         2),  \
    ENUM(ABORTED,         3),  \
    ENUM(BAD_FOUR,        4),  \
    ENUM(BAD_FIVE,        5),  \
    ENUM(BAD_SIX,         6),  \
    ENUM(BAD_SEVEN,       7),  \
    ENUM(PHASE_ERROR,     8),  \
    ENUM(BAD_SIGNATURE,   9),  \
    ENUM(BAD_PASSWORD,    10), \
    ENUM(ILLEGAL_COMMAND, 11), \
    ENUM(GENERIC_ERROR,   12), \
    ENUM(FPGA_LOAD_ERROR, 13), \
    ENUM(FPGA_ID_ERROR,   14), \
    ENUM(FPGA_PLL_ERROR,  15), \
    ENUM(COLLECT_ERROR,   16), \
    ENUM(BAD_TOO_LARGE,   17), \
    ENUM_END
#define ENUM_START enum {
#define ENUM_END };
#define ENUM(name, value) name = value
        ENUM_DECLARATION;
    private:
        static const int NUM_ERRORS = BAD_TOO_LARGE + 2; // (+2 is for BAD_NEGATIVE and OK)
        static const string strings[NUM_ERRORS];
    };

    class Dc1371 : public ICollect, IReset, IDataEndian, IDataReceive, ISpi, IFpgaLoad {
    public:
        enum class ChipSelect : uint8_t {
            ONE = LCC_1371_CHIP_SELECT_ONE,
            TWO = LCC_1371_CHIP_SELECT_TWO
        };

        static int GetNumControllers(int max_controllers);
        static vector<LccControllerInfo> ListControllers(int max_controllers);
        Dc1371(const LccControllerInfo& info) : drive_letter(char(info.id)) { }
        Dc1371(const Dc1371&) = delete;
        Dc1371(Dc1371&&) = delete;
        Dc1371& operator=(const Dc1371& other) = delete;
        ~Dc1371() { }

        Type GetType() override { return Type::DC1371; }

        void Reset() override;

		bool FpgaGetIsLoaded(const string& fpga_filename) override;
        int FpgaLoadFileChunked(const string& fpga_filename) override;
        void FpgaCancelLoad() override;

		void SetGenericConfig(uint32_t generic_config) {
            this->generic_config = SwapBytes(generic_config);
        }
		void SetDemoConfig(uint32_t demo_config) { this->demo_config = SwapBytes(demo_config); }

        void DataSetHighByteFirst() override { swap_bytes = true; }
        void DataSetLowByteFirst() override { swap_bytes = false; }
		void DataStartCollect (int total_samples, Trigger trigger) override;
        bool DataIsCollectDone() override;
        void DataCancelCollect() override;
        int DataReceive(uint8_t data[], int total_bytes) override {
            return ReadBytes(data, total_bytes); 
        }
        int DataReceive(uint16_t data[], int total_values) override {
            return Controller::DataRead(*this, swap_bytes, data, total_values);
        }
        int DataReceive(uint32_t data[], int total_values) override {
            return Controller::DataRead(*this, swap_bytes, data, total_values);
        }
        void SpiChooseChipSelect(ChipSelect new_chip_select) { chip_select = new_chip_select; }

        void SpiSend(uint8_t values[], int num_values) override;
        void SpiReceive(uint8_t values[], int num_values) override;
        void SpiTransceive(uint8_t send_values[], uint8_t receive_values[],
            int num_values) override;

        // Convenience SPI functions with "address/value" mode
        void SpiSendAtAddress(uint8_t address, uint8_t* values, int num_values) override;
        void SpiSendAtAddress(uint8_t address, uint8_t value) override {
            SpiSendAtAddress(address, &value, 1);
        }
        void SpiReceiveAtAddress(uint8_t address, uint8_t* values, int num_values) override;
        uint8_t SpiReceiveAtAddress(uint8_t address) override {
            uint8_t value;
            SpiReceiveAtAddress(address, &value, 1);
            return value;
        }

        // Low-level SPI routines
        void SpiSetCsState(SpiCsState chip_select_state) override;
		void SpiSendNoChipSelect(uint8_t values[], int num_values) override;
		void SpiReceiveNoChipSelect(uint8_t values[], int num_values) override;
		void SpiTransceiveNoChipSelect(uint8_t send_values[], uint8_t receive_values[],
            int num_values) override;

        void EepromReadString(char* buffer, int buffer_size) override;

        string GetSerialNumber() override;
        string GetDescription() override { return DESCRIPTION; }

        static const int MAX_CONTROLLERS = 23;

    private:
        friend class Controller;
        static const string DESCRIPTION;

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

        static const int BLOCK_SIZE = 512;
        static const int MAX_BLOCKS = 32;

        static const DWORD QUERY_SIGNATURE = 0x36644851;    // QHd6 -- query signature
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
            CommandHeader(Opcode opcode) : signature(QUERY_SIGNATURE), opcode(opcode),
                byte_param(0), word_param(0) {
                dword_param_1.value = 0;
                dword_param_2.value = 0;
            }
            BYTE GetStatus() { return byte_param; }
            WORD GetLength() { return word_param; }
            void SetLength(WORD length) { word_param = length; }
            void SetNumBlocks(WORD num_blocks) { word_param = num_blocks; }
            void SetAddress(WORD address) { dword_param_1.word_0 = address; }
            void SetTail(WORD tail) { dword_param_1.word_0 = tail; }
        };

        static const int COMMAND_DATA_SIZE = BLOCK_SIZE - sizeof(CommandHeader);
        //    For commands that carry some data in the CMDB block, we limit
        //    the max amount so that some space is available behind db[] for
        //    various uses at the receiving end.  Also, it's convenient to
        //    have it be the EEPROM page size, which is 16 bytes. So...
        //
        static const int MAX_COMMAND_DATA = COMMAND_DATA_SIZE - 16;
        static const int MAX_SPI_READ_BYTES = (MAX_COMMAND_DATA - 1) / 2;

        struct Command {
            CommandHeader header;
            char data[COMMAND_DATA_SIZE];
            Command(Opcode opcode) : header(opcode) {
                memset(data, 0, COMMAND_DATA_SIZE);
            }
            void Reset(Opcode opcode) {
                memset(this, 0, sizeof(Command));
                header.signature = QUERY_SIGNATURE;
                header.opcode = opcode;
            }
        };

        class CommandFile {
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

        class BlockFile {
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

        struct FpgaLoadInfo {
            vector<char> data;
            wstring path;
            uint8_t load_id;
            int offset;
            int num_blocks;
            CommandFile command_file;
            BlockFile block_file;
            FpgaLoadInfo(wstring path, uint8_t load_id, int num_blocks, char drive_letter) :
                data(MAX_BLOCKS * BLOCK_SIZE), path(path), load_id(load_id), offset(0),
                num_blocks(num_blocks), command_file(drive_letter), block_file(drive_letter) { }
            FpgaLoadInfo(FpgaLoadInfo&& other) = delete;
            FpgaLoadInfo(const FpgaLoadInfo& other) = delete;
            FpgaLoadInfo& operator =(const FpgaLoadInfo& other) = delete;
            ~FpgaLoadInfo() = default;
        };

        void FpgaStartLoadFile(const string& fpga_filename);
        void FpgaLoadChunk();
        void FpgaFinishLoadFile();
        void SpiDoTransaction(Command& command, uint8_t* receive_values, int num_values);
        void SpiBufferLowerChipSelect(Command& command, int& offset);
        void SpiBufferRaiseChipSelect(Command& command, int& offset);
        void SpiBufferSendOrTranceive(Command& command, int& offset,
            uint8_t send_values[], int num_values, bool is_send);
        void SpiBufferReceive(Command& command, int& offset, int num_values);
        uint8_t GetCommandResult(Command& command, CommandFile& command_file,
            uint8_t* data = nullptr, int num_data = 0);
        void CheckCommandResult(Command& command, CommandFile& command_file,
            uint8_t* data = nullptr, int num_data = 0);
        bool FpgaGetIsLoaded(uint8_t fpga_load_id);
        int ReadBytes(uint8_t data[], int total_bytes);
        
        char drive_letter;
		uint32_t generic_config = 0;
		uint32_t demo_config = 0;
        bool initialize_ram = false;
        ChipSelect chip_select = ChipSelect::ONE;
        uint8_t eeprom_address = 0x50;
        bool swap_bytes = true;
        bool fpga_load_started = false;
        unique_ptr<FpgaLoadInfo> fpga_load_info;
        bool collect_started = false;
        unique_ptr<CommandFile> collect_command_file;
        
    };

}
