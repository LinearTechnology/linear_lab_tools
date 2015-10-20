# -*- coding: utf-8 -*-
'''
DC1369 / LTC2261 Interface Example

This program demonstrates how to communicate with the LTC2261 demo board through Python.
Examples are provided for reading data captured by the ADC, or test data generated by
the ADC.

Board setup is described in Demo Manual 1369. Follow the procedure in this manual, and
verify operation with the PScope software. Once operation is verified, exit PScope
and run this script.

Tested with Python 2.7, Anaconda distribution available from Continuum Analytics,
http://www.continuum.io/

Demo board documentation:
http://www.linear.com/demo/1369
http://www.linear.com/product/LTC2261#demoboards

LTC2261 product page
http://www.linear.com/product/LTC2261


REVISION HISTORY
$Revision$
$Date$

Copyright (c) 2015, Linear Technology Corp.(LTC)
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

The views and conclusions contained in the software and documentation are those
of the authors and should not be interpreted as representing official policies,
either expressed or implied, of Linear Technology Corp.
'''

from time import sleep
import numpy as np
# Import communication library
import sys
sys.path.append("../../")
import ltc_controller_comm as comm

def ltc2261_dc1369(num_samples, verbose=False, do_demo=False):
    if do_demo:
        plot_data = True
        write_to_file = True
    else:
        plot_data = False
        write_to_file = False

    # set TEST_DATA_REG to one of these constants
    DATA_REAL = 0x00
    DATA_ALL_ZEROS = 0x08
    DATA_ALL_ONES = 0x18
    DATA_CHECKERBOARD = 0x28
    DATA_ALTERNATING = 0x38

    TEST_DATA_REG = DATA_REAL

    SAMPLE_BYTES = 2
    
    num_samples_x2 = num_samples * 2
    
    def vprint(s):
        """Print string only if verbose is on"""
        if verbose:
            print s

   # find demo board with correct ID
    EXPECTED_EEPROM_ID = 'LTC2261-14,D9002,DC1369A-A,YEE232T,DLVDS,-------'
    device_info = None
    vprint('Looking for a DC890 with a DC1369A-A demoboard')
    for info in comm.list_controllers(comm.TYPE_DC890):
        with comm.Controller(info) as device:
            eeprom_id = device.eeprom_read_string(len(EXPECTED_EEPROM_ID))
            if 'DC1369' in eeprom_id:
                if verbose:
                    print 'Found a DC1369 demoboard'
                device_info = info
                break
    vprint(device_info)
    if device_info is None:
        raise(comm.HardwareError('Could not find a compatible device'))
    # Open communication to the demo board
    with comm.Controller(device_info) as controller:

        controller.dc890_gpio_set_byte(0xF8)
        controller.dc890_gpio_spi_set_bits(3, 0, 1)

        vprint('Configuring SPI registers')
        if TEST_DATA_REG == DATA_REAL:
            vprint('Set to read real data')
        else:
            vprint('Set to generate test data')
            
        controller.spi_send_byte_at_address(0x00, 0x80)
        controller.spi_send_byte_at_address(0x01, 0x00)
        # Set address 0x02 to a value of 0x01 to enable DCS (useful if clock is not 50% Duty Cycle)
        controller.spi_send_byte_at_address(0x02, 0x00)
        controller.spi_send_byte_at_address(0x03, 0x71)
        controller.spi_send_byte_at_address(0x04, TEST_DATA_REG)

        if not controller.fpga_get_is_loaded("DLVDS"):
            vprint('Loading FPGA')
            controller.fpga_load_file("DLVDS")
        else:
            vprint('FPGA already loaded')

        vprint('Starting data collect')
        # Due to a quirk of the DC1369 and the DDR LVDS load, we have to claim this
        # is a 2 channel part and then throw away the data from the second channel
        # this means we only get half of what we ask for (so we ask for twice as much).
        controller.data_set_high_byte_first()
        controller.data_set_characteristics(True, SAMPLE_BYTES, True)
        controller.data_start_collect(num_samples_x2, comm.TRIGGER_NONE)
        for i in range(10):
            is_done = controller.data_is_collect_done()
            if is_done:
                break
            sleep(0.2)

        if not is_done:
            raise comm.HardwareError('Data collect timed out (missing clock?)')
        vprint('Data collect done.')

        controller.dc890_flush()

        vprint('Reading data')
        num_bytes, data = controller.data_receive_uint16_values(end=num_samples_x2)
        vprint('Data read done')

        # keep data from first channel only
        data_ch1 = [data[2*i] & 0x3FFF for i in range(num_samples)]

        vprint('Writing data to file "data.txt"')
        with open('data.txt', 'w') as f:
            for item in data_ch1:
                f.write(str(item & 0x3FFF) + '\n')
        vprint('File write done.')

        if plot_data:
            from matplotlib import pyplot as plt
            plt.figure(1)
            plt.plot(data_ch1)
            plt.title('Time Domain Data')

            plt.show()

            ADC_AMPLITUDE = 16384.0 / 2.0

            windowscale = (num_samples) / sum(np.blackman(num_samples))
            vprint("Window scaling factor: " + str(windowscale))

            data_ch1 -= np.average(data_ch1)
            windowed_data_ch1 = data_ch1 * np.blackman(num_samples) * windowscale # Apply Blackman window
            freq_domain_ch1 = np.fft.fft(windowed_data_ch1)/(num_samples) # FFT
            freq_domain_magnitude_ch1 = np.abs(freq_domain_ch1) # Extract magnitude
            freq_domain_magnitude_db_ch1 = 20 * np.log10(freq_domain_magnitude_ch1/ADC_AMPLITUDE)

            plt.figure(2)
            plt.title('Frequency Domain')
            plt.plot(freq_domain_magnitude_db_ch1)

            plt.show()

        vprint('All finished!')
    
        return data_ch1

if __name__ == '__main__':
    NUM_SAMPLES = 64 * 1024
    # to use this function in your own code you would typically do
    # data = ltc2261_dc1369(num_samples)
    ltc2261_dc1369(NUM_SAMPLES, verbose=True, do_demo=True)

