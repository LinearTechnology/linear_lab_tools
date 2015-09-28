# -*- coding: utf-8 -*-
"""
Created on Wed June 26 8:46:58 2015

@author: jeremy_s
"""

import math
import time
import array
import struct
import ltc_high_speed_comm as lths

NUM_DAC_SAMPLES = 64 * 1024
NUM_CYCLES_1 = 489
NUM_CYCLES_2 = 2 * NUM_CYCLES_1
NUM_CYCLES_3 = 2 * NUM_CYCLES_2
AMPLITUDE = 32000
TWO_PI = 2 * math.pi

REG_RESET_PD = 1
REG_CLK_CONFIG = 2
REG_CLK_PHASE = 3
REG_PORT_EN = 4
REG_SYNC_PHASE = 5
REG_PHASE_COMP_OUT = 6
REG_LINEAR_GAIN = 7
REG_LINEARIZATION = 8
REG_DAC_GAIN = 9
REG_LVDS_MUX = 24
REG_TEMP_SELECT = 25
REG_PATTERN_ENABLE = 30
REG_PATTERN_DATA = 31

FPGA_ID_REG = 0
FPGA_CONTROL_REG = 1
FPGA_STATUS_REG = 2
FPGA_DAC_PD = 3

NUM_ADC_SAMPLES = 16384

CAPTURE_CONFIG_REG = 1
CAPTURE_CONTROL_REG = 2
CAPTURE_RESET_REG = 3
CAPTURE_STATUS_REG = 4
CLOCK_STATUS_REG = 6

MAX_EEPROM_CHARS = 240

JESD204B_WB0_REG = 7
JESD204B_WB1_REG = 8
JESD204B_WB2_REG = 9
JESD204B_WB3_REG = 10
JESD204B_CONFIG_REG = 11
JESD204B_RB0_REG = 12
JESD204B_RB1_REG = 13
JESD204B_RB2_REG = 14
JESD204B_RB3_REG = 15
JESD204B_CHECK_REG = 16

SPI_READ_BIT = 128
SPI_WRITE_BIT = 0

GPIO_LOW_BASE = 138
FPGA_ACTION_BIT = 16
FPGA_READ_WRITE_BIT = 32
FPGA_ADDRESS_DATA_BIT = 64

LTC2123_ID_STRING = (r"[0074 DEMO 10 DC1974A-A LTC2124-14 D2124" "\r\n"
                     r"ADC 14 16 2 0000 00 00 00 00" "\r\n"
                     r"DBFLG 0003 00 00 00 00" "\r\n"
                     r"FPGA S0000 T0" "\r\n"
                     r"187F]")


def reset_fpga(device):
    device.set_bit_mode(lths.BIT_MODE_MPSSE)
    device.fpga_toggle_reset()
    time.sleep(.01)
    device.fpga_write_data_at_address(FPGA_DAC_PD, 1)
    time.sleep(0.01)
    device.fpga_write_data_at_address(FPGA_CONTROL_REG, 0x20)
    time.sleep(0.01)
    device.set_bit_mode(lths.BIT_MODE_FIFO)


def write_jedec_reg(device, address, b3, b2, b1, b0):
    device.fpga_write_data_at_address(JESD204B_WB3_REG, b3)
    device.fpga_write_data_at_address(JESD204B_WB2_REG, b2)
    device.fpga_write_data_at_address(JESD204B_WB1_REG, b1)
    device.fpga_write_data_at_address(JESD204B_WB0_REG, b0)
    device.fpga_write_data_at_address(JESD204B_CONFIG_REG, (address << 2) | 0x02)
    if device.fpga_read_data() & 0x01 == 0:
        raise RuntimeError("Got bad FPGA status in write_jedec_reg")


