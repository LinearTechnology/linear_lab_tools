#include <chrono>
#include <thread>

#include "high_speed.hpp"
#include "utilities.hpp"

#ifdef min
#undef min
#endif

using std::this_thread::sleep_for;
using std::chrono::milliseconds;
using std::to_string;

namespace linear {

static const int MAX_FIFO_READ_SIZE     = 32 * 1024;
static const int MAX_FIFO_WRITE_SIZE    = MAX_FIFO_READ_SIZE;
static const int COMMAND_BUFFER_SIZE    = 4 * 1024;
static const int COMMAND_PREFIX_3_BYTES = 3;
static const int COMMAND_PREFIX_1_BYTE  = 1;
static const int I2C_BLOCK_SIZE         = 8;
static const int MAX_I2C_BYTES          = COMMAND_BUFFER_SIZE / 8;  // each bit takes 1 byte

static const uint8_t GPIO_LOW_BASE = 0x8A;

static const uint8_t SPI_CLK_BIT = 0x01;
static const uint8_t SPI_SDI_BIT = 0x02;
static const uint8_t SPI_SDO_BIT = 0x04;
static const uint8_t SPI_CS_BIT  = 0x08;

#pragma warning(push)
#pragma warning(disable : 4245)  // ~ wants to make an int, causing sign mismatch

static const uint8_t SPI_CLK_MASK = ~SPI_CLK_BIT;
static const uint8_t SPI_SDI_MASK = ~SPI_SDI_BIT;
static const uint8_t SPI_SDO_MASK = ~SPI_SDO_BIT;
static const uint8_t SPI_CS_MASK  = ~SPI_CS_BIT;

#pragma warning(pop)

static const uint8_t FPGA_ACTION_BIT       = 0x10;
static const uint8_t FPGA_READ_WRITE_BIT   = 0x20;
static const uint8_t FPGA_ADDRESS_DATA_BIT = 0x40;
static const uint8_t FPGA_RESET_BIT        = 0x80;

// This SHOULD just be the ~ of the above, but FPGA_RESET_BIT confuses linux too
// So I am just hard coding them.
static const uint8_t FPGA_ACTION_MASK       = 0xEF;
static const uint8_t FPGA_READ_WRITE_MASK   = 0xDF;
static const uint8_t FPGA_ADDRESS_DATA_MASK = 0xBF;
static const uint8_t FPGA_RESET_MASK        = 0x7F;

static const uint8_t FPGA_I2C_SDA_BIT = 0x01;
static const uint8_t FPGA_I2C_SCL_BIT = 0x02;

static const uint8_t GPIO_LOW_READ_DIRECTION   = 0x0B;
static const uint8_t GPIO_LOW_WRITE_DIRECTION  = 0xFB;
static const uint8_t GPIO_HIGH_READ_DIRECTION  = 0x00;
static const uint8_t GPIO_HIGH_WRITE_DIRECTION = 0xFF;

static const uint8_t GPIO_LOW_READ_OP_CODE   = 0x81;
static const uint8_t GPIO_LOW_WRITE_OP_CODE  = 0x80;
static const uint8_t GPIO_HIGH_READ_OP_CODE  = 0x83;
static const uint8_t GPIO_HIGH_WRITE_OP_CODE = 0x82;

static const uint8_t SPI_SEND_MODE_0_OP_CODE       = 0x11;
static const uint8_t SPI_SEND_MODE_2_OP_CODE       = 0x10;
static const uint8_t SPI_RECEIVE_MODE_0_OP_CODE    = 0x20;
static const uint8_t SPI_RECEIVE_MODE_2_OP_CODE    = 0x24;
static const uint8_t SPI_TRANSCEIVE_MODE_0_OP_CODE = 0x31;
static const uint8_t SPI_TRANSCEIVE_MODE_2_OP_CODE = 0x34;

static const uint8_t MPSSE_ENABLE_DIVIDE_BY_5_OPCODE  = 0x8B;
static const uint8_t MPSSE_DISABLE_DIVIDE_BY_5_OPCODE = 0x8A;
static const uint8_t MPSSE_CLK_DIVIDE_OPCODE          = 0x86;

#define MUST_NOT_HAVE_HIGH_BIT(arg) \
    if ((arg)&0x80) { throw invalid_argument(QUOTE(arg) " must not have high bit set."); }

// General functions

HighSpeed::HighSpeed(const Ftdi& ftdi, const LccControllerInfo& info)
        : ftdi(ftdi),
          description(info.description),
          serial_number_a(string(info.serial_number) + 'A'),
          serial_number_b(string(info.serial_number) + 'B'),
          index_a(narrow<WORD>(info.id & 0xFFFF)),
          index_b(narrow<WORD>(info.id >> 16)),
          command_buffer(new uint8_t[COMMAND_BUFFER_SIZE]) {}

HighSpeed::~HighSpeed() {
    Close();
    delete[] command_buffer;
    command_buffer = nullptr;
}

// TODO: make all fields that need to be RAII, so we can just use the default move constructor
HighSpeed::HighSpeed(HighSpeed&& other)
        : ftdi(std::move(other.ftdi)),
          index_a(std::move(other.index_a)),
          index_b(std::move(other.index_b)),
          description(std::move(other.description)),
          serial_number_a(std::move(other.serial_number_a)),
          serial_number_b(std::move(other.serial_number_b)),
          spi_mode(std::move(other.spi_mode)),
          i2c_bit_bang_register(std::move(other.i2c_bit_bang_register)),
          channel_a(std::move(other.channel_a)),
          channel_b(std::move(other.channel_b)),
          command_buffer(std::move(other.command_buffer)),
          is_repeated_start(std::move(other.is_repeated_start)),
          swap_bytes(std::move(other.swap_bytes)) {
    other.index_a        = 0;
    other.index_b        = 0;
    other.channel_a      = nullptr;
    other.channel_b      = nullptr;
    other.command_buffer = nullptr;
}

static bool OpenByIndex(const Ftdi&   ftdi,
                        WORD          index_a,
                        WORD          index_b,
                        FT_HANDLE&    channel_a,
                        FT_HANDLE&    channel_b,
                        const string& serial_number_a,
                        const string& serial_number_b) {
    ftdi.OpenByIndex(index_a, &channel_a);
    FT_DEVICE device;
    DWORD     id;
    char      serial_number[LCC_MAX_SERIAL_NUMBER_SIZE];
    char      description[LCC_MAX_DESCRIPTION_SIZE];
    try {
        ftdi.GetDeviceInfo(channel_a, &device, &id, serial_number, description);
        if (device != FT_DEVICE_2232H || string(serial_number) != serial_number_a) {
            ftdi.Close(&channel_a);
            return false;
        }
        ftdi.OpenByIndex(index_b, &channel_b);
        try {
            ftdi.GetDeviceInfo(channel_b, &device, &id, serial_number, description);
            if (device != FT_DEVICE_2232H || string(serial_number) != serial_number_b) {
                ftdi.Close(&channel_a);
                ftdi.Close(&channel_b);
                return false;
            }
        } catch (...) {
            ftdi.Close(&channel_b);
            throw;
        }
    } catch (...) {
        ftdi.Close(&channel_a);
        throw;
    }
    return true;
}

void HighSpeed::OpenIfNeeded() {
    if (channel_a != nullptr) { return; }

    auto is_same = OpenByIndex(ftdi, index_a, index_b, channel_a, channel_b, serial_number_a,
                               serial_number_b);
    if (!is_same) {
        auto info_list = ftdi.ListControllers(LCC_TYPE_HIGH_SPEED, 100);
        for (auto info_iter = info_list.begin(); info_iter != info_list.end(); ++info_iter) {
            if (info_iter->type == FT_DEVICE_2232H &&
                (serial_number_a.substr(0, serial_number_a.size() - 1) ==
                 info_iter->serial_number) &&
                (description == info_iter->description)) {
                index_a = info_iter->id & 0xFFFF;
                index_b = info_iter->id >> 16;
                return OpenIfNeeded();
            }
        }
        throw HardwareError("Could not find controller.");
    }

    SetTimeouts();
    ftdi.DisableEventChar(channel_a);
    ftdi.EnableEventChar(channel_b);
    const int FTDI_MAX_BUFFER_SIZE = 64 * 1024 - 1;
    ftdi.SetUSBParameters(channel_a, FTDI_MAX_BUFFER_SIZE, 0);
    ftdi.SetUSBParameters(channel_b, FTDI_MAX_BUFFER_SIZE, 0);
}

int HighSpeed::Write(FT_HANDLE handle, uint8_t* values, int num_values, bool allow_partial_write) {
    OpenIfNeeded();
    auto num_written = ftdi.Write(handle, values, num_values);
    if (!allow_partial_write && num_values != num_written) {
        Close();
        throw HardwareError(string("Expected to write " + to_string(num_values) +
                                   " bytes, but only wrote " + to_string(num_written)));
    } else {
        return num_written;
    }
}

int HighSpeed::Read(FT_HANDLE handle, uint8_t* values, int num_values, bool allow_partial_read) {
    OpenIfNeeded();
    try {
        auto num_read = ftdi.Read(handle, values, num_values);
        if (!allow_partial_read && num_values != num_read) {
            throw HardwareError(string("Expected to read " + to_string(num_values) +
                                       " bytes, but only read " + to_string(num_read)));
        } else {
            return num_read;
        }
    } catch (HardwareError&) {
        Close();
        throw;
    }
}

void HighSpeed::SetBitMode(BitMode mode) {
    OpenIfNeeded();
    try {
        ftdi.SetBitMode(channel_a, 0, static_cast<BYTE>(mode));
        ftdi.SetBitMode(channel_b, 0, FT_BITMODE_MPSSE);
        if (mode == BitMode::MPSSE) {
            GpioWriteLowByte(GPIO_LOW_BASE);
            return;
        } else {
            ftdi.SetLatencyTimer(channel_a, 2);
            ftdi.SetFlowControl(channel_a, FT_FLOW_RTS_CTS, 0, 0);
        }
    } catch (HardwareError&) {
        Close();
        throw;
    }
}

void HighSpeed::PurgeIo() {
    OpenIfNeeded();
    try {
        ftdi.Purge(channel_a, FT_PURGE_RX | FT_PURGE_TX);
        ftdi.Purge(channel_b, FT_PURGE_RX | FT_PURGE_TX);
    } catch (HardwareError&) {
        Close();
        throw;
    }
}

void HighSpeed::Open() { OpenIfNeeded(); }

void HighSpeed::Close() {
    if (channel_a != nullptr) {
        ftdi.Close(channel_a);
        channel_a = nullptr;
    }
    if (channel_b != nullptr) {
        ftdi.Close(channel_b);
        channel_b = nullptr;
    }
    is_repeated_start = false;
}

void HighSpeed::MpsseEnableDivideBy5(bool enable) {
    OpenIfNeeded();
    uint8_t command = enable ? MPSSE_ENABLE_DIVIDE_BY_5_OPCODE : MPSSE_DISABLE_DIVIDE_BY_5_OPCODE;
    Write(channel_b, &command, 1);
}

void HighSpeed::MpsseSetClkDivider(uint16_t divider) {
    OpenIfNeeded();
    command_buffer[0] = MPSSE_CLK_DIVIDE_OPCODE;
    command_buffer[1] = narrow<uint8_t>(divider & 0xFF);
    command_buffer[2] = narrow<uint8_t>(divider >> 8);
    Write(channel_b, command_buffer, COMMAND_PREFIX_3_BYTES);
}

// Fast Fifo functions

int HighSpeed::WriteBytes(uint8_t values[], int total_bytes) {
    ASSERT_POSITIVE(total_bytes);
    ASSERT_NOT_NULL(values);
    OpenIfNeeded();
    int num_bytes_sent = 0;
    while (num_bytes_sent < total_bytes) {
        int  num_bytes   = std::min(total_bytes, MAX_FIFO_WRITE_SIZE);
        auto num_written = Write(channel_a, values, num_bytes, true);
        if (num_written == 0) { break; }
        num_bytes_sent += num_written;
        values += num_written;
    }
    return num_bytes_sent;
}

int HighSpeed::ReadBytes(uint8_t values[], int total_bytes) {
    ASSERT_POSITIVE(total_bytes);
    ASSERT_NOT_NULL(values);
    OpenIfNeeded();
    int num_bytes_received = 0;
    while (num_bytes_received < total_bytes) {
        int  num_bytes = std::min(total_bytes, MAX_FIFO_READ_SIZE);
        auto num_read  = Read(channel_a, reinterpret_cast<uint8_t*>(values), num_bytes, true);
        if (num_read == 0) { break; }
        num_bytes_received += num_read;
        values += num_read;
    }
    return num_bytes_received;
}

// SPI functions

void HighSpeed::SpiSend(uint8_t* values, int num_values, bool is_data_preset) {
    SpiSetCsState(SpiCsState::LOW);
    SpiSendNoChipSelect(values, num_values, is_data_preset);
    SpiSetCsState(SpiCsState::HIGH);
}
void HighSpeed::SpiReceive(uint8_t* values, int num_values) {
    SpiSetCsState(SpiCsState::LOW);
    SpiReceiveNoChipSelect(values, num_values);
    SpiSetCsState(SpiCsState::HIGH);
}
void HighSpeed::SpiTransceive(uint8_t* send_values, uint8_t* receive_values, int num_values) {
    SpiSetCsState(SpiCsState::LOW);
    SpiTransceiveNoChipSelect(send_values, receive_values, num_values);
    SpiSetCsState(SpiCsState::HIGH);
}

// Convenience SPI functions with "address/value" mode

void HighSpeed::SpiSendAtAddress(uint8_t address, uint8_t values[], int num_values) {
    const int ADDRESS_SIZE = 1;
    // Here we use some insider knowledge; we know that the command to send SPI takes the first
    // 3 bytes of the command buffer, so we start at index three, copy the address and data
    // bytes ourselves, and let the low-level routine know not to do its memcpy. This saves us
    // from needing to allocate a new buffer to combine the address and values.
    safe_memcpy(command_buffer + COMMAND_PREFIX_3_BYTES,
                COMMAND_BUFFER_SIZE - COMMAND_PREFIX_3_BYTES, &address, ADDRESS_SIZE);
    safe_memcpy(command_buffer + COMMAND_PREFIX_3_BYTES + ADDRESS_SIZE,
                COMMAND_BUFFER_SIZE - COMMAND_PREFIX_3_BYTES - ADDRESS_SIZE, values, num_values);

    SpiSend(command_buffer, ADDRESS_SIZE + num_values, true);
}

void HighSpeed::SpiReceiveAtAddress(uint8_t address, uint8_t values[], int num_values) {
    SpiSetCsState(SpiCsState::LOW);
    SpiSendNoChipSelect(&address, 1);
    SpiReceiveNoChipSelect(values, num_values);
    SpiSetCsState(SpiCsState::HIGH);
}

// Low-level SPI routines
void HighSpeed::SpiSetCsState(SpiCsState chip_select_state) {
    OpenIfNeeded();
    command_buffer[0] = GPIO_LOW_WRITE_OP_CODE;
    command_buffer[1] =
            chip_select_state == SpiCsState::HIGH ? GPIO_LOW_BASE : GPIO_LOW_BASE & SPI_CS_MASK;
    command_buffer[2] = GPIO_LOW_READ_DIRECTION;
    Write(channel_b, command_buffer, COMMAND_PREFIX_3_BYTES);
}
void HighSpeed::SpiSendNoChipSelect(uint8_t* values, int num_values, bool is_data_preset) {
    ASSERT_POSITIVE(num_values);
    ASSERT_NOT_LARGER(num_values, COMMAND_BUFFER_SIZE - COMMAND_PREFIX_3_BYTES);
    ASSERT_NOT_NULL(values);
    OpenIfNeeded();
    --num_values;  // For "minus-one" encoding
    command_buffer[0] =
            spi_mode == SpiMode::MODE_0 ? SPI_SEND_MODE_0_OP_CODE : SPI_SEND_MODE_2_OP_CODE;
    command_buffer[1] = num_values & 0xFF;
    command_buffer[2] = (num_values >> 8) & 0xFF;
    ++num_values;
    if (!is_data_preset) {
        safe_memcpy(command_buffer + COMMAND_PREFIX_3_BYTES,
                    COMMAND_BUFFER_SIZE - COMMAND_PREFIX_3_BYTES, values, num_values);
    }

    Write(channel_b, command_buffer, COMMAND_PREFIX_3_BYTES + num_values);
}
void HighSpeed::SpiReceiveNoChipSelect(uint8_t* values, int num_values) {
    ASSERT_POSITIVE(num_values);
    ASSERT_NOT_LARGER(num_values, COMMAND_BUFFER_SIZE - COMMAND_PREFIX_3_BYTES);
    ASSERT_NOT_NULL(values);
    OpenIfNeeded();
    command_buffer[0] =
            spi_mode == SpiMode::MODE_0 ? SPI_RECEIVE_MODE_0_OP_CODE : SPI_RECEIVE_MODE_2_OP_CODE;
    --num_values;  // For "minus-one" encoding
    command_buffer[1] = num_values & 0xFF;
    command_buffer[2] = (num_values >> 8) & 0xFF;

    Write(channel_b, command_buffer, COMMAND_PREFIX_3_BYTES);
    ++num_values;  // now we want the actual number again
    Read(channel_b, values, num_values, false);
}
void HighSpeed::SpiTransceiveNoChipSelect(uint8_t* send_values,
                                          uint8_t* receive_values,
                                          int      num_values) {
    ASSERT_POSITIVE(num_values);
    ASSERT_NOT_LARGER(num_values, COMMAND_BUFFER_SIZE - COMMAND_PREFIX_3_BYTES);
    ASSERT_NOT_NULL(send_values);
    ASSERT_NOT_NULL(receive_values);
    OpenIfNeeded();
    command_buffer[0] = spi_mode == SpiMode::MODE_0 ? SPI_TRANSCEIVE_MODE_0_OP_CODE :
                                                      SPI_TRANSCEIVE_MODE_2_OP_CODE;
    --num_values;
    command_buffer[1] = num_values & 0xFF;
    command_buffer[2] = (num_values >> 8) & 0xFF;
    ++num_values;
    safe_memcpy(command_buffer + COMMAND_PREFIX_3_BYTES,
                COMMAND_BUFFER_SIZE - COMMAND_PREFIX_3_BYTES, send_values, num_values);

    Write(channel_b, command_buffer, COMMAND_PREFIX_3_BYTES + num_values);
    Read(channel_b, receive_values, num_values);
}

// Fpga functions (via GPIO)

void HighSpeed::FpgaSetResetLow(bool low) {
    auto byte = GPIO_LOW_BASE & (low ? FPGA_RESET_MASK : 0xFF);
    GpioWriteLowByte(byte);
}

void HighSpeed::FpgaToggleReset() {
    FpgaSetResetLow();
    sleep_for(milliseconds(20));
    FpgaSetResetLow(false);
}
void HighSpeed::FpgaWriteAddress(uint8_t address) {
    OpenIfNeeded();
    int buffer_index = 0;
    BufferFpgaWriteAddressCommand(address, buffer_index);
    Write(channel_b, command_buffer, buffer_index);
}
void HighSpeed::FpgaWriteData(uint8_t value) {
    OpenIfNeeded();
    int buffer_index = 0;
    BufferFpgaWriteDataCommand(value, buffer_index);
    Write(channel_b, command_buffer, buffer_index);
}
uint8_t HighSpeed::FpgaReadData() {
    OpenIfNeeded();
    int buffer_index = 0;
    BufferFpgaReadDataCommand(buffer_index);
    Write(channel_b, command_buffer, buffer_index);
    uint8_t value = 0;
    Read(channel_b, &value, 1);
    return value;
}
void HighSpeed::FpgaWriteDataAtAddress(uint8_t address, uint8_t value) {
    OpenIfNeeded();
    int buffer_index = 0;
    BufferFpgaWriteAddressCommand(address, buffer_index);
    BufferFpgaWriteDataCommand(value, buffer_index);
    Write(channel_b, command_buffer, buffer_index);
}
uint8_t HighSpeed::FpgaReadDataAtAddress(uint8_t address) {
    OpenIfNeeded();
    int buffer_index = 0;
    BufferFpgaWriteAddressCommand(address, buffer_index);
    BufferFpgaReadDataCommand(buffer_index);
    Write(channel_b, command_buffer, buffer_index);
    uint8_t value = 0;
    Read(channel_b, &value, 1);
    return value;
}

// GPIO functions
void HighSpeed::GpioWriteHighByte(uint8_t value) {
    OpenIfNeeded();
    int buffer_index = 0;
    BufferGpioHighWriteCommand(value, buffer_index);
    Write(channel_b, command_buffer, buffer_index);
}
uint8_t HighSpeed::GpioReadHighByte() {
    OpenIfNeeded();
    int buffer_index = 0;
    BufferGpioHighReadCommand(buffer_index);
    Write(channel_b, command_buffer, buffer_index);
    uint8_t value = 0;
    Read(channel_b, &value, 1);
    return value;
}
void HighSpeed::GpioWriteLowByte(uint8_t value) {
    OpenIfNeeded();
    int buffer_index = 0;
    BufferGpioLowWriteCommand(value, buffer_index);
    Write(channel_b, command_buffer, buffer_index);
}
uint8_t HighSpeed::GpioReadLowByte() {
    OpenIfNeeded();
    int buffer_index = 0;
    BufferGpioLowReadCommand(buffer_index);
    Write(channel_b, command_buffer, buffer_index);
    uint8_t value = 0;
    Read(channel_b, &value, COMMAND_PREFIX_1_BYTE);
    return value;
}

// Bit-banged I2C via FPGA register (via GPIO)

const uint8_t I2C_MUX_ADDRESS    = 0x74;
const uint8_t EEPROM_MUX_CHANNEL = 0x02;
const uint8_t EEPROM_ADDRESS     = 0x50;
const int     MAX_EEPROM_CHARS   = 240;
void          HighSpeed::EepromReadString(char* buffer, int buffer_size) {
    OpenIfNeeded();
    // set the mux
    FpgaI2cSendStartCondition();
    FpgaI2cSend(I2C_MUX_ADDRESS, EEPROM_MUX_CHANNEL);
    FpgaI2cSendStopCondition();
    // talk to the EEPROM
    FpgaI2cSendStartCondition();
    uint8_t bytes[2] = { 0, 0 };
    FpgaI2cSend(EEPROM_ADDRESS, bytes, 2);
    FpgaI2cSendStartCondition();
    FpgaI2cReceiveString(EEPROM_ADDRESS, buffer, buffer_size);
    FpgaI2cSendStopCondition();
    buffer[buffer_size - 1] = '\0';
}

void HighSpeed::FpgaI2cSendStartCondition() {
    FpgaWriteAddress(i2c_bit_bang_register);
    int buffer_index = 0;
    if (is_repeated_start) {
        BufferFpgaWriteDataCommand(FPGA_I2C_SDA_BIT, buffer_index);
        BufferFpgaWriteDataCommand(FPGA_I2C_SCL_BIT | FPGA_I2C_SDA_BIT, buffer_index);
    } else {
        is_repeated_start = true;
    }
    BufferFpgaWriteDataCommand(FPGA_I2C_SCL_BIT, buffer_index);
    BufferFpgaWriteDataCommand(0, buffer_index);
    Write(channel_b, command_buffer, buffer_index);
}

void HighSpeed::FpgaI2cSendStopCondition() {
    is_repeated_start = false;
    int buffer_index  = 0;
    BufferFpgaWriteDataCommand(0, buffer_index);
    BufferFpgaWriteDataCommand(FPGA_I2C_SCL_BIT, buffer_index);
    BufferFpgaWriteDataCommand(FPGA_I2C_SCL_BIT | FPGA_I2C_SDA_BIT, buffer_index);
    Write(channel_b, command_buffer, buffer_index);
}

void HighSpeed::FpgaI2cSendNoAddress(uint8_t* values, int num_values) {
    ASSERT_POSITIVE(num_values);
    // not strictly necessary on write, but the bit-banged I2c is so slow, you wouldn't
    // want to wait for this to finish!
    ASSERT_NOT_LARGER(num_values, MAX_I2C_BYTES);
    ASSERT_NOT_NULL(values);

    int total_values = num_values;
    while (total_values > 0) {
        num_values       = std::min(total_values, I2C_BLOCK_SIZE);
        int buffer_index = 0;
        for (int value_index = 0; value_index < num_values; ++value_index) {
            uint8_t value = values[value_index];
            for (int bit_index = 0; bit_index < 8; ++bit_index) {
                uint8_t bit = (value & 0x80) ? FPGA_I2C_SDA_BIT : 0;
                BufferFpgaWriteDataCommand(bit, buffer_index);
                BufferFpgaWriteDataCommand(bit | FPGA_I2C_SCL_BIT, buffer_index);
                BufferFpgaWriteDataCommand(bit, buffer_index);
                value <<= 1;
            }

            BufferFpgaWriteDataCommand(FPGA_I2C_SDA_BIT, buffer_index);
            BufferFpgaWriteDataCommand(FPGA_I2C_SDA_BIT | FPGA_I2C_SCL_BIT, buffer_index);

            BufferFpgaReadDataCommand(buffer_index);

            BufferFpgaWriteDataCommand(FPGA_I2C_SDA_BIT, buffer_index);
        }

        Write(channel_b, command_buffer, buffer_index);
        Read(channel_b, command_buffer, num_values);

        for (int i = 0; i < num_values; ++i) {
            if ((command_buffer[i] & FPGA_I2C_SDA_BIT) != 0) {
                Close();
                throw HardwareError("I2C slave did not ACK.");
            }
        }
        total_values -= num_values;
    }
}
void HighSpeed::FpgaI2cReceiveNoAddress(uint8_t* values, int num_values) {
    ASSERT_POSITIVE(num_values);
    // needed to prevent overruning command_buffer
    ASSERT_NOT_LARGER(num_values, MAX_I2C_BYTES);
    ASSERT_NOT_NULL(values);

    int original_values = num_values;
    int total_values    = num_values - 1;  // last byte is special
    int buffer_index    = 0;
    while (total_values > 0) {
        num_values   = std::min(total_values, I2C_BLOCK_SIZE);
        buffer_index = 0;
        for (int value_index = 0; value_index < num_values; ++value_index) {
            for (int bit_index = 0; bit_index < 8; ++bit_index) {
                BufferFpgaWriteDataCommand(FPGA_I2C_SDA_BIT, buffer_index);
                BufferFpgaWriteDataCommand(FPGA_I2C_SDA_BIT | FPGA_I2C_SCL_BIT, buffer_index);
                BufferFpgaReadDataCommand(buffer_index);
                BufferFpgaWriteDataCommand(FPGA_I2C_SDA_BIT, buffer_index);
            }
            BufferFpgaWriteDataCommand(0, buffer_index);
            BufferFpgaWriteDataCommand(FPGA_I2C_SCL_BIT, buffer_index);
            BufferFpgaWriteDataCommand(0, buffer_index);
        }
        Write(channel_b, command_buffer, buffer_index);
        total_values -= num_values;
    }

    // last byte
    buffer_index = 0;
    for (int bit_index = 0; bit_index < 8; ++bit_index) {
        BufferFpgaWriteDataCommand(FPGA_I2C_SDA_BIT, buffer_index);
        BufferFpgaWriteDataCommand(FPGA_I2C_SDA_BIT | FPGA_I2C_SCL_BIT, buffer_index);
        BufferFpgaReadDataCommand(buffer_index);
        BufferFpgaWriteDataCommand(FPGA_I2C_SDA_BIT, buffer_index);
    }
    BufferFpgaWriteDataCommand(FPGA_I2C_SDA_BIT, buffer_index);
    BufferFpgaWriteDataCommand(FPGA_I2C_SDA_BIT | FPGA_I2C_SCL_BIT, buffer_index);
    BufferFpgaWriteDataCommand(FPGA_I2C_SDA_BIT, buffer_index);

    Write(channel_b, command_buffer, buffer_index);
    Read(channel_b, command_buffer, original_values * 8);

    int received_bit_index = 0;
    for (int byte_index = 0; byte_index < original_values; ++byte_index) {
        uint8_t bit        = 0x80;
        values[byte_index] = 0;
        for (int bit_index = 0; bit_index < 8; ++bit_index) {
            values[byte_index] |= command_buffer[received_bit_index] ? bit : 0;
            bit >>= 1;
            ++received_bit_index;
        }
    }
}

void HighSpeed::FpgaI2cSend(uint8_t address, uint8_t* values, int num_values) {
    MUST_NOT_HAVE_HIGH_BIT(address);
    address <<= 1;
    FpgaI2cSendNoAddress(&address, 1);
    FpgaI2cSendNoAddress(values, num_values);
}
void HighSpeed::FpgaI2cSend(uint8_t address, uint8_t value) {
    return FpgaI2cSend(address, &value, 1);
}
void HighSpeed::FpgaI2cReceive(uint8_t address, uint8_t* values, int num_values) {
    MUST_NOT_HAVE_HIGH_BIT(address);
    address = (address << 1) | 0x01;
    FpgaI2cSendNoAddress(&address, 1);
    FpgaI2cReceiveNoAddress(values, num_values);
}
uint8_t HighSpeed::FpgaI2cReceive(uint8_t address) {
    uint8_t value = 0;
    FpgaI2cReceive(address, &value, 1);
    return value;
}
void HighSpeed::FpgaI2cReceiveString(uint8_t address, char* buffer, int buffer_size) {
    return FpgaI2cReceive(address, reinterpret_cast<uint8_t*>(buffer), buffer_size);
}

// buffered GPIO functions
void HighSpeed::BufferGpioHighSetToReadCommand(int& buffer_index) {
    command_buffer[buffer_index] = GPIO_HIGH_WRITE_OP_CODE;
    ++buffer_index;
    command_buffer[buffer_index] = 0x00;  // Doesn't matter.
    ++buffer_index;
    command_buffer[buffer_index] = GPIO_HIGH_READ_DIRECTION;
    ++buffer_index;
}
void HighSpeed::BufferGpioHighReadCommand(int& buffer_index) {
    command_buffer[buffer_index] = GPIO_HIGH_READ_OP_CODE;
    ++buffer_index;
}
void HighSpeed::BufferGpioHighWriteCommand(uint8_t value, int& buffer_index) {
    command_buffer[buffer_index] = GPIO_HIGH_WRITE_OP_CODE;
    ++buffer_index;
    command_buffer[buffer_index] = value;
    ++buffer_index;
    command_buffer[buffer_index] = GPIO_HIGH_WRITE_DIRECTION;
    ++buffer_index;
}
void HighSpeed::BufferGpioLowReadCommand(int& buffer_index) {
    command_buffer[buffer_index] = GPIO_LOW_READ_OP_CODE;
    ++buffer_index;
}
void HighSpeed::BufferGpioLowWriteCommand(uint8_t value, int& buffer_index) {
    command_buffer[buffer_index] = GPIO_LOW_WRITE_OP_CODE;
    ++buffer_index;
    command_buffer[buffer_index] = value;
    ++buffer_index;
    command_buffer[buffer_index] = GPIO_LOW_WRITE_DIRECTION;
    ++buffer_index;
}
void HighSpeed::BufferFpgaWriteAddressCommand(uint8_t address, int& buffer_index) {
    BufferGpioHighWriteCommand(address, buffer_index);
    BufferGpioLowWriteCommand(GPIO_LOW_BASE | FPGA_ADDRESS_DATA_BIT, buffer_index);
    BufferGpioLowWriteCommand(GPIO_LOW_BASE | FPGA_ADDRESS_DATA_BIT | FPGA_ACTION_BIT,
                              buffer_index);
    BufferGpioLowWriteCommand(GPIO_LOW_BASE, buffer_index);
    BufferGpioHighSetToReadCommand(buffer_index);
}
void HighSpeed::BufferFpgaWriteDataCommand(uint8_t value, int& buffer_index) {
    BufferGpioHighWriteCommand(value, buffer_index);
    BufferGpioLowWriteCommand(GPIO_LOW_BASE | FPGA_ACTION_BIT, buffer_index);
    BufferGpioLowWriteCommand(GPIO_LOW_BASE, buffer_index);
    BufferGpioHighSetToReadCommand(buffer_index);
}
void HighSpeed::BufferFpgaReadDataCommand(int& buffer_index) {
    BufferGpioLowWriteCommand(GPIO_LOW_BASE | FPGA_READ_WRITE_BIT, buffer_index);
    BufferGpioLowWriteCommand(GPIO_LOW_BASE | FPGA_READ_WRITE_BIT | FPGA_ACTION_BIT, buffer_index);
    BufferGpioHighReadCommand(buffer_index);
    BufferGpioLowWriteCommand(GPIO_LOW_BASE, buffer_index);
}
}