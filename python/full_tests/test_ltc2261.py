import sys
sys.path.append('..')
import math
import time
import struct
import ltc_controller_comm as lcc

EEPROM_ID_SIZE = 50
NUM_ADC_SAMPLES = 64 * 1024

def test():

    print 'Use an LTC2261 setup.'
    raw_input("Press Enter to continue...")

    controller_info = None
    for info in lcc.list_controllers(lcc.TYPE_DC890):
        with lcc.Controller(info) as controller:
            eeprom_id = controller.eeprom_read_string(EEPROM_ID_SIZE)
            if 'LTC2261' in eeprom_id:
                controller_info = info
                break
    if controller_info is None:
        raise Exception("could not find compatible device")

    print "Found LTC2261 demo board:"

    # open and use the device
    with lcc.Controller(controller_info) as controller:
        controller.dc890_gpio_set_byte(0xF8)
        controller.dc890_gpio_spi_set_bits(3, 0, 1)

        controller.spi_send_byte_at_address(0x00, 0x80)
        controller.spi_send_byte_at_address(0x01, 0x00)
        controller.spi_send_byte_at_address(0x02, 0x00)
        controller.spi_send_byte_at_address(0x03, 0x71)
        controller.spi_send_byte_at_address(0x04, 0x28)

        if not controller.fpga_get_is_loaded('DLVDS'):
            controller.fpga_load_file('DLVDS')

        controller.data_set_characteristics(True, 2, True)

        controller.data_start_collect(NUM_ADC_SAMPLES, lcc.TRIGGER_NONE)

        for i in range(10):
            if controller.data_is_collect_done():
                break
            time.sleep(0.2)

        controller.dc890_flush()

        num_bytes, data = controller.data_receive_uint16_values(end=NUM_ADC_SAMPLES)

        codes = [0x2AAA, 0x1555]
        code_index = 1
        if (data[0] & 0x3FFF) == codes[0]:
            code_index = 0

        for i in xrange(0, NUM_ADC_SAMPLES, 2):
            if (data[i] & 0x3FFF) != codes[code_index]:
                raise lcc.HardwareError('Data values not correct')
            code_index ^= 1

if __name__ == '__main__':
    test()
