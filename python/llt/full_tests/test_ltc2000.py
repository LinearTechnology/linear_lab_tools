# -*- coding: utf-8 -*-
"""
Created on Wed June 26 8:46:58 2015

@author: jeremy_s
"""

import sys
import math
import time
import struct
import llt.common.ltc_controller_comm as lcc

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

GPIO_LOW_BASE = 138
FPGA_ACTION_BIT = 16
FPGA_READ_WRITE_BIT = 32
FPGA_ADDRESS_DATA_BIT = 64

SPI_READ_BIT = 0x80
SPI_WRITE_BIT = 0x00

def reset_fpga(controller):
    controller.hs_set_bit_mode(lcc.HS_BIT_MODE_MPSSE)
    controller.hs_fpga_toggle_reset()
    time.sleep(.01)
    controller.hs_fpga_write_data_at_address(FPGA_DAC_PD, 1)
    time.sleep(0.01)
    controller.hs_fpga_write_data_at_address(FPGA_CONTROL_REG, 0x20)
    time.sleep(0.01)
    controller.hs_set_bit_mode(lcc.HS_BIT_MODE_FIFO)


def test():

    print 'Use an LTC2000 setup and a scope.'
    raw_input("Press Enter to continue...")

    controller_info = None
    for info in lcc.list_controllers(lcc.TYPE_HIGH_SPEED):
        if "LTC2000" in info.get_description():
            controller_info = info
            break
    if controller_info is None:
        raise Exception("could not find compatible device")

    print "Found LTC2000 demo board:"
    print "Description: ", controller_info.get_description()
    print "Serial Number: ", controller_info.get_serial_number()

    # open and use the device
    with lcc.Controller(controller_info) as controller:
        spi_write = lambda reg, val: controller.spi_send_byte_at_address(reg | SPI_WRITE_BIT, val)
        spi_read = lambda reg: controller.spi_receive_byte_at_address(reg | SPI_READ_BIT)

        controller.hs_set_bit_mode(lcc.HS_BIT_MODE_MPSSE)

        controller.hs_fpga_toggle_reset()

        print "FPGA ID is ", format(controller.hs_fpga_read_data_at_address(FPGA_ID_REG), "2X")

        controller.hs_fpga_write_data_at_address(FPGA_DAC_PD, 1)

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

        controller.hs_fpga_write_data_at_address(FPGA_CONTROL_REG, 0x20)

        controller.data_set_high_byte_first()

        data = [int(AMPLITUDE * math.sin((NUM_CYCLES_1 * TWO_PI * d) / NUM_DAC_SAMPLES))
                for d in range(NUM_DAC_SAMPLES)]
        controller.hs_set_bit_mode(lcc.HS_BIT_MODE_FIFO)
        if controller.data_send_uint16_values(data) != NUM_DAC_SAMPLES * 2:
            raise RuntimeError("Not all samples sent")
        print "Do you see a sine wave in the scope with frequency = clock_frequency / ", \
            NUM_DAC_SAMPLES / NUM_CYCLES_1, "?"
        response = raw_input("(y = yes, n = no)")
        if response[0] != 'y':
            raise RuntimeError("User indicates output is invalid")
        print "user indicates output is valid"

        print "list_controllers is OK"
        print "constructor OK"
        print "hs_set_bit_mode is OK"
        print "hs_fpga_toggle_reset is OK"
        print "hs_fpga_read_data_at_address is OK"
        print "hs_fpga_write_data_at_address is OK"
        print "spi_send_byte_at_address is OK"
        print "spi_receive_byte_at_address is OK"
        print "data_set_high_byte_first is OK"
        print "data_send_uint16_values is OK"

        reset_fpga(controller)
        data = [AMPLITUDE * math.sin((NUM_CYCLES_2 * TWO_PI * d) / NUM_DAC_SAMPLES) \
                for d in range(NUM_DAC_SAMPLES)]
        data32 = []
        for i in xrange(NUM_DAC_SAMPLES / 2):
            h1 = struct.pack('h', data[2*i])
            h2 = struct.pack('h', data[2*i+1])
            bytes = h2[1] + h2[0] + h2[1] + h1[0]
            i32 = struct.unpack('I', bytes)[0]
            data32.append(i32)

        controller.data_set_low_byte_first()
        controller.hs_set_bit_mode(lcc.HS_BIT_MODE_FIFO)
        if controller.data_send_uint32_values(data32) != NUM_DAC_SAMPLES * 2:
            raise RuntimeError("Not all samples sent")
        print "Do you see a sine wave in the scope with frequency = clock_frequency / ", \
            NUM_DAC_SAMPLES / NUM_CYCLES_2, "?"
        response = raw_input("(y = yes, n = no)")
        if response[0] != 'y':
            raise RuntimeError("User indicates output is invalid")
        print "user indicates output is valid"
        print "data_set_low_byte_first is OK"
        print "data_send_uint32_values is OK"

        reset_fpga(controller)
        data = [AMPLITUDE * math.sin((NUM_CYCLES_3 * TWO_PI * d) / NUM_DAC_SAMPLES) \
                for d in range(NUM_DAC_SAMPLES)]
        data8 = []
        for i in xrange(NUM_DAC_SAMPLES):
            bytes = struct.pack('h', data[i])
            data8.append(struct.unpack('B', bytes[1])[0])
            data8.append(struct.unpack('B', bytes[0])[0])
        controller.hs_set_bit_mode(lcc.HS_BIT_MODE_FIFO)
        if controller.data_send_bytes(data8) != NUM_DAC_SAMPLES * 2:
            raise RuntimeError("Not all samples sent")
        print "Do you see a sine wave in the scope with frequency = clock_frequency / ", \
            NUM_DAC_SAMPLES / NUM_CYCLES_3, "?"
        response = raw_input("(y = yes, n = no)")
        if response[0] != 'y':
            raise RuntimeError("User indicates output is invalid")
        print "user indicates output is valid"
        print "data_send_uint8_values is OK"

        controller.hs_set_bit_mode(lcc.HS_BIT_MODE_MPSSE)

        controller.spi_send_bytes([REG_LINEAR_GAIN | SPI_WRITE_BIT, 0x02])
        if spi_read(REG_LINEAR_GAIN) != 0x02:
            raise RuntimeError("spi_send_bytes didn't seem to work")
        print "spi_send_bytes is OK"

        controller.spi_transceive_bytes([REG_LINEAR_GAIN | SPI_WRITE_BIT, 0x04])
        if controller.spi_transceive_bytes([REG_LINEAR_GAIN | SPI_READ_BIT, 0x00])[1] != 0x04:
            raise RuntimeError("spi_transceive_bytes didn't seem to work")
        print "spi_transceive_bytes is OK"

        controller.spi_send_bytes_at_address(REG_LINEAR_GAIN | SPI_WRITE_BIT, [6])
        if spi_read(REG_LINEAR_GAIN) != 6:
            raise RuntimeError("spi_send_bytes_at_address didn't seem to work")
        print "spi_bytes_at_address is OK"

        if controller.spi_receive_bytes_at_address(REG_LINEAR_GAIN | SPI_READ_BIT, end=1)[0] != 6:
            raise RuntimeError("spi_receive_bytes_at_address didn't seem to work")
        print "spi_receive_bytes_at_address is OK"

        controller.spi_set_cs_state(lcc.SPI_CS_STATE_LOW)
        controller.spi_send_no_chip_select([REG_LINEAR_GAIN | SPI_WRITE_BIT, 0x08])
        controller.spi_set_cs_state(lcc.SPI_CS_STATE_HIGH)
        if spi_read(REG_LINEAR_GAIN) != 0x08:
            raise RuntimeError("spi_set_chip_select or spi_send_no_chip_select didn't seem to work")
        print "spi_set_chip_select is OK"
        print "spi_send_no_chip_select is OK"

        controller.spi_set_cs_state(lcc.SPI_CS_STATE_LOW)
        controller.spi_send_no_chip_select([REG_LINEAR_GAIN | SPI_READ_BIT, 0])
        value = controller.spi_receive_no_chip_select(end=1)[0]
        controller.spi_set_cs_state(lcc.SPI_CS_STATE_HIGH)
        if value != 0x08:
            raise RuntimeError("spi_receive_no_chip_select didn't seem to work")
        print "spi_receive_no_chip_select is OK"

        controller.spi_set_cs_state(lcc.SPI_CS_STATE_LOW)
        controller.spi_transceive_no_chip_select([REG_LINEAR_GAIN | SPI_WRITE_BIT, 0x0A])
        controller.spi_set_cs_state(lcc.SPI_CS_STATE_HIGH)
        controller.spi_set_cs_state(lcc.SPI_CS_STATE_LOW)
        values = controller.spi_transceive_no_chip_select([REG_LINEAR_GAIN | SPI_READ_BIT, 0])
        controller.spi_set_cs_state(lcc.SPI_CS_STATE_HIGH)
        if values[1] != 0x0A:
            raise RuntimeError("spi_transceive_no_chip_select didn't seem to work")
        print "spi_transceive_no_chip_select is OK"

        controller.hs_fpga_write_address(FPGA_ID_REG)
        controller.hs_fpga_write_data(92)
        if controller.hs_fpga_read_data_at_address(FPGA_ID_REG) != 92:
            raise RuntimeError("fpga_write_address or fpga_write_data didn't seem to work")
        print "fpga_write_address is OK"
        print "fpga_write_data is OK"

        controller.hs_fpga_write_data(37)
        if controller.hs_fpga_read_data() != 37:
            raise RuntimeError("fpga_read_data didn't seem to work")
        print "fpga_read_data is OK"

        controller.hs_gpio_write_low_byte(GPIO_LOW_BASE)
        controller.hs_gpio_write_high_byte(56)
        controller.hs_gpio_write_low_byte(GPIO_LOW_BASE | FPGA_ACTION_BIT)
        controller.hs_gpio_write_low_byte(GPIO_LOW_BASE)
        if controller.hs_fpga_read_data() != 56:
            raise RuntimeError("gpio_write_low_byte or gpio_write_high_byte didn't seem to work")
        print "gpio_write_low_byte is OK"
        print "gpio_write_high_byte is OK"

        controller.hs_fpga_write_data(72)
        controller.hs_gpio_write_low_byte(GPIO_LOW_BASE | FPGA_READ_WRITE_BIT)
        controller.hs_gpio_write_low_byte(GPIO_LOW_BASE | FPGA_READ_WRITE_BIT | FPGA_ACTION_BIT)
        value = controller.hs_gpio_read_high_byte()
        controller.hs_gpio_write_low_byte(GPIO_LOW_BASE)
        if value != 72:
            raise RuntimeError("gpio_read_high_byte didn't seem to work")
        print "gpio_read_high_byte is OK"

        if controller.get_description() != controller_info.get_description():
            raise RuntimeError("get_description didn't seem to work")
        print "get_description is OK"

        if controller.get_serial_number() != controller_info.get_serial_number():
            raise RuntimeError("get_serial_number didn't seem to work")
        print "get_serial_number is OK"

        controller.data_send_bytes([0x80])
        controller.hs_purge_io()
        if controller.data_receive_bytes(end=1)[0] != 0:
            raise RuntimeError("purge_io didn't seem to work")
        print "purge_io is OK"

        controller.close()
        with lcc.Controller(controller_info) as stolen_controller:
            stolen_controller.hs_fpga_read_data_at_address(FPGA_ID_REG)
            close_ok = False
            error_ok = False
            try:
                controller.hs_fpga_read_data_at_address(FPGA_ID_REG)
            except Exception as e:
                close_ok = True
                if e.message == "Error opening device by index (FTDI error code: DEVICE_NOT_OPENED)":
                    error_ok = True
            if not close_ok:
                raise RuntimeError("close didn't seem to work")
            if not error_ok:
                raise RuntimeError("get_error_info didn't seem to work")

            print "close is OK"

        controller.hs_fpga_read_data_at_address(FPGA_ID_REG)
        print "with cleanup is OK"

if __name__ == '__main__':
    test()