def init_adc(device, spi_write):
    device.close()
    device.set_bit_mode(lths.BIT_MODE_MPSSE)
    device.fpga_toggle_reset()
    spi_write(0x01, 0x00)
    spi_write(0x02, 0x00)
    spi_write(0x03, 0xAB)
    spi_write(0x04, 0x0C)
    spi_write(0x05, 0x01)
    spi_write(0x06, 0x17)
    spi_write(0x07, 0x00)
    spi_write(0x08, 0x00)
    spi_write(0x09, 0x04)

    write_jedec_reg(device, 0x01, 0x00, 0x00, 0x00, 0x01)
    write_jedec_reg(device, 0x02, 0x00, 0x00, 0x00, 0x01)
    write_jedec_reg(device, 0x03, 0x00, 0x00, 0x00, 0x17)
    write_jedec_reg(device, 0x00, 0x00, 0x00, 0x01, 0x02)

    if device.fpga_read_data_at_address(CLOCK_STATUS_REG) != 0x1E:
        raise RuntimeError("CLOCK_STATUS_REG value was not 0x1E")
    device.fpga_write_data_at_address(CAPTURE_CONFIG_REG, 0x78)
    device.fpga_write_data_at_address(CAPTURE_RESET_REG, 0x01)
    device.fpga_write_data_at_address(CAPTURE_CONTROL_REG, 0x01)
    time.sleep(0.05)
    if device.fpga_read_data_at_address(CAPTURE_STATUS_REG) & 0x31 != 0x31:
        raise RuntimeError("CAPTURE_STATUS_REG was not 0x31")


def next_prbs(current_value):
    next_value = ((current_value << 1) ^ (current_value << 2)) & 0xFFFC
    next_value |= ((next_value >> 15) ^ (next_value >> 14)) & 0x0001
    next_value |= ((next_value >> 14) ^ (current_value << 1)) & 0x0002
    return next_value


def check_prbs(data):
    if data[0] == 0:
        return False
    for i in xrange(1, len(data)):
        next_value = next_prbs(data[i - 1])
        if data[i] != next_value:
            return False
    return True


print 'Test battery 1'
print 'Use an LTC2000 setup and a scope.'
raw_input("Press Enter to continue...")

device_info = None
for info in lths.list_devices():
    if "LTC2000" in info.get_description():
        device_info = info
        break
if device_info is None:
    raise Exception("could not find compatible device")

print "Found LTC2000 demo board:"
print "Description: ", device_info.get_description()
print "Serial Number: ", device_info.get_serial_number()

