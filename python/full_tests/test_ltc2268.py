import sys
sys.path.append('..')
import time
import ltc_controller_comm as lcc

EEPROM_ID_SIZE = 200
NUM_ADC_SAMPLES = 64 * 1024

def read_and_check(controller, expected_data):
    is_done = False
    for i in range(10):
        if controller.data_is_collect_done():
            is_done = True
            break
        time.sleep(0.2)
    if not is_done:
        raise lcc.HardwareError('Data collect timed out.')
    bytes_received, data = controller.data_receive_uint16_values(end=NUM_ADC_SAMPLES)
    if bytes_received != 2 * NUM_ADC_SAMPLES:
        raise lcc.HardwareError('Not all bytes received')
    for d in data:
        if d != expected_data:
            raise lcc.HardwareError('Data values not correct')

def test():

    print 'Use an LTC2268 setup.'
    raw_input("Press Enter to continue...")

    controller_info = None
    for info in lcc.list_controllers(lcc.TYPE_DC1371):
        with lcc.Controller(info) as controller:
            eeprom_id = controller.eeprom_read_string(EEPROM_ID_SIZE)
            if 'LTC2268' in eeprom_id:
                controller_info = info
                break
    if controller_info is None:
        raise Exception("could not find compatible device")

    print "Found LTC2268 demo board:"

    # open and use the device
    with lcc.Controller(controller_info) as controller:
        controller.reset()

        controller.spi_send_byte_at_address(0x00, 0x80)
        controller.spi_send_byte_at_address(0x01, 0x00)
        controller.spi_send_byte_at_address(0x02, 0x00)
        controller.spi_send_byte_at_address(0x03, 0xAA)
        controller.spi_send_byte_at_address(0x04, 0xAA)

        if not controller.fpga_get_is_loaded('S2175'):
            controller.fpga_load_file('S2175')

        controller.dc1371_set_demo_config(0x28000000)

        controller.data_start_collect(NUM_ADC_SAMPLES, lcc.TRIGGER_NONE)
        read_and_check(controller, 0x2AAA)

        # print 'Please disconnect the clock'
        # raw_input('Press Enter to continue...')
        # controller.data_start_collect(NUM_ADC_SAMPLES, lcc.TRIGGER_NONE)
        # if controller.data_is_collect_done():
        #     raise lcc.HardwareError('collect finished with no clock')
        # controller.data_cancel_collect()

        # print 'Please reconnect the clock'
        # raw_input('Press Enter to continue...')

        controller.spi_send_byte_at_address(0x03, 0xAA)
        controller.spi_send_byte_at_address(0x04, 0xBB)

        controller.data_start_collect(NUM_ADC_SAMPLES, lcc.TRIGGER_NONE)
        read_and_check(controller, 0x2ABB)

        controller.data_start_collect(NUM_ADC_SAMPLES, lcc.TRIGGER_NONE)
        for i in range(10):
            if controller.data_is_collect_done():
                is_done = True
                break
            time.sleep(0.2)
        if not is_done:
            raise lcc.HardwareError('Data collect timed out.')

        controller.data_receive_uint16_values(end = 1024)
        controller.data_cancel_collect()

        controller.spi_send_byte_at_address(0x03, 0xAA)
        controller.spi_send_byte_at_address(0x04, 0xCC)

        controller.data_start_collect(NUM_ADC_SAMPLES, lcc.TRIGGER_NONE)
        read_and_check(controller, 0x2ACC)
        
        controller.fpga_load_file_chunked('S2157')
        controller.fpga_cancel_load()

        controller.fpga_load_file('S2195')
        if not controller.fpga_get_is_loaded('S2195'):
            raise lcc.HardwareError('FPGA load failed')

if __name__ == '__main__':
    test()