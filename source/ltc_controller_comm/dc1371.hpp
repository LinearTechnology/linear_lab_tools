#pragma once
#include <vector>
#include <string>
#include <cstdint>
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
        Dc1371(LccControllerInfo info) : drive_letter(char(info.id)) { }
        Dc1371(const Dc1371&) = delete;
        Dc1371(Dc1371&&) = delete;
        Dc1371& operator=(const Dc1371& other) = delete;
        ~Dc1371() { }

        Type GetType() override { return Type::DC1371; }

        void Reset() override;

		bool FpgaGetIsLoaded(const string& fpga_filename) override;
        int  FpgaLoadFileChunked(const string& fpga_filename) override;
        void FpgaCancelLoad() override { fpga_load_started = false; }

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
        void DataCancelReceive() override;

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
        struct Command;
        class  CommandFile;
        class  BlockFile;

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
        // We are making two assumptions here that are not guaranteed by the standard:
        // 1. Reads and writes are atomic for bools (true "everywhere" in C++)
        // 2. 'volatile' makes cache coherency issues go away (true on all versions of Windows)
        // To be totally correct, we should use a mutex or interlock whenever we touch these in
        // a multithreaded context, but practically speaking it isn't necessary so we opt out
        // of the needed overhead.
        volatile bool abort_read = false;
        volatile bool is_reading = false;
    };

}