# open and use the device
with lths.Lths(device_info) as device:
    spi_write = lambda reg, val: device.spi_send_byte_at_address(reg | SPI_WRITE_BIT, val)
    spi_read = lambda reg: device.spi_receive_byte_at_address(reg | SPI_READ_BIT)

    device.set_bit_mode(lths.BIT_MODE_MPSSE)

    device.fpga_toggle_reset()

    print "FPGA ID is ", format(device.fpga_read_data_at_address(FPGA_ID_REG), "2X")

    device.fpga_write_data_at_address(FPGA_DAC_PD, 1)

    spi_write(REG_RESET_PD, 0x00)
    spi_write(REG_RESET_PD, 0x00)
    spi_write(REG_CLK_PHASE, 0x05)
    spi_write(REG_PORT_EN, 0x0B)
    spi_write(REG_SYNC_PHASE, 0x00)
    spi_write(REG_LINEAR_GAIN, 0x00)
    spi_write(REG_LINEARIZATION, 0x08)
    spi_write(REG_DAC_GAIN, 0x20)
    spi_write(REG_LVDS_MUX, 0x00)
    spi_write(REG_TEMP_SELECT, 0x00)
    spi_write(REG_PATTERN_ENABLE, 0x00)

    if spi_read(REG_RESET_PD) & 0xCF != 0x00:
        raise RuntimeError("Error reading SPI register ", format(REG_RESET_PD, "2X"))
    if spi_read(REG_CLK_PHASE) != 0x07:
        raise RuntimeError("Error reading SPI register ", format(REG_CLK_PHASE, "2X"))
    if spi_read(REG_PORT_EN) != 0x0B:
        raise RuntimeError("Error reading SPI register ", format(REG_PORT_EN, "2X"))
    if spi_read(REG_SYNC_PHASE) & 0xFC != 0x00:
        raise RuntimeError("Error reading SPI register ", format(REG_SYNC_PHASE, "2X"))
    if spi_read(REG_LINEAR_GAIN) != 0x00:
        raise RuntimeError("Error reading SPI register ", format(REG_LINEAR_GAIN, "2X"))
    if spi_read(REG_LINEARIZATION) != 0x08:
        raise RuntimeError("Error reading SPI register ", format(REG_LINEARIZATION, "2X"))
    if spi_read(REG_DAC_GAIN) != 0x20:
        raise RuntimeError("Error reading SPI register ", format(REG_DAC_GAIN, "2X"))

    device.fpga_write_data_at_address(FPGA_CONTROL_REG, 0x20)

    data = [int(AMPLITUDE * math.sin((NUM_CYCLES_1 * TWO_PI * d) / NUM_DAC_SAMPLES))
            for d in range(NUM_DAC_SAMPLES)]
    device.set_bit_mode(lths.BIT_MODE_FIFO)
    if device.fifo_send_uint16_values(data) != NUM_DAC_SAMPLES * 2:
        raise RuntimeError("Not all samples sent")
    print "Do you see a sine wave in the scope with frequency = clock_frequency / ", \
        NUM_DAC_SAMPLES / NUM_CYCLES_1, "?"
    response = raw_input("(y = yes, n = no)")
    if response[0] != 'y':
        raise RuntimeError("User indicates output is invalid")
    print "user indicates output is valid"

    print "list_devices is OK"
    print "constructor OK"
    print "set_bit_mode is OK"
    print "fpga_toggle_reset is OK"
    print "fpga_read_data_at_address is OK"
    print "fpga_write_data_at_address is OK"
    print "spi_send_byte_at_address is OK"
    print "spi_receive_byte_at_address is OK"
    print "fifo_send_uint16_values is OK"

    reset_fpga(device)
    data = [AMPLITUDE * math.sin((NUM_CYCLES_2 * TWO_PI * d) / NUM_DAC_SAMPLES) \
            for d in range(NUM_DAC_SAMPLES)]
    data32 = []
    for i in xrange(NUM_DAC_SAMPLES / 2):
        data32.append(struct.unpack('I', struct.pack('h', data[2 * i + 1]) +
                                    struct.pack('h', data[2 * i]))[0])
    device.set_bit_mode(lths.BIT_MODE_FIFO)
    if device.fifo_send_uint32_values(data32) != NUM_DAC_SAMPLES * 2:
        raise RuntimeError("Not all samples sent")
    print "Do you see a sine wave in the scope with frequency = clock_frequency / ", \
        NUM_DAC_SAMPLES / NUM_CYCLES_2, "?"
    response = raw_input("(y = yes, n = no)")
    if response[0] != 'y':
        raise RuntimeError("User indicates output is invalid")
    print "user indicates output is valid"
    print "fifo_send_uint32_values is OK"

    reset_fpga(device)
    data = [AMPLITUDE * math.sin((NUM_CYCLES_3 * TWO_PI * d) / NUM_DAC_SAMPLES) \
            for d in range(NUM_DAC_SAMPLES)]
    data8 = []
    for i in xrange(NUM_DAC_SAMPLES):
        bytes = struct.pack('h', data[i])
        data8.append(struct.unpack('B', bytes[1])[0])
        data8.append(struct.unpack('B', bytes[0])[0])
    device.set_bit_mode(lths.BIT_MODE_FIFO)
    if device.fifo_send_bytes(data8) != NUM_DAC_SAMPLES * 2:
        raise RuntimeError("Not all samples sent")
    print "Do you see a sine wave in the scope with frequency = clock_frequency / ", \
        NUM_DAC_SAMPLES / NUM_CYCLES_3, "?"
    response = raw_input("(y = yes, n = no)")
    if response[0] != 'y':
        raise RuntimeError("User indicates output is invalid")
    print "user indicates output is valid"
    print "fifo_send_uint8_values is OK"

    device.set_bit_mode(lths.BIT_MODE_MPSSE)

    device.spi_send_bytes([REG_LINEAR_GAIN | SPI_WRITE_BIT, 0x02])
    if spi_read(REG_LINEAR_GAIN) != 0x02:
        raise RuntimeError("spi_send_bytes didn't seem to work")
    print "spi_send_bytes is OK"

    device.spi_transceive_bytes([REG_LINEAR_GAIN | SPI_WRITE_BIT, 0x04])
    if device.spi_transceive_bytes([REG_LINEAR_GAIN | SPI_READ_BIT, 0x00])[1] != 0x04:
        raise RuntimeError("spi_transceive_bytes didn't seem to work")
    print "spi_transceive_bytes is OK"

    device.spi_send_bytes_at_address(REG_LINEAR_GAIN | SPI_WRITE_BIT, [6])
    if spi_read(REG_LINEAR_GAIN) != 6:
        raise RuntimeError("spi_send_bytes_at_address didn't seem to work")
    print "spi_bytes_at_address is OK"

    if device.spi_receive_bytes_at_address(REG_LINEAR_GAIN | SPI_READ_BIT, end=1)[0] != 6:
        raise RuntimeError("spi_receive_bytes_at_address didn't seem to work")
    print "spi_receive_bytes_at_address is OK"

    device.spi_set_chip_select(lths.SPI_CHIP_SELECT_LOW)
    device.spi_send_no_chip_select([REG_LINEAR_GAIN | SPI_WRITE_BIT, 0x08])
    device.spi_set_chip_select(lths.SPI_CHIP_SELECT_HIGH)
    if spi_read(REG_LINEAR_GAIN) != 0x08:
        raise RuntimeError("spi_set_chip_select or spi_send_no_chip_select didn't seem to work")
    print "spi_set_chip_select is OK"
    print "spi_send_no_chip_select is OK"

    device.spi_set_chip_select(lths.SPI_CHIP_SELECT_LOW)
    device.spi_send_no_chip_select([REG_LINEAR_GAIN | SPI_READ_BIT, 0])
    value = device.spi_receive_no_chip_select(end=1)[0]
    device.spi_set_chip_select(lths.SPI_CHIP_SELECT_HIGH)
    if value != 0x08:
        raise RuntimeError("spi_receive_no_chip_select didn't seem to work")
    print "spi_receive_no_chip_select is OK"

    device.spi_set_chip_select(lths.SPI_CHIP_SELECT_LOW)
    device.spi_transceive_no_chip_select([REG_LINEAR_GAIN | SPI_WRITE_BIT, 0x0A])
    device.spi_set_chip_select(lths.SPI_CHIP_SELECT_HIGH)
    device.spi_set_chip_select(lths.SPI_CHIP_SELECT_LOW)
    values = device.spi_transceive_no_chip_select([REG_LINEAR_GAIN | SPI_READ_BIT, 0])
    device.spi_set_chip_select(lths.SPI_CHIP_SELECT_HIGH)
    if values[1] != 0x0A:
        raise RuntimeError("spi_transceive_no_chip_select didn't seem to work")
    print "spi_transceive_no_chip_select is OK"

    device.fpga_write_address(FPGA_ID_REG)
    device.fpga_write_data(92)
    if device.fpga_read_data_at_address(FPGA_ID_REG) != 92:
        raise RuntimeError("fpga_write_address or fpga_write_data didn't seem to work")
    print "fpga_write_address is OK"
    print "fpga_write_data is OK"

    device.fpga_write_data(37)
    if device.fpga_read_data() != 37:
        raise RuntimeError("fpga_read_data didn't seem to work")
    print "fpga_read_data is OK"

    device.gpio_write_low_byte(GPIO_LOW_BASE)
    device.gpio_write_high_byte(56)
    device.gpio_write_low_byte(GPIO_LOW_BASE | FPGA_ACTION_BIT)
    device.gpio_write_low_byte(GPIO_LOW_BASE)
    if device.fpga_read_data() != 56:
        raise RuntimeError("gpio_write_low_byte or gpio_write_high_byte didn't seem to work")
    print "gpio_write_low_byte is OK"
    print "gpio_write_high_byte is OK"

    device.fpga_write_data(72)
    device.gpio_write_low_byte(GPIO_LOW_BASE | FPGA_READ_WRITE_BIT)
    device.gpio_write_low_byte(GPIO_LOW_BASE | FPGA_READ_WRITE_BIT | FPGA_ACTION_BIT)
    value = device.gpio_read_high_byte()
    device.gpio_write_low_byte(GPIO_LOW_BASE)
    if value != 72:
        raise RuntimeError("gpio_read_high_byte didn't seem to work")
    print "gpio_read_high_byte is OK"

    if device.get_description() != device_info.get_description():
        raise RuntimeError("get_description didn't seem to work")
    print "get_description is OK"

    if device.get_serial_number() != device_info.get_serial_number():
        raise RuntimeError("get_serial_number didn't seem to work")
    print "get_serial_number is OK"

    device.set_timeouts(500, 500)
    start = time.time()
    device.fifo_receive_bytes(end=1)
    elapsed = time.time() - start
    if elapsed < 0.250 or elapsed > 0.750:
        raise RuntimeError("set_timeouts didn't seem to work")
    device.set_timeouts(3000, 3000)
    start = time.time()
    device.fifo_receive_bytes(end=1)
    elapsed = time.time() - start
    if elapsed < 2.750 or elapsed > 3.250:
        raise RuntimeError("set_timeouts didn't seem to work")
    print "set_timeouts is OK"

    device.fifo_send_bytes([0x80])
    device.purge_io()
    if device.fifo_receive_bytes(end=1)[0] != 0:
        raise RuntimeError("purge_io didn't seem to work")
    print "purge_io is OK"

    device.close()
    with lths.Lths(device_info) as stolen_device:
        stolen_device.fpga_read_data_at_address(FPGA_ID_REG)
        close_ok = False
        error_ok = False
        try:
            device.fpga_read_data_at_address(FPGA_ID_REG)
        except Exception as e:
            close_ok = True
            if e.message == "Error opening the device.":
                error_ok = True
        if not close_ok:
            raise RuntimeError("close didn't seem to work")
        if not error_ok:
            raise RuntimeError("get_error_info didn't seem to work")

        print "close is OK"

    device.fpga_read_data_at_address(FPGA_ID_REG)
    print "with cleanup is OK"

