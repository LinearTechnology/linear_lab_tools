# -*- coding: utf-8 -*-
'''
DC1532 / LTC2268 Interface Example

This program demonstrates how to communicate with the LTC2268 demo board through Python.
Examples are provided for reading data captured by the ADC, or test data generated by
the ADC.

Board setup is described in Demo Manual 1532. Follow the procedure in this manual, and
verify operation with the PScope software. Once operation is verified, exit PScope
and run this script.

Tested with Python 2.7, Anaconda distribution available from Continuum Analytics,
http://www.continuum.io/

Demo board documentation:
http://www.linear.com/demo/1532
http://www.linear.com/product/LTC2268#demoboards

LTC2268 product page
http://www.linear.com/product/LTC2268


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
# Import communication library
import sys
sys.path.append("../../")
#print sys.path
from matplotlib import pyplot as plt
import numpy as np


import ltc_controller_comm as comm

# Print extra information to console
verbose = True
# Plot data to screen
plot_data = True
#Write data out to a text file
write_to_file = True

# change this to collect real or test pattern data
use_test_data = False
# change this to set the output when using the test pattern
test_data_value = 0x2AAA

NUM_ADC_SAMPLES = 64 * 1024
TOTAL_ADC_SAMPLES = 2 * NUM_ADC_SAMPLES # two channel part
SAMPLE_BYTES = 2

# find demo board with correct ID
expected_eeprom_id = '[0074 DEMO 10 DC1532A-A LTC2268-14 D2175\r\n' + \
            'ADC 14 14 2 0000 00 00 00 00\r\n' + \
            'DBFLG 0003 28 00 00 00\r\n' + \
            'FPGA S2175 T2\r\n' + \
            '8006]'
controller_info = None
print 'Looking for a DC1371 with a DC1532A-A demoboard'
for info in comm.list_controllers(comm.TYPE_DC1371):
    with comm.Controller(info) as controller:
        found_eeprom_id = controller.eeprom_read_string(len(expected_eeprom_id))
        if found_eeprom_id == expected_eeprom_id:
            if verbose:
                print 'Found a DC1532A-A demoboard'
            controller_info = info
            break
if controller_info is None:
    raise(comm.HardwareError('Could not find a compatible device'))
# Open communication to the demo board
with comm.Controller(controller_info) as controller:

    if verbose:
        print 'Configuring SPI registers'

    if use_test_data:
        if verbose:
            print 'Set to generate test data'
        reg3 = 0x80 | ((test_data_value >> 8) & 0x3F)
        reg4 = test_data_value & 0xFF
    else:
        if verbose:
            print 'Set to read real data'
        reg3 = 0x00
        reg4 = 0x00

    controller.spi_send_byte_at_address(0x00, 0x80)
    controller.spi_send_byte_at_address(0x01, 0x00)
    controller.spi_send_byte_at_address(0x02, 0x00)
    controller.spi_send_byte_at_address(0x03, reg3)
    controller.spi_send_byte_at_address(0x04, reg4)

    if not controller.fpga_get_is_loaded("S2175"):
        if verbose:
            print 'Loading FPGA'
        controller.fpga_load_file("S2175")
    elif verbose:
        print 'FPGA already loaded'

    # demo-board specific information needed by the DC1371
    controller.dc1371_set_demo_config(0x28000000)

    if verbose:
        print 'Starting data collect'

    controller.data_start_collect(TOTAL_ADC_SAMPLES, comm.TRIGGER_NONE)

    for i in range(10):
        is_done = controller.data_is_collect_done()
        if is_done:
            break
        sleep(0.2)

    if not is_done:
        raise comm.HardwareError('Data collect timed out (missing clock?)')

    if verbose:
        print 'Data collect done.'

    if verbose:
        print 'Reading data'
    num_bytes, data = controller.data_receive_uint16_values(end=TOTAL_ADC_SAMPLES)
    if verbose:
        print 'Data read done'

# Split data into two channels
    data_ch1 = [data[i] & 0x3FFF for i in range(0, TOTAL_ADC_SAMPLES, 2)]
    data_ch2 = [data[i] & 0x3FFF for i in range(1, TOTAL_ADC_SAMPLES, 2)]

    # write the data to a file
    if write_to_file:
        if verbose:
            print 'Writing data to file'
        with open('data.txt', 'w') as f:
            for i in range(NUM_ADC_SAMPLES):
                f.write(str(data_ch1[i]) + str(data_ch2[i]) + '\n')
    
        print 'File write done.'

    print 'All finished!'

# Plot data if requested
    if plot_data:
        plt.figure(1)
        plt.subplot(211)
        plt.plot(data_ch1)
        plt.title('CH0')
        plt.subplot(212)
        plt.title('CH1')
        plt.plot(data_ch2)
        plt.show()

        adc_amplitude = 16384.0 / 2.0
        
        windowscale = (NUM_ADC_SAMPLES) / sum(np.blackman(NUM_ADC_SAMPLES))
        print("Window scaling factor: " + str(windowscale))
        
        data_ch1 -= np.average(data_ch1)
        windowed_data_ch1 = data_ch1 * np.blackman(NUM_ADC_SAMPLES) * windowscale # Apply Blackman window
        freq_domain_ch1 = np.fft.fft(windowed_data_ch1)/(NUM_ADC_SAMPLES) # FFT
        freq_domain_magnitude_ch1 = np.abs(freq_domain_ch1) # Extract magnitude
        freq_domain_magnitude_db_ch1 = 20 * np.log10(freq_domain_magnitude_ch1/adc_amplitude)
        
        data_ch2 -= np.average(data_ch2)
        windowed_data_ch2 = data_ch2 * np.blackman(NUM_ADC_SAMPLES) * windowscale # Apply Blackman window
        freq_domain_ch2 = np.fft.fft(windowed_data_ch2)/(NUM_ADC_SAMPLES) # FFT
        freq_domain_magnitude_ch2 = np.abs(freq_domain_ch2) # Extract magnitude
        freq_domain_magnitude_db_ch2 = 20 * np.log10(freq_domain_magnitude_ch2/adc_amplitude)

        
        plt.figure(2)
        plt.subplot(211)
        plt.title('CH0 FFT')
        plt.plot(freq_domain_magnitude_db_ch1)
        plt.subplot(212)
        plt.title('CH1 FFT')
        plt.plot(freq_domain_magnitude_db_ch2)
        plt.show()

