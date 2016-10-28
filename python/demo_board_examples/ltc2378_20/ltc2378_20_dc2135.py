# -*- coding: utf-8 -*-
'''
DC2135 or DC1925 / LTC2378-20 Interface Example

This program demonstrates how to communicate with the LTC2378-20 demo board through Python.

Board setup is described in Demo Manual 1925 or 2135. Follow the procedure in the manual, and
verify operation with the PScope software. Once operation is verified, exit PScope
and run this script.

Tested with Python 2.7, Anaconda distribution available from Continuum Analytics,
http://www.continuum.io/

Demo board documentation:
http://www.linear.com/demo/
http://www.linear.com/product/LTC2378-20#demoboards

LTC2378-20 product page
http://www.linear.com/product/LTC2378-20


REVISION HISTORY
$Revision: 4276 $
$Date: 2015-10-20 10:38:41 -0700 (Tue, 20 Oct 2015) $

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
import ltc_controller_comm as comm

def ltc2378_20_dc2135(num_samples, verbose=False, do_demo=False):
    def vprint(s):
        """Print string only if verbose is on"""
        if verbose:
            print s
            
    if do_demo:
        plot_data = True
        write_to_file = True
    else:
        plot_data = False
        write_to_file = False

    # Print extra information to console
    verbose = True
    # Plot data to screen
    plot_data = True
    #Write data out to a text file
    write_to_file = True
    
    #NUM_ADC_SAMPLES = 64 * 1024
    NUM_ADC_SAMPLES = num_samples
    SAMPLE_BYTES = 4 # for 32-bit reads
    EEPROM_ID_SIZE = 50
    
    # find demo board with correct ID
    device_info = None
    print 'Looking for a DC890 with a DC2135 OR DC1925 demoboard'
    for info in comm.list_controllers(comm.TYPE_DC890):
        with comm.Controller(info) as device:
            eeprom_id = device.eeprom_read_string(EEPROM_ID_SIZE)
            if 'DC2135' in eeprom_id:
                vprint('Found a DC2135 demoboard')
                device_info = info
                break
            if 'DC1925' in eeprom_id:
                vprint('Found a DC1925 demoboard')
                device_info = info
                break
    if device_info is None:
        raise(comm.HardwareError('Could not find a compatible device'))
    # Open communication to the demo board
    with comm.Controller(device_info) as controller:
        if not controller.fpga_get_is_loaded("CMOS"):
            vprint('Loading FPGA')
            controller.fpga_load_file("CMOS")
        else:
            vprint('FPGA already loaded')
        vprint('Starting data collect')
    
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
    
        vprint('Data collect done.')
        controller.dc890_flush()
        vprint('Reading data')
        num_bytes, rawdata = controller.data_receive_uint32_values(end=NUM_ADC_SAMPLES)
        vprint('Data read done')

        data = [0] * (NUM_ADC_SAMPLES)
        for i in range(NUM_ADC_SAMPLES):
            data[i] = rawdata[i] & 0x000FFFFF # Extract lower 20 bits
            if((data[i] > 0x0007FFFF)):       # Work around Python's tendency to not
                data[i] -= 0x00100000         # understand 2's complement
    
        # write the data to a file
        if write_to_file == True:
            vprint('Writing data to file')
            with open('data.txt', 'w') as f:
                for i in range(NUM_ADC_SAMPLES):
                    f.write(str(data[i] & 0xFFFFFFFF) + '\n')
            vprint('File write done.')
        vprint('All finished!')
    
        # Plot data
        if(plot_data == True):
            from matplotlib import pyplot as plt
            import numpy as np
            plt.figure(1)
            plt.plot(data)
            plt.title('Time Domain Samples')
            plt.show()
    
            adc_amplitude = 2.0**20 / 2.0
            
            data_no_dc = data - np.average(data) # Remove DC to avoid leakage when windowing
            
            windowscale = (NUM_ADC_SAMPLES/2) / sum(np.blackman(NUM_ADC_SAMPLES/2))
            print("Window scaling factor: " + str(windowscale))
            
            windowed_data = data_no_dc * np.blackman(NUM_ADC_SAMPLES) * windowscale # Apply Blackman window
            freq_domain = np.fft.fft(windowed_data)/(NUM_ADC_SAMPLES) # FFT
            freq_domain_magnitude = np.abs(freq_domain) # Extract magnitude
            freq_domain_magnitude_db = 20 * np.log10(freq_domain_magnitude/adc_amplitude)
    
            plt.figure(2)
            plt.title('FFT')
            plt.plot(freq_domain_magnitude_db)
            plt.show()
            
        return data

if __name__ == '__main__':
    NUM_SAMPLES = 64 * 1024
    # to use this function in your own code you would typically do
    # data = ltc2378_20_dc2135(num_samples)
    # Valid number of samples are 1024 to 65536 (powers of two)
    testdata = ltc2378_20_dc2135(NUM_SAMPLES, verbose=True, do_demo=True)
    


    
    
    
    