print 'Test battery 2'
print 'Use an LTC2123 setup.'
raw_input("Press Enter to continue...")

device_info = None
for info in lths.list_devices():
    if info.get_description() == "LTC Communication Interface":
        device_info = info
        break
if device_info is None:
    raise RuntimeError("could not find compatible device")

print "Found LTC2123 demo board:"
print "Description: ", device_info.get_description()
print "Serial Number: ", device_info.get_serial_number()

# open and use the device
with lths.Lths(device_info) as device:
    spi_write = lambda reg, val: device.spi_send_byte_at_address(reg | SPI_WRITE_BIT, val)
    spi_read = lambda reg: device.spi_receive_byte_at_address(reg | SPI_READ_BIT)

    device.fifo_set_low_byte_first()

    init_adc(device, spi_write)
    device.set_bit_mode(lths.BIT_MODE_FIFO)
    num_bytes, data = device.fifo_receive_uint16_values(end=NUM_ADC_SAMPLES)
    if num_bytes != NUM_ADC_SAMPLES * 2:
        raise RuntimeError("didn't receive all bytes")
    channel_a = []
    channel_b = []
    for i in xrange(0, NUM_ADC_SAMPLES / 2, 2):
        channel_a.append(data[2 * i])
        channel_a.append(data[2 * i + 1])
        channel_b.append(data[2 * i + 2])
        channel_b.append(data[2 * i + 3])

    if not check_prbs(channel_a):
        raise RuntimeError("fifo_receive_uint16_values didn't seem to work")
    if not check_prbs(channel_b):
        raise RuntimeError("fifo_receive_uint16_values didn't seem to work")
    print "fifo_receive_uint16_values is OK"

    init_adc(device, spi_write)
    device.set_bit_mode(lths.BIT_MODE_FIFO)
    num_bytes, data = device.fifo_receive_uint32_values(end=NUM_ADC_SAMPLES / 2)
    if num_bytes != NUM_ADC_SAMPLES * 2:
        raise RuntimeError("didn't receive all bytes")
    channel_a = []
    channel_b = []
    for i in xrange(0, NUM_ADC_SAMPLES / 2, 2):
        two_samples = struct.pack('L', data[i])
        channel_a.append(struct.unpack('H', two_samples[0:2])[0])
        channel_a.append(struct.unpack('H', two_samples[2:4])[0])
        two_samples = struct.pack('L', data[i + 1])
        channel_b.append(struct.unpack('H', two_samples[0:2])[0])
        channel_b.append(struct.unpack('H', two_samples[2:4])[0])
    if not check_prbs(channel_a):
        raise RuntimeError("fifo_receive_uint32_values didn't seem to work")
    if not check_prbs(channel_b):
        raise RuntimeError("fifo_receive_uint32_values didn't seem to work")
    print "fifo_receive_uint32_values is OK"

    init_adc(device, spi_write)
    device.set_bit_mode(lths.BIT_MODE_FIFO)
    num_bytes, data = device.fifo_receive_bytes(end=NUM_ADC_SAMPLES * 2)
    if num_bytes != NUM_ADC_SAMPLES * 2:
        raise RuntimeError("didn't receive all bytes")
    channel_a = []
    channel_b = []
    for i in xrange(0, NUM_ADC_SAMPLES / 2, 2):
        byte_array = bytearray(data[(4 * i):(4 * i + 8)])
        channel_a.append(struct.unpack('H', byte_array[0:2])[0])
        channel_a.append(struct.unpack('H', byte_array[2:4])[0])
        channel_b.append(struct.unpack('H', byte_array[4:6])[0])
        channel_b.append(struct.unpack('H', byte_array[6:8])[0])
    if not check_prbs(channel_a):
        raise RuntimeError("fifo_receive_bytes didn't seem to work")
    if not check_prbs(channel_b):
        raise RuntimeError("fifo_receive_bytes didn't seem to work")
    print "fifo_receive_bytes is OK"

    device.set_bit_mode(lths.BIT_MODE_MPSSE)
    device.fpga_toggle_reset()

    id_str = device.fpga_eeprom_read_string(MAX_EEPROM_CHARS)
    if (id_str[0:len(LTC2123_ID_STRING)] != LTC2123_ID_STRING):
        raise RuntimeError("fpga_eeprom_receive_string didn't seem to work.")
    print "fpga_eeprom_receive_string is OK"

    device.fpga_write_data_at_address(0x00, 0x00)
    device.fpga_eeprom_set_bit_bang_register(0x00)
    try:
        device.fpga_eeprom_read_string(1)
    except:
        pass  # we expect this to throw an error
    if device.fpga_read_data_at_address(0x00) == 0:
        raise RuntimeError("fpga_eeprom_set_bitbang_register didn't seem to work")
    print "fpga_i2c_set_bitbang_register is OK"

