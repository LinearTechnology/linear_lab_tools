import math
import time
import struct
import llt.common.ltc_controller_comm as lcc

SPI_READ_BIT = 0x80
SPI_WRITE_BIT = 0x00

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

LTC2123_ID_STRING = (r"[0074 DEMO 10 DC1974A-A LTC2124-14 D2124" "\r\n"
                     r"ADC 14 16 2 0000 00 00 00 00" "\r\n"
                     r"DBFLG 0003 00 00 00 00" "\r\n"
                     r"FPGA S0000 T0" "\r\n"
                     r"187F]")

def write_jedec_reg(controller, address, b3, b2, b1, b0):
    controller.hs_fpga_write_data_at_address(JESD204B_WB3_REG, b3)
    controller.hs_fpga_write_data_at_address(JESD204B_WB2_REG, b2)
    controller.hs_fpga_write_data_at_address(JESD204B_WB1_REG, b1)
    controller.hs_fpga_write_data_at_address(JESD204B_WB0_REG, b0)
    controller.hs_fpga_write_data_at_address(JESD204B_CONFIG_REG, (address << 2) | 0x02)
    if controller.hs_fpga_read_data() & 0x01 == 0:
        raise RuntimeError("Got bad FPGA status in write_jedec_reg")

def init_adc(controller, spi_write):
    controller.close()
    controller.hs_set_bit_mode(lcc.HS_BIT_MODE_MPSSE)
    controller.hs_fpga_toggle_reset()
    spi_write(0x01, 0x00)
    spi_write(0x02, 0x00)
    spi_write(0x03, 0xAB)
    spi_write(0x04, 0x0C)
    spi_write(0x05, 0x01)
    spi_write(0x06, 0x17)
    spi_write(0x07, 0x00)
    spi_write(0x08, 0x00)
    spi_write(0x09, 0x04)

    write_jedec_reg(controller, 0x01, 0x00, 0x00, 0x00, 0x01)
    write_jedec_reg(controller, 0x02, 0x00, 0x00, 0x00, 0x01)
    write_jedec_reg(controller, 0x03, 0x00, 0x00, 0x00, 0x17)
    write_jedec_reg(controller, 0x00, 0x00, 0x00, 0x01, 0x02)

    if controller.hs_fpga_read_data_at_address(CLOCK_STATUS_REG) != 0x1E:
        raise RuntimeError("CLOCK_STATUS_REG value was not 0x1E")
    controller.hs_fpga_write_data_at_address(CAPTURE_CONFIG_REG, 0x78)
    controller.hs_fpga_write_data_at_address(CAPTURE_RESET_REG, 0x01)
    controller.hs_fpga_write_data_at_address(CAPTURE_CONTROL_REG, 0x01)
    time.sleep(0.05)
    if controller.hs_fpga_read_data_at_address(CAPTURE_STATUS_REG) & 0x31 != 0x31:
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

def test():
    print 'Use an LTC2123 setup.'
    raw_input("Press Enter to continue...")

    controller_info = None
    for info in lcc.list_controllers(lcc.TYPE_HIGH_SPEED):
        if info.get_description() == "LTC Communication Interface":
            controller_info = info
            break
    if controller_info is None:
        raise RuntimeError("could not find compatible device")

    print "Found LTC2123 demo board:"
    print "Description: ", controller_info.get_description()
    print "Serial Number: ", controller_info.get_serial_number()

    # open and use the device
    with lcc.Controller(controller_info) as controller:
        spi_write = lambda reg, val: controller.spi_send_byte_at_address(reg | SPI_WRITE_BIT, val)
        spi_read = lambda reg: controller.spi_receive_byte_at_address(reg | SPI_READ_BIT)

        controller.data_set_low_byte_first()

        init_adc(controller, spi_write)
        controller.hs_set_bit_mode(lcc.HS_BIT_MODE_FIFO)
        num_bytes, data = controller.data_receive_uint16_values(end=NUM_ADC_SAMPLES)
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
            raise RuntimeError("data_receive_uint16_values didn't seem to work")
        if not check_prbs(channel_b):
            raise RuntimeError("data_receive_uint16_values didn't seem to work")
        print "data_receive_uint16_values is OK"

        init_adc(controller, spi_write)
        controller.hs_set_bit_mode(lcc.HS_BIT_MODE_FIFO)
        num_bytes, data = controller.data_receive_uint32_values(end=NUM_ADC_SAMPLES / 2)
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
            raise RuntimeError("data_receive_uint32_values didn't seem to work")
        if not check_prbs(channel_b):
            raise RuntimeError("data_receive_uint32_values didn't seem to work")
        print "data_receive_uint32_values is OK"

        init_adc(controller, spi_write)
        controller.hs_set_bit_mode(lcc.HS_BIT_MODE_FIFO)
        num_bytes, data = controller.data_receive_bytes(end=NUM_ADC_SAMPLES * 2)
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
            raise RuntimeError("data_receive_bytes didn't seem to work")
        if not check_prbs(channel_b):
            raise RuntimeError("data_receive_bytes didn't seem to work")
        print "data_receive_bytes is OK"

        controller.hs_set_bit_mode(lcc.HS_BIT_MODE_MPSSE)
        controller.hs_fpga_toggle_reset()

        id_str = controller.eeprom_read_string(MAX_EEPROM_CHARS)
        if (id_str[0:len(LTC2123_ID_STRING)] != LTC2123_ID_STRING):
            raise RuntimeError("fpga_eeprom_receive_string didn't seem to work.")
        print "fpga_eeprom_receive_string is OK"

        controller.hs_fpga_write_data_at_address(0x00, 0x00)
        controller.hs_fpga_eeprom_set_bit_bang_register(0x00)
        try:
            controller.eeprom_read_string(1)
        except:
            pass  # we expect this to throw an error
        if controller.hs_fpga_read_data_at_address(0x00) == 0:
            raise RuntimeError("fpga_eeprom_set_bitbang_register didn't seem to work")
        print "fpga_i2c_set_bitbang_register is OK"

if __name__ == '__main__':
    test()