# -*- coding: utf-8 -*-
'''
DC1975 / LTC2270 Interface Example

This program demonstrates how to communicate with the LTC2270 demo board through Python.
Examples are provided for reading data captured by the ADC, or test data generated by
the ADC.

Board setup is described in Demo Manual 1975. Follow the procedure in this manual, and
verify operation with the PScope software. Once operation is verified, exit PScope
and run this script.

Tested with Python 2.7, Anaconda distribution available from Continuum Analytics,
http://www.continuum.io/

Demo board documentation:
http://www.linear.com/demo/1369
http://www.linear.com/product/LTC2261#demoboards

LTC2000 product page
http://www.linear.com/product/LTC2261


REVISION HISTORY
$Revision:  $
$Date:  $

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

# set test_data_reg to one of these constants
DATA_REAL = 0x00
DATA_ALL_ZEROS = 0x08
DATA_ALL_ONES = 0x18
DATA_CHECKERBOARD = 0x28
DATA_ALTERNATING = 0x38
#test_data_reg = DATA_ALTERNATING
test_data_reg = DATA_REAL

NUM_ADC_SAMPLES = 64 * 1024
SAMPLE_BYTES = 2
EEPROM_ID_SIZE = 50

# find demo board with correct ID
device_info = None
print 'Looking for a DC890 with a DC1975A-A demoboard'
for info in comm.list_controllers(comm.TYPE_DC890):
    with comm.Controller(info) as device:
        eeprom_id = device.eeprom_read_string(EEPROM_ID_SIZE)
        if 'DC1975' in eeprom_id:
            if verbose:
                print 'Found a DC1975A-A demoboard'
            device_info = info
            break
if device_info is None:
    raise(comm.HardwareError('Could not find a compatible device'))
# Open communication to the demo board
with comm.Controller(device_info) as controller:

    controller.dc890_gpio_set_byte(0xF8)
    controller.dc890_gpio_spi_set_bits(3, 0, 1)

    if verbose:
        print 'Configuring SPI registers'
        if test_data_reg == DATA_REAL:
            print 'Set to read real data'
        else:
            print 'Set to generate test data'
    controller.spi_send_byte_at_address(0x00, 0x80)
    controller.spi_send_byte_at_address(0x01, 0x00)
    controller.spi_send_byte_at_address(0x02, 0x00)
    controller.spi_send_byte_at_address(0x03, 0x70)
    controller.spi_send_byte_at_address(0x04, test_data_reg)
    if not controller.fpga_get_is_loaded("CMOS"):
        if verbose:
            print 'Loading FPGA'
        controller.fpga_load_file("CMOS")
    elif verbose:
        print 'FPGA already loaded'

    if verbose:
        print 'Starting data collect'

    controller.data_set_high_byte_first()

    controller.data_set_characteristics(True, SAMPLE_BYTES, True)
    controller.data_start_collect(NUM_ADC_SAMPLES, comm.TRIGGER_NONE)

    for i in range(10):
        is_done = controller.data_is_collect_done()
        if is_done:
            break
        sleep(0.2)

    if not is_done:
        raise comm.HardwareError('Data collect timed out (missing clock?)')

    if verbose:
        print 'Data collect done.'

    controller.dc890_flush()

    if verbose:
        print 'Reading data'
    num_bytes, data = controller.data_receive_uint16_values(end=NUM_ADC_SAMPLES)
    if verbose:
        print 'Data read done'

# Split data into two channels
    data_ch1 = [0] * (NUM_ADC_SAMPLES/2)
    data_ch2 = [0] * (NUM_ADC_SAMPLES/2)
    
    for i in range(NUM_ADC_SAMPLES/2):
        data_ch1[i] = data[2*i]& 0xFFFF
        data_ch2[i] = data[2*i + 1]& 0xFFFF

    # write the data to a file
    if write_to_file == True:
        if verbose:
            print 'Writing data to file'
        with open('data.txt', 'w') as f:
            for i in range(NUM_ADC_SAMPLES/2):
                # remember we have an extra fake channel so we write every other sample
                f.write(str(data_ch1[i] & 0xFFFF) + str(data_ch2[i] & 0xFFFF) + '\n')
    
        print 'File write done.'

    print 'All finished!'

# Plot data if not running pattern check
    if(plot_data == True):
        plt.figure(1)
        plt.subplot(211)
        plt.plot(data_ch1)
        plt.title('CH0')
        plt.subplot(212)
        plt.title('CH1')
        plt.plot(data_ch2)
        plt.show()

        adc_amplitude = 65536.0 / 2.0
        
        windowscale = (NUM_ADC_SAMPLES/2) / sum(np.blackman(NUM_ADC_SAMPLES/2))
        print("Window scaling factor: " + str(windowscale))
        
        windowed_data_ch1 = data_ch1 * np.blackman(NUM_ADC_SAMPLES/2) * windowscale # Apply Blackman window
        freq_domain_ch1 = np.fft.fft(windowed_data_ch1)/(NUM_ADC_SAMPLES/2) # FFT
        freq_domain_magnitude_ch1 = np.abs(freq_domain_ch1) # Extract magnitude
        freq_domain_magnitude_db_ch1 = 10 * np.log(freq_domain_magnitude_ch1/adc_amplitude)

        windowed_data_ch2 = data_ch2 * np.blackman(NUM_ADC_SAMPLES/2) * windowscale # Apply Blackman window
        freq_domain_ch2 = np.fft.fft(windowed_data_ch2)/(NUM_ADC_SAMPLES/2) # FFT
        freq_domain_magnitude_ch2 = np.abs(freq_domain_ch2) # Extract magnitude
        freq_domain_magnitude_db_ch2 = 10 * np.log10(freq_domain_magnitude_ch2/adc_amplitude)

        
        plt.figure(2)
        plt.subplot(211)
        plt.title('CH0 FFT')
        plt.plot(freq_domain_magnitude_db_ch1)
        plt.subplot(212)
        plt.title('CH1 FFT')
        plt.plot(freq_domain_magnitude_db_ch2)
        plt.show()
