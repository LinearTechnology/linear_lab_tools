#include "ltc_controller_comm/ltc_controller_comm.h"

#include <string>
#include <iostream>
#include <cstdint>
#include <vector>
#include <utility>
#include <thread>
#include <chrono>

#define _USE_MATH_DEFINES
#include <math.h>

using std::string;
using std::cin;
using std::cout;
using std::vector;
using std::pair;
using std::make_pair;
using std::this_thread::sleep_for;
using std::chrono::milliseconds;
using std::chrono::high_resolution_clock;
using std::chrono::duration_cast;

const int NUM_DAC_SAMPLES = 64 * 1024;
const int NUM_CYCLES_1 = 489;
const int NUM_CYCLES_2 = 2 * NUM_CYCLES_1;
const int NUM_CYCLES_3 = 2 * NUM_CYCLES_2;
const int AMPLITUDE = 32000;
const double TWO_PI = 2 * M_PI;

const uint8_t REG_RESET_PD = 0x01;
const uint8_t REG_CLK_CONFIG = 0x02;
const uint8_t REG_CLK_PHASE = 0x03;
const uint8_t REG_PORT_EN = 0x04;
const uint8_t REG_SYNC_PHASE = 0x05;
const uint8_t REG_PHASE_COMP_OUT = 0x06;
const uint8_t REG_LINEAR_GAIN = 0x07;
const uint8_t REG_LINEARIZATION = 0x08;
const uint8_t REG_DAC_GAIN = 0x09;
const uint8_t REG_LVDS_MUX = 0x18;
const uint8_t REG_TEMP_SELECT = 0x19;
const uint8_t REG_PATTERN_ENABLE = 0x1E;
const uint8_t REG_PATTERN_DATA = 0x1F;

const uint8_t FPGA_ID_REG = 0x00;
const uint8_t FPGA_CONTROL_REG = 0x01;
const uint8_t FPGA_STATUS_REG = 0x02;
const uint8_t FPGA_DAC_PD = 0x03;

const uint8_t CAPTURE_CONFIG_REG = 0x01;
const uint8_t CAPTURE_CONTROL_REG = 0x02;
const uint8_t CAPTURE_RESET_REG = 0x03;
const uint8_t CAPTURE_STATUS_REG = 0x04;
const uint8_t CLOCK_STATUS_REG = 0x06;

const uint8_t I2C_MUX_ADDRESS = 0x74;
const uint8_t EEPROM_MUX_CHANNEL = 0x02;
const uint8_t EEPROM_ADDRESS = 0x50;
const int     MAX_EEPROM_CHARS = 200;

const uint8_t JESD204B_WB0_REG = 0x07;
const uint8_t JESD204B_WB1_REG = 0x08;
const uint8_t JESD204B_WB2_REG = 0x09;
const uint8_t JESD204B_WB3_REG = 0x0A;
const uint8_t JESD204B_CONFIG_REG = 0x0B;
const uint8_t JESD204B_RB0_REG = 0x0C;
const uint8_t JESD204B_RB1_REG = 0x0D;
const uint8_t JESD204B_RB2_REG = 0x0E;
const uint8_t JESD204B_RB3_REG = 0x0F;
const uint8_t JESD204B_CHECK_REG = 0x10;

const uint8_t GPIO_LOW_BASE = 0x8A;
const uint8_t FPGA_ACTION_BIT = 0x10;
const uint8_t FPGA_READ_WRITE_BIT = 0x20;
const uint8_t FPGA_ADDRESS_DATA_BIT = 0x40;

const int NUM_ADC_SAMPLES = 64 * 1024;

void WaitForEnterPress() {
    cin.sync();
    cin.get();
}

bool HandleStatus(LccHandle& handle, int status, int line_number) {
    if (status != 0) {
        if (handle == nullptr) {
            cout << "Error (" << line_number << ")\n";
        } else {
            char buffer[256];
            LccGetErrorInfo(handle, buffer, 256);
            cout << "Error (" << line_number << "): " << buffer << "\n";
            LccCleanup(&handle);
        }
        return false;
    } else {
        return true;
    }
}

#define CHECK(x, ln) if (!HandleStatus(handle, (x), (ln))) { return -1; }
#define FAIL(msg, ln) { LccCleanup(&handle); return -1; }

const int SPI_READ_BIT = 0x80;
const int SPI_WRITE_BIT = 0x00;

#define SPI_WRITE(address, value) LccSpiSendByteAtAddress(handle, address | SPI_WRITE_BIT, value)
#define SPI_READ(address, value) LccSpiReceiveByteAtAddress(handle, address | SPI_READ_BIT, &value)


int ResetFpga(LccHandle handle, int line_number) {
    CHECK(LccHsSetBitMode(handle, LCC_HS_BIT_MODE_MPSSE), line_number);
    CHECK(LccHsFpgaToggleReset(handle), line_number);
    sleep_for(milliseconds(10));
    CHECK(LccHsFpgaWriteDataAtAddress(handle, FPGA_DAC_PD, 0x01), line_number);
    sleep_for(milliseconds(10));
    CHECK(LccHsFpgaWriteDataAtAddress(handle, FPGA_CONTROL_REG, 0x20), line_number);
    sleep_for(milliseconds(10));
    CHECK(LccHsSetBitMode(handle, LCC_HS_BIT_MODE_FIFO), line_number);
    return 0;
}

const char* LTC2123_ID_STRING = "[0074 DEMO 10 DC1974A-A LTC2124-14 D2124\r\n"
"ADC 14 16 2 0000 00 00 00 00\r\n"
"DBFLG 0003 00 00 00 00\r\n"
"FPGA S0000 T0\r\n"
"187F]";

static int WriteJedecReg(LccHandle handle, uint8_t address,
    uint8_t b3, uint8_t b2, uint8_t b1, uint8_t b0, int line_number) {
    CHECK(LccHsFpgaWriteDataAtAddress(handle, JESD204B_WB3_REG, b3), line_number);
    CHECK(LccHsFpgaWriteDataAtAddress(handle, JESD204B_WB2_REG, b2), line_number);
    CHECK(LccHsFpgaWriteDataAtAddress(handle, JESD204B_WB1_REG, b1), line_number);
    CHECK(LccHsFpgaWriteDataAtAddress(handle, JESD204B_WB0_REG, b0), line_number);
    CHECK(LccHsFpgaWriteDataAtAddress(handle, JESD204B_CONFIG_REG, (address << 2) | 0x02), line_number);
    uint8_t status = 0;
    CHECK(LccHsFpgaReadData(handle, &status), line_number);
    if ((status & 0x01) == 0) {
        FAIL("Error, got bad FPGA statues in WriteJedecReg\n", __LINE__);
    } else {
        return 0;
    }
}

