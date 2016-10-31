import sys
import llt.common.ltc_controller_comm as lcc

def test():

    print "Use an FT2232H mini-module with:"
    print "CN2-5 connected to CN2-11"
    print "CN3-1 connected to CN3-3"
    print "CN3-17 connected to CN3-24"
    raw_input("Press Enter to continue...")

    controller_info = None
    for info in lcc.list_controllers(lcc.TYPE_HIGH_SPEED):
        if info.get_description() == "LTC Communication Interface":
            controller_info = info
            break
    if controller_info is None:
        raise RuntimeError("could not find compatible device")

    print "Found Mini-module:"
    print "Description: ", controller_info.get_description()
    print "Serial Number: ", controller_info.get_serial_number()

    # open and use the device
    with lcc.Controller(controller_info) as controller:
        controller.hs_set_bit_mode(lcc.HS_BIT_MODE_MPSSE)
        controller.hs_gpio_write_high_byte(0x01)
        if controller.spi_receive_bytes(end=1)[0] != 0xFF:
            raise RuntimeError("spi_receive_bytes_didn't seem to work")
        controller.hs_gpio_write_high_byte(0x00)
        if controller.spi_receive_bytes(end=1)[0] != 0x00:
            raise RuntimeError("spi_receive_bytes_didn't seem to work")
        print "spi_receive_bytes is OK"

        controller.hs_gpio_write_high_byte(0x01)
        if (controller.hs_gpio_read_low_byte() & 0x04) == 0:
            raise RuntimeError("gpio_read_low_byte didn't seem to work")
        controller.hs_gpio_write_high_byte(0x00)
        if (controller.hs_gpio_read_low_byte()) & 0x04 != 0:
            raise RuntimeError("gpio_read_low_byte didn't seem to work")
        print "gpio_read_low_byte is OK"

if __name__ == '__main__':
    test()