print "Test battery 3"
print "Use an FT2232H mini-module with:"
print "CN2-5 connected to CN2-11"
print "CN3-1 connected to CN3-3"
print "CN3-17 connected to CN3-24"
raw_input("Press Enter to continue...")

device_info = None
for info in lths.list_devices():
    if info.get_description() == "LTC Communication Interface":
        device_info = info
        break
if device_info is None:
    raise RuntimeError("could not find compatible device")

print "Found Mini-module:"
print "Description: ", device_info.get_description()
print "Serial Number: ", device_info.get_serial_number()

# open and use the device
with lths.Lths(device_info) as device:
    device.set_bit_mode(lths.BIT_MODE_MPSSE)
    device.gpio_write_high_byte(0x01)
    if device.spi_receive_bytes(end=1)[0] != 0xFF:
        raise RuntimeError("spi_receive_bytes_didn't seem to work")
    device.gpio_write_high_byte(0x00)
    if device.spi_receive_bytes(end=1)[0] != 0x00:
        raise RuntimeError("spi_receive_bytes_didn't seem to work")
    print "spi_receive_bytes is OK"

    device.gpio_write_high_byte(0x01)
    if (device.gpio_read_low_byte() & 0x04) == 0:
        raise RuntimeError("gpio_read_low_byte didn't seem to work")
    device.gpio_write_high_byte(0x00)
    if (device.gpio_read_low_byte()) & 0x04 != 0:
        raise RuntimeError("gpio_read_low_byte didn't seem to work")
    print "gpio_read_low_byte is OK"

print "All tests passed!"