// this assumes numSamps is power of 2 (which it is if it is a valid number of samps)
// it is a quick way to get the log base 2, then it subtracts 7 (2^7 is 128, smallest value) and
// shifts it to the left by 1 nybble.
static uint8_t RegFromNumSamps(int numSamps) {
    unsigned int reg = 0;
    reg |= ((numSamps & 0xAAAAAAAA) != 0);
    reg |= ((numSamps & 0xCCCCCCCC) != 0) << 1;
    reg |= ((numSamps & 0xF0F0F0F0) != 0) << 2;
    reg |= ((numSamps & 0xFF00FF00) != 0) << 3;
    reg |= ((numSamps & 0xFFFF0000) != 0) << 4;
    return (reg - 7) << 4;
}

int InitAdc(LccHandle handle) {

    CHECK(LccClose(handle), __LINE__);
    CHECK(LccHsSetBitMode(handle, LCC_HS_BIT_MODE_MPSSE), __LINE__);
    CHECK(LccHsFpgaToggleReset(handle), __LINE__);
    CHECK(SPI_WRITE(1, 0x00), __LINE__);
    CHECK(SPI_WRITE(2, 0x00), __LINE__);
    CHECK(SPI_WRITE(3, 0xAB), __LINE__);
    CHECK(SPI_WRITE(4, 0x0C), __LINE__);
    CHECK(SPI_WRITE(5, 0x01), __LINE__);
    CHECK(SPI_WRITE(6, 0x17), __LINE__);
    CHECK(SPI_WRITE(7, 0x00), __LINE__);
    CHECK(SPI_WRITE(8, 0x00), __LINE__);
    CHECK(SPI_WRITE(9, 0x04), __LINE__);

    if (WriteJedecReg(handle, 0x01, 0x00, 0x00, 0x00, 0x01, __LINE__) != 0) { return -1; }
    if (WriteJedecReg(handle, 0x02, 0x00, 0x00, 0x00, 0x00, __LINE__) != 0) { return -1; }
    if (WriteJedecReg(handle, 0x03, 0x00, 0x00, 0x00, 0x17, __LINE__) != 0) { return -1; }
    if (WriteJedecReg(handle, 0x00, 0x00, 0x00, 0x01, 0x02, __LINE__) != 0) { return -1; }

    uint8_t status = 0;
    CHECK(LccHsFpgaReadDataAtAddress(handle, CLOCK_STATUS_REG, &status), __LINE__);
    if (status != 0x1E) {
        FAIL("Error: CLOCK_STATUS_REG status was not 0x1E\n", __LINE__);
    }
    CHECK(LccHsFpgaWriteDataAtAddress(handle, CAPTURE_CONFIG_REG,
        RegFromNumSamps(NUM_ADC_SAMPLES) | 0x08), __LINE__);
    CHECK(LccHsFpgaWriteDataAtAddress(handle, CAPTURE_RESET_REG, 0x01), __LINE__);
    CHECK(LccHsFpgaWriteDataAtAddress(handle, CAPTURE_CONTROL_REG, 0x01), __LINE__);
    sleep_for(milliseconds(50));
    CHECK(LccHsFpgaReadDataAtAddress(handle, CAPTURE_STATUS_REG, &status), __LINE__);
    if ((status & 0x31) != 0x31) {
        FAIL("Error: CAPTURE_STATUS_REG status was not 0x31\n", __LINE__);
    }
    return 0;
}

uint16_t NextPrbs(uint16_t current_value) {
    uint16_t next = ((current_value << 1) ^ (current_value << 2)) & 0xFFFC;
    next |= ((next >> 15) ^ (next >> 14)) & 0x0001;
    next |= ((next >> 14) ^ (current_value << 1)) & 0x0002;
    return next;
}

bool CheckPrbs(const uint16_t* data, int size) {
    if (data[0] == 0) {
        return false;
    }
    for (int i = 1; i < size; ++i) {
        auto next = NextPrbs(data[i - 1]);
        if (data[i] != next) {
            return false;
        }
    }
    return true;
}

//#define HIGH_SPEED_BATTERY_1
//#define HIGH_SPEED_BATTERY_2
//#define HIGH_SPEED_BATTERY_3
//#define DC1371_BATTERY_1
#define DC890_BATTERY_1
//#define DC718_BATTERY_1

