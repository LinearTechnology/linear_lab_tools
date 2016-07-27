#pragma once
#include <vector>
#include <string>
#include <cstdint>
#include "i_close.hpp"
#include "i_data_endian.hpp"
#include "i_data_send.hpp"
#include "i_data_receive.hpp"
#include "i_spi.hpp"
#include "controller.hpp"
#include "Ftdi.hpp"

namespace linear {

using std::string;
using std::vector;

class HighSpeed : public IClose, public IDataEndian,
    public IDataReceive, public IDataSend, public ISpi {
public:
    enum class BitMode : uint8_t {
        MPSSE = FT_BITMODE_MPSSE,
        FIFO = FT_BITMODE_SYNC_FIFO
    };

    enum class SpiMode {
        MODE_0 = 0,
        MODE_2 = 2
    };

    // General functions
    HighSpeed(const Ftdi& ftdi, const LccControllerInfo& info);
    ~HighSpeed();
    HighSpeed(const HighSpeed&) = delete;
    HighSpeed(HighSpeed&& other);
    HighSpeed& operator=(const HighSpeed&) = delete;

    Type GetType() override { return Type::HIGH_SPEED; }

    string GetDescription() override { return description; }
    string GetSerialNumber() override { return serial_number_a.substr(0, serial_number_a.size() - 1); }

    void SetBitMode(BitMode mode);
    void PurgeIo();
    void Close() override;
    void Open();

    // Data functions
    void DataSetHighByteFirst() override { swap_bytes = true; }
    void DataSetLowByteFirst() override { swap_bytes = false; }

    int DataReceive(uint8_t data[], int total_bytes) override {
        return ReadBytes(data, total_bytes);
    }
    int DataReceive(uint16_t data[], int total_values) override {
        return Controller::DataRead(*this, swap_bytes, data, total_values);
    }
    int DataReceive(uint32_t data[], int total_values) override {
        return Controller::DataRead(*this, swap_bytes, data, total_values);
    }
    int DataSend(uint8_t data[], int total_bytes) override {
        return WriteBytes(data, total_bytes);
    }
    int DataSend(uint16_t data[], int total_values) override {
        return Controller::DataWrite(*this, swap_bytes, data, total_values);
    }
    int DataSend(uint32_t data[], int total_values) override {
        return Controller::DataWrite(*this, swap_bytes, data, total_values);
    }

    // SPI functions
    void SetSpiMode(SpiMode new_spi_mode) { spi_mode = new_spi_mode; }
    void SpiSend(uint8_t* values, int num_values) override {
        return SpiSend(values, num_values, false);
    }
    void SpiSend(uint8_t* values, int num_values, bool is_data_preset);
    void SpiReceive(uint8_t* values, int num_values) override;
    void SpiTransceive(uint8_t* send_values, uint8_t* receive_values, int num_values) override;

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
    void SpiSendNoChipSelect(uint8_t* values, int num_values) override {
        SpiSendNoChipSelect(values, num_values, false);
    }
    void SpiSendNoChipSelect(uint8_t* values, int num_values, bool is_data_preset);
    void SpiReceiveNoChipSelect(uint8_t* values, int num_values) override;
    void SpiTransceiveNoChipSelect(uint8_t* send_values, uint8_t* receive_values,
                                   int num_values) override;

    // Fpga functions (via GPIO)
    void FpgaSetResetLow(bool low = true);
    void FpgaToggleReset();
    void FpgaWriteAddress(uint8_t address);
    void FpgaWriteData(uint8_t value);
    uint8_t FpgaReadData();
    void FpgaWriteDataAtAddress(uint8_t address, uint8_t value);
    uint8_t FpgaReadDataAtAddress(uint8_t address);

    // GPIO functions
    void GpioWriteHighByte(uint8_t value);
    uint8_t GpioReadHighByte();
    void GpioWriteLowByte(uint8_t value);
    uint8_t GpioReadLowByte();

    // Read EEPROM using bit-banged I2C via FPGA register (via GPIO)
    void FpgaEepromSetBitBangRegister(uint8_t value) { i2c_bit_bang_register = value; }
    void EepromReadString(char* buffer, int buffer_size) override;

private:
    static const ULONG DEFAULT_READ_TIMEOUT = 3000;
    static const ULONG DEFAULT_WRITE_TIMEOUT = 3000;
    void SetTimeouts(ULONG read_timeout = DEFAULT_READ_TIMEOUT,
                     ULONG write_timeout = DEFAULT_WRITE_TIMEOUT) {
        ftdi.SetTimeouts(channel_a, read_timeout, write_timeout);
        ftdi.SetTimeouts(channel_b, read_timeout, write_timeout);
    }
    friend class Controller;
    void OpenIfNeeded();
    int Write(FT_HANDLE handle, uint8_t* values, int num_values,
              bool allow_partial_write = false);
    int ReadBytes(uint8_t data[], int total_bytes);
    int WriteBytes(uint8_t data[], int total_bytes);
    int Read(FT_HANDLE handle, uint8_t* values, int num_values,
             bool allow_partial_read = false);
    void BufferGpioHighSetToReadCommand(int& buffer_index);
    void BufferGpioHighReadCommand(int& buffer_index);
    void BufferGpioHighWriteCommand(uint8_t value, int& buffer_index);
    void BufferGpioLowReadCommand(int& buffer_index);
    void BufferGpioLowWriteCommand(uint8_t value, int& buffer_index);
    void BufferFpgaWriteAddressCommand(uint8_t address, int& buffer_index);
    void BufferFpgaWriteDataCommand(uint8_t value, int& buffer_index);
    void BufferFpgaReadDataCommand(int& buffer_index);
    void FpgaI2cSendStartCondition();
    void FpgaI2cSendStopCondition();
    void FpgaI2cSend(uint8_t address, uint8_t value);
    void FpgaI2cSend(uint8_t address, uint8_t* values, int num_values);
    uint8_t FpgaI2cReceive(uint8_t address);
    void FpgaI2cReceive(uint8_t address, uint8_t* values, int num_values);
    void FpgaI2cReceiveString(uint8_t address, char* buffer, int buffer_size);
    void FpgaI2cSendNoAddress(uint8_t* values, int num_values);
    void FpgaI2cReceiveNoAddress(uint8_t* values, int num_values);

    const Ftdi& ftdi;
    WORD index_a;
    WORD index_b;
    string description;
    string serial_number_a;
    string serial_number_b;
    SpiMode spi_mode = SpiMode::MODE_0;
    uint8_t i2c_bit_bang_register = 0x11;
    FT_HANDLE channel_a = nullptr;
    FT_HANDLE channel_b = nullptr;
    uint8_t* command_buffer = nullptr;
    bool is_repeated_start = false;
    bool swap_bytes = true;
};
}