int main() {

#ifdef HIGH_SPEED_BATTERY_1
#ifdef HIGH_SPEED_BATTERY_2
#ifdef HIGH_SPEED_BATTERY_3
#ifdef DC1371_BATTERY_1
#ifdef DC890_BATTERY_1
#ifdef DC718_BATTERY_1
#define ALL_TESTS
#endif
#endif
#endif
#endif
#endif
#endif
#ifndef ALL_TESTS
    cout << "################################################################################\n";
    cout << "WARNING! This is not a valid test; please define all test batteries and rebuild.\n";
    cout << "################################################################################\n";
#endif

#ifdef HIGH_SPEED_BATTERY_1
    cout << "Test Battery 1\nUse an LTC2000 setup with a scope to view output.\n"
        "Press enter when ready\n.";
    WaitForEnterPress();

    cout << "Testing basic functionality\n";

    LccHandle handle = nullptr;

    int num_devices = 0;
    CHECK(LccGetNumControllers(LCC_TYPE_HIGH_SPEED, &num_devices), __LINE__);

    vector<LccControllerInfo> controller_info_vector(num_devices);
    CHECK(LccGetControllerList(LCC_TYPE_HIGH_SPEED, controller_info_vector.data(), num_devices),
        __LINE__);

    LccControllerInfo device_info;
    device_info.description[0] = '\0';
    for (auto& info : controller_info_vector) {
        string description = info.description;
        cout << "Found FT2232H based device with description: " << description << '\n';
        if (description.substr(0, 7) == "LTC2000") {
            device_info = info;
        }
    }

    if (device_info.description[0] == '\0') {
        cout << "No LTC2000 demo board detected\n";
        return -1;
    }

    cout << "Found LTC2000 demo board:\n";
    cout << "Description: " << device_info.description << "\n";
    cout << "Serial Number: " << device_info.serial_number << "\n";


    CHECK(LccInitController(&handle, device_info), __LINE__);

    CHECK(LccHsSetBitMode(handle, LCC_HS_BIT_MODE_MPSSE), __LINE__);

    CHECK(LccHsFpgaToggleReset(handle), __LINE__);

    uint8_t id = 0;
    CHECK(LccHsFpgaReadDataAtAddress(handle, FPGA_ID_REG, &id), __LINE__);
    cout << "FPGA ID is " << int(id) << "\n";

    CHECK(LccHsFpgaWriteDataAtAddress(handle, FPGA_DAC_PD, 0x01), __LINE__);

    CHECK(SPI_WRITE(REG_RESET_PD, 0x00), __LINE__);
    CHECK(SPI_WRITE(REG_CLK_PHASE, 0x05), __LINE__);
    CHECK(SPI_WRITE(REG_PORT_EN, 0x0B), __LINE__);
    CHECK(SPI_WRITE(REG_SYNC_PHASE, 0x00), __LINE__);
    CHECK(SPI_WRITE(REG_LINEAR_GAIN, 0x00), __LINE__);
    CHECK(SPI_WRITE(REG_LINEARIZATION, 0x08), __LINE__);
    CHECK(SPI_WRITE(REG_DAC_GAIN, 0x20), __LINE__);
    CHECK(SPI_WRITE(REG_LVDS_MUX, 0x00), __LINE__);
    CHECK(SPI_WRITE(REG_TEMP_SELECT, 0x00), __LINE__);
    CHECK(SPI_WRITE(REG_PATTERN_ENABLE, 0x00), __LINE__);

    uint8_t value;
    CHECK(SPI_READ(REG_RESET_PD, value), __LINE__);
    if ((value & 0xCF) != 0x00) {
        FAIL("Error reading SPI register (" << __LINE__ << ")\n", __LINE__);
    }
    CHECK(SPI_READ(REG_CLK_PHASE, value), __LINE__);
    if (value != 0x07) {
        cout << "Expected a 7, got a " << int(value) << "\n";
        FAIL("Error reading SPI register", __LINE__);
    }
    CHECK(SPI_READ(REG_PORT_EN, value), __LINE__);
    if (value != 0x0B) {
        FAIL("Error reading SPI register", __LINE__);
    }
    CHECK(SPI_READ(REG_SYNC_PHASE, value), __LINE__);
    if ((value & 0xFC) != 0x00) {
        FAIL("Error reading SPI register", __LINE__);
    }
    CHECK(SPI_READ(REG_LINEAR_GAIN, value), __LINE__);
    if (value != 0x00) {
        FAIL("Error reading SPI register", __LINE__);
    }
    CHECK(SPI_READ(REG_LINEARIZATION, value), __LINE__);
    if (value != 0x08) {
        FAIL("Error reading SPI register", __LINE__);;
    }
    CHECK(SPI_READ(REG_DAC_GAIN, value), __LINE__);

    if (value != 0x20) {
        FAIL("Error reading SPI register", __LINE__);
    }

    CHECK(LccHsFpgaWriteDataAtAddress(handle, FPGA_CONTROL_REG, 0x20), __LINE__);

    auto data_16 = vector<int16_t>(NUM_DAC_SAMPLES);
    int i = 0;
    for (auto& d : data_16) {
        d = static_cast<int16_t>(AMPLITUDE * sin((NUM_CYCLES_1 * TWO_PI * i) / NUM_DAC_SAMPLES));
        ++i;
    }

    CHECK(LccHsSetBitMode(handle, LCC_HS_BIT_MODE_FIFO), __LINE__);

    // 16-bit

    int num_bytes_sent = 0;
    CHECK(LccDataSendUint16Values(handle, reinterpret_cast<uint16_t*>(data_16.data()),
        NUM_DAC_SAMPLES, &num_bytes_sent), __LINE__);
    if (num_bytes_sent != NUM_DAC_SAMPLES * 2) {
        FAIL("Error, not all samples sent\n", __LINE__);
    }

    cout << "Basic test finished, do you see a sine wave in the scope with "
        "frequency = clock_frequency / " << float(NUM_DAC_SAMPLES) / NUM_CYCLES_1 << "? (y = yes, n = no)\n";
    string response;
    cin >> response;
    if (response[0] != 'y') {
        FAIL("Error, user indicates output is invalid\n", __LINE__);
    }

    cout << "User indicates output is valid.\n";

    cout << "LccCreateDeviceList is OK\n";
    cout << "LccGetDeviceList is OK\n";
    cout << "LccInitDevice is OK\n";
    cout << "LccSetBitMode is OK\n";
    cout << "LccFpgaSetReset is OK\n";
    cout << "LccFpgaReadDataAtAddress is OK\n";
    cout << "LccFpgaWriteDataAtAddress is OK\n";
    cout << "LccSpiWriteByteAtAddress is OK\n";
    cout << "LccSpiReadByteAtAddress is OK\n";
    cout << "LccFifoSendUint16Values is OK\n";

    // 8-bit

    if (ResetFpga(handle, __LINE__) != 0) {
        return -1;
    }

    i = 0;
    for (auto& d : data_16) {
        d = static_cast<int16_t>(AMPLITUDE * sin((NUM_CYCLES_2 * TWO_PI * i) / NUM_DAC_SAMPLES));
        ++i;
    }

    auto data_8 = vector<uint8_t>(NUM_DAC_SAMPLES * 2);
    for (int i = 0; i < NUM_DAC_SAMPLES; ++i) {
        data_8[2 * i] = static_cast<uint8_t>(data_16[i] >> 8);
        data_8[2 * i + 1] = static_cast<uint8_t>(data_16[i] & 0xFF);
    }
    CHECK(LccDataSendBytes(handle, data_8.data(), NUM_DAC_SAMPLES * 2, &num_bytes_sent), __LINE__);
    if (num_bytes_sent != NUM_DAC_SAMPLES * 2) {
        FAIL("Error, not all samples sent\n", __LINE__);
    }

    cout << "Basic test finished, do you see a sine wave in the scope with "
        "frequency = clock_frequency / " << float(NUM_DAC_SAMPLES) / NUM_CYCLES_2 << "? (y = yes, n = no)\n";
    cin >> response;
    if (response[0] != 'y') {
        FAIL("Error, user indicates output is invalid\n", __LINE__);
    }
    cout << "LccFifoSendByteValues is OK\n";

    // 32-bit

    if (ResetFpga(handle, __LINE__) != 0) {
        return -1;
    }

    // double the frequency, send as uin32_t
    i = 0;
    for (auto& d : data_16) {
        d = static_cast<int16_t>(AMPLITUDE * sin((NUM_CYCLES_3 * TWO_PI * i) / NUM_DAC_SAMPLES));
        ++i;
    }

    sleep_for(milliseconds(20));

    auto data_32 = vector<uint32_t>(NUM_DAC_SAMPLES / 2);
    for (int i = 0; i < NUM_DAC_SAMPLES / 2; ++i) {
        auto temp = data_16[2 * i];
        data_16[2 * i] = data_16[2 * i + 1];
        data_16[2 * i + 1] = temp;
        data_32[i] = *reinterpret_cast<uint32_t*>(data_16.data() + (2 * i));
    }

    CHECK(LccDataSendUint32Values(handle, data_32.data(), NUM_DAC_SAMPLES / 2, &num_bytes_sent), __LINE__);
    if (num_bytes_sent != NUM_DAC_SAMPLES * 2) {
        FAIL("Error, not all samples sent\n", __LINE__);
    }

    cout << "Basic test finished, do you see a sine wave in the scope with "
        "frequency = clock_frequency / " << float(NUM_DAC_SAMPLES) / NUM_CYCLES_3 << "? (y = yes, n = no)\n";
    cin >> response;
    if (response[0] != 'y') {
        FAIL("Error, user indicates output is invalid\n", __LINE__);
    }

    cout << "LccFifoSendUint32Values is OK\n";

    CHECK(LccHsSetBitMode(handle, LCC_HS_BIT_MODE_MPSSE), __LINE__);

    uint8_t address_value[2] = { REG_LINEAR_GAIN | SPI_WRITE_BIT, 2 };
    CHECK(LccSpiSendBytes(handle, address_value, 2), __LINE__);

    CHECK(SPI_READ(REG_LINEAR_GAIN, value), __LINE__);
    if (value != 0x02) {
        FAIL("Error LccSpiSendBytes didn't seem to work (" << __LINE__ << ")\n", __LINE__);
    }
    cout << "LccSpiSendBytes is OK\n";

    address_value[1] = 0x04;
    CHECK(LccSpiTransceiveBytes(handle, address_value, address_value, 2), __LINE__);
    address_value[0] = REG_LINEAR_GAIN | SPI_READ_BIT;
    address_value[1] = 0;
    CHECK(LccSpiTransceiveBytes(handle, address_value, address_value, 2), __LINE__);

    if (address_value[1] != 0x04) {
        FAIL("Error LccTransceiveBytes didn't seem to work", __LINE__);
    }

    value = 0x06;
    CHECK(LccSpiSendBytesAtAddress(handle, REG_LINEAR_GAIN | SPI_WRITE_BIT, &value, 1), __LINE__);

    CHECK(SPI_READ(REG_LINEAR_GAIN, value), __LINE__);
    if (value != 0x06) {
        FAIL("Error LccSpiSendBytesAtAddress didn't seem to work", __LINE__);
    }
    cout << "LccSpiSendBytesAtAddress is OK\n";

    value = 0x00; // to make sure the function below really changes it
    CHECK(LccSpiReceiveBytesAtAddress(handle, REG_LINEAR_GAIN | SPI_READ_BIT, &value, 1), __LINE__);

    if (value != 0x06) {
        FAIL("Error: LccSpiReceiveBytesAtAddress didn't seem to work", __LINE__);
    }
    cout << "LccSpiReceiveBytesAtAddress is OK\n";

    CHECK(LccSpiSetCsState(handle, LCC_SPI_CS_STATE_LOW), __LINE__);
    address_value[0] = REG_LINEAR_GAIN | SPI_WRITE_BIT;
    address_value[1] = 0x08;
    CHECK(LccSpiSendNoChipSelect(handle, address_value, 2), __LINE__);
    CHECK(LccSpiSetCsState(handle, LCC_SPI_CS_STATE_HIGH), __LINE__);
    CHECK(SPI_READ(REG_LINEAR_GAIN, value), __LINE__);
    if (value != 0x08) {
        FAIL(Error: LccSetChipSelect or LccSpiSendNoChipSelect didn't seem to work", __LINE__);
    }
    cout << "LccSpiSetChipSelect is OK\n";
    cout << "LccSpiSendNoChipSelect is OK\n";

    address_value[0] = REG_LINEAR_GAIN | SPI_READ_BIT;
    address_value[1] = 0; // to make sure it gets changed
    CHECK(LccSpiSetCsState(handle, LCC_SPI_CS_STATE_LOW), __LINE__);
    CHECK(LccSpiSendNoChipSelect(handle, address_value, 2), __LINE__);
    CHECK(LccSpiReceiveNoChipSelect(handle, &value, 1), __LINE__);
    CHECK(LccSpiSetCsState(handle, LCC_SPI_CS_STATE_HIGH), __LINE__);
    if (value != 0x08) {
        FAIL("Error: LccReceiveNoChipSelect didn't seem to work", __LINE__);
    }
    cout << "LccSpiReceiveNoChipSelect is OK\n";

    address_value[0] = REG_LINEAR_GAIN | SPI_WRITE_BIT;
    address_value[1] = 0x0A;
    CHECK(LccSpiSetCsState(handle, LCC_SPI_CS_STATE_LOW), __LINE__);
    CHECK(LccSpiTransceiveNoChipSelect(handle, address_value, address_value, 2), __LINE__);
    CHECK(LccSpiSetCsState(handle, LCC_SPI_CS_STATE_HIGH), __LINE__);
    address_value[0] = REG_LINEAR_GAIN | SPI_READ_BIT;
    address_value[1] = 0x00;
    CHECK(LccSpiSetCsState(handle, LCC_SPI_CS_STATE_LOW), __LINE__);
    CHECK(LccSpiTransceiveNoChipSelect(handle, address_value, address_value, 2), __LINE__);
    CHECK(LccSpiSetCsState(handle, LCC_SPI_CS_STATE_HIGH), __LINE__);
    if (address_value[1] != 0x0A) {
        cout << "Error: LccTransceiveNoChipSelect didn't seem to work (" << __LINE__ << ")\n";
    }
    cout << "LccSpiTransceiveNoChipSelect is OK\n";

    CHECK(LccHsFpgaWriteAddress(handle, FPGA_ID_REG), __LINE__);
    CHECK(LccHsFpgaWriteData(handle, 92), __LINE__);
    CHECK(LccHsFpgaReadDataAtAddress(handle, FPGA_ID_REG, &value), __LINE__);
    if (value != 92) {
        FAIL("Error: LccFpgaWriteAddress or LccFpgaWriteData didn't seem to work", __LINE__);
    }

    cout << "LccFpgaWriteAddress is OK\n";
    cout << "LccFpgaWriteData is OK\n";

    CHECK(LccHsFpgaWriteData(handle, 37), __LINE__);
    CHECK(LccHsFpgaReadData(handle, &value), __LINE__);
    if (value != 37) {
        cout << "Error: LccFpgaReadData didn't seem to work (" << __LINE__ << ")\n";
    }
    cout << "LccFpgaReadData is OK\n";

    CHECK(LccHsFpgaWriteAddress(handle, FPGA_ID_REG), __LINE__);

    CHECK(LccHsGpioWriteLowByte(handle, GPIO_LOW_BASE), __LINE__)
        CHECK(LccHsGpioWriteHighByte(handle, 56), __LINE__);
    CHECK(LccHsGpioWriteLowByte(handle, GPIO_LOW_BASE | FPGA_ACTION_BIT), __LINE__);
    CHECK(LccHsGpioWriteLowByte(handle, GPIO_LOW_BASE), __LINE__);

    CHECK(LccHsFpgaReadData(handle, &value), __LINE__);

    if (value != 56) {
        FAIL("Error: LccGpioWriteHighByte or LccGpioWriteLowByte didn't seem to work\n", __LINE__);
    }
    cout << "LccGpioWriteHighByte is OK\n";
    cout << "LccGpioWriteLowByte is OK\n";

    CHECK(LccHsFpgaWriteData(handle, 72), __LINE__);

    CHECK(LccHsGpioWriteLowByte(handle, GPIO_LOW_BASE | FPGA_READ_WRITE_BIT), __LINE__);
    CHECK(LccHsGpioWriteLowByte(handle,
        GPIO_LOW_BASE | FPGA_READ_WRITE_BIT | FPGA_ACTION_BIT), __LINE__);
    CHECK(LccHsGpioReadHighByte(handle, &value), __LINE__);
    CHECK(LccHsGpioWriteLowByte(handle, GPIO_LOW_BASE), __LINE__);

    if (value != 72) {
        FAIL("Error: LccGpioReadHighByte didn't seem to work\n", __LINE__);
    }
    cout << "LccGpioReadHighByte is OK\n";

    auto description_size = LccGetDescription(handle, nullptr, 0);
    if (description_size != strlen(device_info.description) + 1) {
        FAIL("Error: LccGetDescription with no buffer didn't seem to work\n", __LINE__);
    }
    char buffer[256];
    CHECK(LccGetDescription(handle, buffer, sizeof(buffer)), __LINE__);
    if (strcmp(buffer, device_info.description) != 0) {
        FAIL("Error: LccGetDescription didn't seem to work\n", __LINE__);
    }
    cout << "LccGetDescription is OK\n";

    auto serial_number_size = LccGetSerialNumber(handle, nullptr, 0);
    if (serial_number_size != strlen(device_info.serial_number) + 1) {
        FAIL("Error: LccGetSerialNumber with no buffer didn't seem to work\n", __LINE__);
    }

    CHECK(LccGetSerialNumber(handle, buffer, sizeof(buffer)), __LINE__);
    if (strcmp(buffer, device_info.serial_number) != 0) {
        cout << "Error: LccGetSerialNumber didn't seem to work\n";
    }

    cout << "LccGetSerialNumber is OK\n";

    int num_transfered = 0;

    CHECK(LccSetTimeouts(handle, 500, 500), __LINE__);
    // LccFifoReceiveBytes is really just a call to FTDI's read function, with nothing on the
    // buffer it will timeout.
    high_resolution_clock::time_point start_time = high_resolution_clock::now();
    CHECK(LccDataReceiveBytes(handle, &value, 1, &num_transfered), __LINE__);
    auto elapsed_ms = duration_cast<milliseconds>(high_resolution_clock::now() - start_time).count();
    if (elapsed_ms < 250 || elapsed_ms > 750) {
        FAIL("Error: LccSetTimeouts didn't seem to work\n", __LINE__);
    }

    CHECK(LccSetTimeouts(handle, 3000, 3000), __LINE__);
    // LccFifoReceiveBytes is really just a call to FTDI's read function, with nothing on the
    // buffer it will timeout.

    start_time = high_resolution_clock::now();
    CHECK(LccDataReceiveBytes(handle, &value, 1, &num_transfered), __LINE__);
    elapsed_ms = duration_cast<milliseconds>(high_resolution_clock::now() - start_time).count();
    if (elapsed_ms < 2750 || elapsed_ms > 3250) {
        FAIL("Error: LccSetTimeouts didn't seem to work\n", __LINE__);
    }

    cout << "LccSetTimeouts is OK\n";

    // send a "bad command" to cause the FTDI device to return an 0xFA, then flush and see if it
    // is still there
    value = 0x80;
    CHECK(LccDataSendBytes(handle, &value, 1, &num_transfered), __LINE__);
    CHECK(LccHsPurgeIo(handle), __LINE__);
    CHECK(LccDataReceiveBytes(handle, &value, 1, &num_transfered), __LINE__);
    if (num_transfered != 0) {
        FAIL("Error: LccPurgeIo didn't seem to work\n", __LINE__);
    }

    cout << "LccPurgeIo is OK\n";

    // steal the device handle
    CHECK(LccClose(handle), __LINE__);
    LccHandle stolen_handle;
    CHECK(LccInitController(&stolen_handle, device_info), __LINE__);
    // use it, so it opens the device
    CHECK(LccHsFpgaReadDataAtAddress(stolen_handle, FPGA_ID_REG, &value), __LINE__);
    // now this will fail
    auto error = LccHsFpgaReadDataAtAddress(handle, FPGA_ID_REG, &value);
    if (error == 0) {
        FAIL("Error: LccClose didn't seem to work\n", __LINE__);
    }
    cout << "LccClose is OK\n";

    CHECK(LccGetErrorInfo(handle, buffer, sizeof(buffer)), __LINE__);
    if (strcmp(buffer, "Error opening device by index (FTDI error code: DEVICE_NOT_OPENED)") != 0) {
        FAIL("Error: LccGetErrorInfo didn't seem to work\n", __LINE__);
    }
    cout << "LccGetErrorInfo is OK\n";

    CHECK(LccCleanup(&stolen_handle), __LINE__);
    if (stolen_handle != nullptr) {
        cout << "Eror: LccCleanup didn't seem to work\n";
    }
    CHECK(LccHsFpgaReadDataAtAddress(handle, FPGA_ID_REG, &value), __LINE__);
    cout << "LccCleanup is OK\n";

    LccCleanup(&handle);

#endif

#ifdef HIGH_SPEED_BATTERY_2
#ifndef HIGH_SPEED_BATTERY_1
    LccHandle handle = nullptr;
    int num_transfered;
    uint8_t value;
    int num_devices;
    vector<LccControllerInfo> controller_info_vector;
    LccControllerInfo device_info;
    char buffer[256];
#endif

    cout << "Test Battery 2\nUse an LTC2123 setup.\n"
        "Press enter when ready\n.";
    WaitForEnterPress();

    num_devices = 0;
    CHECK(LccGetNumControllers(LCC_TYPE_HIGH_SPEED, &num_devices), __LINE__);

    controller_info_vector.resize(num_devices);
    CHECK(LccGetControllerList(LCC_TYPE_HIGH_SPEED, controller_info_vector.data(), num_devices),
        __LINE__);

    device_info.description[0] = '\0';
    for (auto& info : controller_info_vector) {
        string description = info.description;
        cout << "Found FT2232H based device with description: " << description << '\n';
        if (description == "LTC Communication Interface") {
            device_info = info;
        }
    }

    if (device_info.description[0] == '\0') {
        FAIL("No LTC2123 demo board detected\n", __LINE__);
    }

    cout << "Found LTC2123 demo board:\n";
    cout << "Serial Number: " << device_info.serial_number << "\n";

    CHECK(LccInitController(&handle, device_info), __LINE__);

    CHECK(LccDataSetLowByteFirst(handle), __LINE__);

    auto udata_16 = vector<uint16_t>(NUM_ADC_SAMPLES);
    auto udata_32 = vector<uint32_t>(NUM_ADC_SAMPLES / 2);
    auto udata_8 = vector<uint8_t>(NUM_ADC_SAMPLES * 2);

    auto channel_a = vector<uint16_t>(NUM_ADC_SAMPLES / 2);
    auto channel_b = vector<uint16_t>(NUM_ADC_SAMPLES / 2);

    // uint16

    if (InitAdc(handle) != 0) {
        return -1;
    }
    CHECK(LccHsSetBitMode(handle, LCC_HS_BIT_MODE_FIFO), __LINE__);
    CHECK(LccDataReceiveUint16Values(handle, udata_16.data(), NUM_ADC_SAMPLES, &num_transfered),
        __LINE__);

    for (int i = 0; i < NUM_ADC_SAMPLES / 2; i += 2) {
        channel_a[i] = udata_16[2 * i];
        channel_a[i + 1] = udata_16[2 * i + 1];
        channel_b[i] = udata_16[2 * i + 2];
        channel_b[i + 1] = udata_16[2 * i + 3];
    }

    if (!CheckPrbs(channel_a.data(), channel_a.size())) {
        FAIL("Error: LccFifoReceiveUint16Values didn't seem to work\n", __LINE__);
    }

    if (!CheckPrbs(channel_b.data(), channel_a.size())) {
        FAIL("Error: LccFifoReceiveUint16Values didn't seem to work\n", __LINE__);
    }

    cout << "LccFifoReceiveUint16Values is OK\n";

    // uint32
    if (InitAdc(handle) != 0) {
        return -1;
    }
    CHECK(LccHsSetBitMode(handle, LCC_HS_BIT_MODE_FIFO), __LINE__);
    CHECK(LccDataReceiveUint32Values(handle, udata_32.data(), NUM_ADC_SAMPLES / 2,
        &num_transfered), __LINE__);

    for (int i = 0; i < NUM_ADC_SAMPLES / 2; i += 2) {
        auto temp = reinterpret_cast<uint16_t*>(udata_32.data() + i);
        channel_a[i] = temp[0];
        channel_a[i + 1] = temp[1];
        channel_b[i] = temp[2];
        channel_b[i + 1] = temp[3];
    }

    if (!CheckPrbs(channel_a.data(), channel_a.size())) {
        FAIL("Error: LccFifoReceiveUint32Values didn't seem to work\n", __LINE__);
    }

    if (!CheckPrbs(channel_b.data(), channel_a.size())) {
        FAIL("Error: LccFifoReceiveUint32Values didn't seem to work\n", __LINE__);
    }

    cout << "LccFifoReceiveUint32Values is OK\n";

    // uint8

    if (InitAdc(handle) != 0) {
        return -1;
    }
    CHECK(LccHsSetBitMode(handle, LCC_HS_BIT_MODE_FIFO), __LINE__);
    CHECK(LccDataReceiveBytes(handle, udata_8.data(), NUM_ADC_SAMPLES * 2, &num_transfered),
        __LINE__);

    for (int i = 0; i < NUM_ADC_SAMPLES / 2; i += 2) {
        channel_a[i] = *reinterpret_cast<uint16_t*>(udata_8.data() + 4 * i);
        channel_a[i + 1] = *reinterpret_cast<uint16_t*>(udata_8.data() + 4 * i + 2);
        channel_b[i] = *reinterpret_cast<uint16_t*>(udata_8.data() + 4 * i + 4);
        channel_b[i + 1] = *reinterpret_cast<uint16_t*>(udata_8.data() + 4 * i + 6);
    }

    if (!CheckPrbs(channel_a.data(), channel_a.size())) {
        FAIL("Error: LccFifoReceiveBytes didn't seem to work\n", __LINE__);
    }

    if (!CheckPrbs(channel_b.data(), channel_a.size())) {
        FAIL("Error: LccFifoReceiveBytes didn't seem to work\n", __LINE__);
    }

    cout << "LccFifoReceiveBytes is OK\n";

    memset(buffer, 0, 256);

    CHECK(LccHsSetBitMode(handle, LCC_HS_BIT_MODE_MPSSE), __LINE__);

    CHECK(LccHsFpgaToggleReset(handle), __LINE__);

    CHECK(LccEepromReadString(handle, buffer, MAX_EEPROM_CHARS), __LINE__);

    if (strncmp(LTC2123_ID_STRING, buffer, strlen(LTC2123_ID_STRING)) != 0) {
        FAIL("Error: LccFpgaEepromReadString didn't seem to work.\n", __LINE__);
    }
    cout << "LccFpgaEepromReadString is OK\n";

    CHECK(LccHsFpgaWriteDataAtAddress(handle, 0x00, 0x00), __LINE__);

    CHECK(LccHsFpgaEepromSetBitBangRegister(handle, 0x00), __LINE__);
    LccEepromReadString(handle, buffer, 1);

    CHECK(LccHsFpgaReadDataAtAddress(handle, 0x00, &value), __LINE__);

    if (value == 0) {
        FAIL("Error: LccFpgaEepromSetBitBangRegister didn't seem to work\n", __LINE__);
    }

    cout << "LccFpgaEepromSetBitBangRegister is OK\n";

    CHECK(LccCleanup(&handle), __LINE__);

#endif

#ifdef HIGH_SPEED_BATTERY_3
#ifndef HIGH_SPEED_BATTERY_1
#ifndef HIGH_SPEED_BATTERY_2
    int num_devices;
    vector<LccDeviceInfo> controller_info_vector;
    LccHandle handle = nullptr;
    LccDeviceInfo device_info;
    uint8_t value;
#endif
#endif

    cout << "Test Battery 3\nUse an FT2232H mini-module with:\n";
    cout << "CN2-5 connected to CN2-11\n";
    cout << "CN3-1 connected to CN3-3\n";
    cout << "CN3-17 connected to CN3-24\n";
    cout << "Press enter when ready\n.";
    WaitForEnterPress();

    num_devices = 0;
    CHECK(LccGetNumControllers(LCC_TYPE_HIGH_SPEED, &num_devices), __LINE__);

    controller_info_vector.resize(num_devices);
    CHECK(LccGetControllerList(LCC_TYPE_HIGH_SPEED, controller_info_vector.data(), num_devices), __LINE__);

    device_info.description[0] = '\0';
    for (auto& info : controller_info_vector) {
        string description = info.description;
        cout << "Found FT2232H based device with description: " << description << '\n';
        if (description == "LTC Communication Interface") {
            device_info = info;
        }
    }

    if (device_info.description[0] == '\0') {
        FAIL("No Mini-module demo board detected\n", __LINE__);
    }

    cout << "Found Mini-module:\n";
    cout << "Serial Number: " << device_info.serial_number << "\n";

    CHECK(LccInitController(&handle, device_info), __LINE__);

    CHECK(LccHsSetBitMode(handle, LCC_HS_BIT_MODE_MPSSE), __LINE__);

    CHECK(LccHsGpioWriteHighByte(handle, 0x01), __LINE__);
    CHECK(LccSpiReceiveBytes(handle, &value, 1), __LINE__);
    if (value != 0xFF) {
        FAIL("Error: LccSpiReceiveBytes didn't seem to work\n", __LINE__);
    }

    CHECK(LccHsGpioWriteHighByte(handle, 0x00), __LINE__);
    CHECK(LccSpiReceiveBytes(handle, &value, 1), __LINE__);
    if (value != 0x00) {
        FAIL("Error: LccSpiReceiveBytes didn't seem to work\n", __LINE__);
    }

    cout << "LccSpiReceiveBytes is OK\n";

    CHECK(LccHsGpioWriteHighByte(handle, 0x01), __LINE__);
    CHECK(LccHsGpioReadLowByte(handle, &value), __LINE__);
    if ((value & 0x04) == 0) {
        FAIL("Error: LccGpioReadLowByte didn't seem to work\n", __LINE__);
   }
    CHECK(LccHsGpioWriteHighByte(handle, 0x00), __LINE__);
    CHECK(LccHsGpioReadLowByte(handle, &value), __LINE__);
    if ((value & 0x04) != 0) {
        FAIL("Error: LccGpioReadLowByte didn't seem to work\n", __LINE__);
    }

    cout << "LccGpioReadLowByte is OK\n";

    CHECK(LccCleanup(&handle), __LINE__);

#endif

#ifdef DC1371_BATTERY_1
    cout << "DC1371 Test battery 1\n Plug in a DC1371 controller with a demoboard.\n";
    WaitForEnterPress();
    LccHandle handle = nullptr;
    int num_controllers = 0;
    CHECK(LccGetNumControllers(LCC_TYPE_DC1371, 10, &num_controllers), __LINE__);
    LccControllerInfo info;
    CHECK(LccGetControllerList(LCC_TYPE_DC1371, &info, 1), __LINE__);
    CHECK(LccInitController(&handle, info), __LINE__);

    char id_string[200];
    CHECK(LccEepromReadString(handle, id_string, 200), __LINE__);
    cout << "ID string '" << id_string << "'\n";
    CHECK(LccReset(handle), __LINE__);

    CHECK(LccSpiSendByteAtAddress(handle, 0x00, 0x80), __LINE__); // reset
    CHECK(LccSpiSendByteAtAddress(handle, 0x01, 0x00), __LINE__); // offset binary
    CHECK(LccSpiSendByteAtAddress(handle, 0x02, 0x00), __LINE__);
    CHECK(LccSpiSendByteAtAddress(handle, 0x03, 0xAA), __LINE__); // pattern mode
    CHECK(LccSpiSendByteAtAddress(handle, 0x04, 0xAA), __LINE__); // pattern is 0x2AAA (10922)

    bool is_fpga_loaded;
    CHECK(LccFpgaGetIsLoaded(handle, "S2175", &is_fpga_loaded), __LINE__);
    if (!is_fpga_loaded) {
        CHECK(LccFpgaLoadFile(handle, "S2175"), __LINE__);
    } //else {
    //    cout << "The correct FPGA load is already loaded, please power off the system and power "
    //        "it back on, then press enter.\n";
    //    WaitForEnterPress();
    //    CHECK(LccFpgaGetIsLoaded(handle, "S2175", &is_fpga_loaded), __LINE__);
    //    if (!is_fpga_loaded) {
    //        CHECK(LccFpgaLoadFile(handle, "S2175"), __LINE__);
    //    } else {
    //        FAIL("Still have the correct load, aborting\n", __LINE__);
    //    }
    //}

    CHECK(Lcc1371SetDemoConfig(handle, 0x28000000), __LINE__);

    uint16_t data[NUM_ADC_SAMPLES];
    CHECK(LccDataStartCollect(handle, NUM_ADC_SAMPLES * 2, LCC_TRIGGER_NONE), __LINE__);
    bool is_done = false;
    for (int i = 0; i < 10; ++i) {
        CHECK(LccDataIsCollectDone(handle, &is_done), __LINE__);
        if (is_done) {
            break;
        }
        sleep_for(milliseconds(200));
    }

    if (!is_done) {
        FAIL("Data collect timed out.\n", __LINE__);
    }

    int total_bytes_received;
    CHECK(LccDataReceiveUint16Values(handle, data, NUM_ADC_SAMPLES, &total_bytes_received), __LINE__);

    if (total_bytes_received != 2 * NUM_ADC_SAMPLES) {
        FAIL("Not all bytes received\n", __LINE__);
    }

    for (int i = 0; i < NUM_ADC_SAMPLES; ++i) {
        if (data[i] != 0x2AAA) {
            FAIL("Data values not correct\n", __LINE__);
        }
    }

#endif

#ifdef DC890_BATTERY_1

    // DC1369A-A LTC2261

    LccHandle handle = nullptr;
    LccControllerInfo controller_info;
    CHECK(LccGetControllerList(LCC_TYPE_DC890, &controller_info, 1), __LINE__);
    CHECK(LccInitController(&handle, controller_info), __LINE__);

    char eeprom_id[50];
    CHECK(LccEepromReadString(handle, eeprom_id, 50), __LINE__);
    cout << "id string is " << eeprom_id << "\n";

    CHECK(Lcc890GpioSetByte(handle, 0xF8), __LINE__);
    CHECK(Lcc890GpioSpiSetBits(handle, 3, 0, 1), __LINE__);

    CHECK(LccSpiSendByteAtAddress(handle, 0x00, 0x80), __LINE__);
    CHECK(LccSpiSendByteAtAddress(handle, 0x01, 0x00), __LINE__);
    CHECK(LccSpiSendByteAtAddress(handle, 0x02, 0x00), __LINE__);
    CHECK(LccSpiSendByteAtAddress(handle, 0x03, 0x71), __LINE__);
    
    //CHECK(LccSpiSendByteAtAddress(handle, 0x04, 0x08), __LINE__); // All 0's
    //CHECK(LccSpiSendByteAtAddress(handle, 0x04, 0x18), __LINE__); // All 1's
    CHECK(LccSpiSendByteAtAddress(handle, 0x04, 0x28), __LINE__); // Checkerboard


    bool is_loaded = false;
    CHECK(LccFpgaGetIsLoaded(handle, "DLVDS", &is_loaded), __LINE__);
    if (!is_loaded) {
        CHECK(LccFpgaLoadFile(handle, "DLVDS"), __LINE__);
    }

    const int SAMPLE_BYTES = 2;
    CHECK(LccDataSetCharacteristics(handle, true, SAMPLE_BYTES, true), __LINE__);

    uint16_t data[NUM_ADC_SAMPLES];
    CHECK(LccDataStartCollect(handle, NUM_ADC_SAMPLES, LCC_TRIGGER_NONE), __LINE__);
    bool is_done = false;
    for (int i = 0; i < 10; ++i) {
        CHECK(LccDataIsCollectDone(handle, &is_done), __LINE__);
        if (is_done) {
            break;
        }
        sleep_for(milliseconds(200));
    }

    CHECK(Lcc890Flush(handle), __LINE__);

    int total_bytes_received;
    CHECK(LccDataReceiveUint16Values(handle, data, NUM_ADC_SAMPLES, &total_bytes_received), __LINE__);
    
    if (total_bytes_received != 2 * NUM_ADC_SAMPLES) {
        FAIL("Not all bytes received\n", __LINE__);
    }

    for (int i = 0; i < NUM_ADC_SAMPLES; ++i) {
        data[i] &= 0x3FFF;
    }

    uint16_t codes[] = { 0x2AAA, 0x1555 };
    int code_index = 1;
    if ((data[0] & 0x3FFF) == codes[0]) {
        code_index = 0;
    }
    for (int i = 0; i < NUM_ADC_SAMPLES; i += 2) {
        if ((data[i] & 0x3FFF) != codes[code_index]) {
            FAIL("Data values not correct\n", __LINE__);
        }
        code_index ^= 1;
    }

    int progress = 0;
    CHECK(LccFpgaLoadFileChunked(handle, "S1407", &progress), __LINE__);
    CHECK(LccFpgaCancelLoad(handle), __LINE__);
    CHECK(LccFpgaLoadFile(handle, "DCMOS"), __LINE__);
    CHECK(LccFpgaGetIsLoaded(handle, "DCMOS", &is_loaded), __LINE__);
    if (!is_loaded) {
        FAIL("FPGA load failed\n", __LINE__);
    }

    LccCleanup(&handle);

#endif


#ifdef DC718_BATTERY_1

    // DC1369A-A LTC2261

    LccHandle handle = nullptr;
    LccControllerInfo controller_info;
    CHECK(LccGetControllerList(LCC_TYPE_DC718, &controller_info, 1), __LINE__);
    CHECK(LccInitController(&handle, controller_info), __LINE__);

    char eeprom_id[50];
    CHECK(LccEepromReadString(handle, eeprom_id, 50), __LINE__);
    cout << "id string is " << eeprom_id << "\n";

    const int SAMPLE_BYTES = 2;
    CHECK(LccDataSetCharacteristics(handle, true, SAMPLE_BYTES, true), __LINE__);

    uint16_t data[NUM_ADC_SAMPLES];
    CHECK(LccDataStartCollect(handle, NUM_ADC_SAMPLES, LCC_TRIGGER_NONE), __LINE__);
    bool is_done = false;
    for (int i = 0; i < 10; ++i) {
        CHECK(LccDataIsCollectDone(handle, &is_done), __LINE__);
        if (is_done) {
            break;
        }
        sleep_for(milliseconds(200));
    }

    int total_bytes_received;
    CHECK(LccDataReceiveUint16Values(handle, data, NUM_ADC_SAMPLES, &total_bytes_received), __LINE__);

    if (total_bytes_received != 2 * NUM_ADC_SAMPLES) {
        FAIL("Not all bytes received\n", __LINE__);
    }

    for (int i = 0; i < NUM_ADC_SAMPLES; ++i) {
        data[i] &= 0x3FFF;
    }

    uint16_t codes[] = { 0x2AAA, 0x1555 };
    int code_index = 1;
    if ((data[0] & 0x3FFF) == codes[0]) {
        code_index = 0;
    }
    for (int i = 0; i < NUM_ADC_SAMPLES; i += 2) {
        if ((data[i] & 0x3FFF) != codes[code_index]) {
            FAIL("Data values not correct\n", __LINE__);
        }
        code_index ^= 1;
    }

    LccCleanup(&handle);

#endif

    return 0;
}