# -*- coding: utf-8 -*-
'''

HACKED TO HANDLE TWO BOARDS!!!

DC19996 / LTC2323 Interface Example

This program demonstrates how to communicate with the LTC2323 demo board through Python.
Examples are provided for reading data captured by the ADC, or test data generated by
the ADC.

Board setup is described in Demo Manual 1975. Follow the procedure in this manual, and
verify operation with the PScope software. Once operation is verified, exit PScope
and run this script.

Tested with Python 2.7, Anaconda distribution available from Continuum Analytics,
http://www.continuum.io/

Demo board documentation:
http://www.linear.com/demo/1996
http://www.linear.com/product/LTC2323#demoboards

LTC2323 product page
http://www.linear.com/product/LTC2323


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

# Print extra information to console
verbose = True
# Plot data to screen
plot_data = True
#Write data out to a text file
write_to_file = True


def ltc2323_dc1996(NUM_SAMPLES, verbose=True, do_demo=True, trigger=False, timeout=1):

    def vprint(s):
        """Print string only if verbose is on"""
        if verbose:
            print s

    NUM_ADC_SAMPLES = NUM_SAMPLES * 2 # Total number of samples to collect
    SAMPLE_BYTES = 2
    EEPROM_ID_SIZE = 50
    
#    # find demo board with correct ID
#    device_info = None
#    print 'Looking for a DC890 with a DC1996-X demoboard'
#    for info in comm.list_controllers(comm.TYPE_DC890):
#        with comm.Controller(info) as device:
#            eeprom_id = device.eeprom_read_string(EEPROM_ID_SIZE)
#            if 'DC1996' in eeprom_id:
#                if verbose:
#                    print 'Found a DC1996-X demoboard'
#                device_info = info
#                break
#
#    if device_info is None:
#        raise(comm.HardwareError('Could not find a compatible device'))

    num_devices = 0
    descriptions = ['DC890 FastDAACS CNTLR']

    print "Devices found:"
    device_info = [None] * 2

    for info in comm.list_controllers(comm.TYPE_DC890):
        if info.get_description() in descriptions:
            device_info[num_devices] = info
            print device_info
            num_devices = num_devices + 1
            #break
            
    print "No: of devices = ", num_devices
    		
    if device_info is None:
        raise(comm.HardwareError('Could not find a compatible device'))
    
    print "Device Info 1: ", device_info[0]
    print "Device Info 2: ", device_info[1]

    controller0 = comm.Controller(device_info[0])
    controller1 = comm.Controller(device_info[1])


    # Open communication to the demo board
    vprint("Configuring board 0...")
#    with comm.Controller(device_info[0]) as controller:
    if not controller0.fpga_get_is_loaded("CMOS"):
        if verbose:
            print 'Loading FPGA'
        controller0.fpga_load_file("CMOS")
    elif verbose:
        print 'FPGA already loaded'

    if verbose:
        print 'Starting data collect'

    controller0.data_set_high_byte_first()
    controller0.data_set_characteristics(True, SAMPLE_BYTES, True)

    
    
    vprint("Configuring board 1...")
#    with comm.Controller(device_info[1]) as controller:
    if not controller1.fpga_get_is_loaded("CMOS"):
        if verbose:
            print 'Loading FPGA'
        controller1.fpga_load_file("CMOS")
    elif verbose:
        print 'FPGA already loaded'

    if verbose:
        print 'Starting data collect'

    controller1.data_set_high_byte_first()
    controller1.data_set_characteristics(True, SAMPLE_BYTES, True)
    
    if(trigger == True):
        print("Starting capture when trigger received...")
        controller0.data_start_collect(NUM_ADC_SAMPLES, comm.TRIGGER_START_POSITIVE_EDGE)
        controller1.data_start_collect(NUM_ADC_SAMPLES, comm.TRIGGER_START_POSITIVE_EDGE)
        for i in range(timeout):
            is_done = controller0.data_is_collect_done()
            if is_done:
                break
            sleep(1.0)
            print("Waiting up to " + str(timeout) + " seconds... " + str(i))
        if is_done:
            print("Board 0 done!")
        sleep(1.0) # Wait one extra second for board 1 to complete...
        is_done = controller1.data_is_collect_done()
        if is_done:
            print("Board 1 done!")
    else:
        print("No trigger, capturing immediately...")            
        controller0.data_start_collect(NUM_ADC_SAMPLES, comm.TRIGGER_NONE)
        controller1.data_start_collect(NUM_ADC_SAMPLES, comm.TRIGGER_NONE)
        for i in range(10): # First check board 0
            is_done = controller0.data_is_collect_done()
            if is_done:
                break
            sleep(0.2)
        for i in range(10): # Board 1 should be the same, but just in case...
            is_done = controller1.data_is_collect_done()
            if is_done:
                break
            sleep(0.2)

    if not is_done:
        controller0.data_cancel_collect()
        controller1.data_cancel_collect()
        raise comm.HardwareError('Data collect timed out (missing clock?)')
    
    vprint("Reading out data from board 0...")



    controller0.dc890_flush()

    if verbose:
        print 'Reading data'
    num_bytes, data0 = controller0.data_receive_uint16_values(end=NUM_ADC_SAMPLES)
    if verbose:
        print 'Data read done'


    controller1.dc890_flush()

    if verbose:
        print 'Reading data'
    num_bytes, data1 = controller1.data_receive_uint16_values(end=NUM_ADC_SAMPLES)
    if verbose:
        print 'Data read done'         
            
    controller0.close()
    controller1.close()
    
# Split data into two channels
    data_bd0_ch1 = [0] * (NUM_ADC_SAMPLES/2)
    data_bd0_ch2 = [0] * (NUM_ADC_SAMPLES/2)
    data_bd1_ch1 = [0] * (NUM_ADC_SAMPLES/2)
    data_bd1_ch2 = [0] * (NUM_ADC_SAMPLES/2)
    
    for i in range(NUM_ADC_SAMPLES/2):
        data_bd0_ch1[i] = data0[2*i]& 0xFFFF
        data_bd0_ch2[i] = data0[2*i + 1]& 0xFFFF
        data_bd1_ch1[i] = data1[2*i]& 0xFFFF
        data_bd1_ch2[i] = data1[2*i + 1]& 0xFFFF
        if(data_bd0_ch1[i] > 0x8000):
            data_bd0_ch1[i] -= 0x10000
        if(data_bd0_ch2[i] > 0x8000):
            data_bd0_ch2[i] -= 0x10000
        if(data_bd1_ch1[i] > 0x8000):
            data_bd1_ch1[i] -= 0x10000
        if(data_bd1_ch2[i] > 0x8000):
            data_bd1_ch2[i] -= 0x10000

    # write the data to a file
    if write_to_file == True:
        if verbose:
            print 'Writing data to file'
        with open('data.txt', 'w') as f:
            for i in range(NUM_ADC_SAMPLES/2):
                f.write(str(data_bd0_ch1[i]) + "," + str(data_bd0_ch2[i]) + ',' +
                        str(data_bd1_ch1[i]) + "," + str(data_bd1_ch2[i])+ '\n')
    
        vprint('File write done.')

    vprint('All finished!')

# Plot data if not running pattern check
    if(plot_data == True):
        from matplotlib import pyplot as plt
        
        plt.figure(1)
        plt.subplot(411)
        plt.plot(data_bd0_ch1)
        plt.title('Board 0, CH1')
        plt.subplot(412)
        plt.plot(data_bd0_ch2)
        plt.title('Board 0, CH2')
        plt.subplot(413)
        plt.plot(data_bd1_ch1)
        plt.title('Board 1, CH1')
        plt.subplot(414)
        plt.plot(data_bd1_ch2)
        plt.title('Board 1, CH2')
        plt.show()
#        import numpy as np
#        adc_amplitude = 65536.0 / 2.0
#        
#        data_ch1 -= np.average(data_ch1)
#        data_ch2 -= np.average(data_ch2)
#        
#        windowscale = (NUM_ADC_SAMPLES/2) / sum(np.blackman(NUM_ADC_SAMPLES/2))
#        print("Window scaling factor: " + str(windowscale))
#        
#        windowed_data_ch1 = data_ch1 * np.blackman(NUM_ADC_SAMPLES/2) * windowscale # Apply Blackman window
#        freq_domain_ch1 = np.fft.fft(windowed_data_ch1)/(NUM_ADC_SAMPLES/2) # FFT
#        freq_domain_magnitude_ch1 = np.abs(freq_domain_ch1) # Extract magnitude
#        freq_domain_magnitude_db_ch1 = 20 * np.log10(freq_domain_magnitude_ch1/adc_amplitude)
#
#        windowed_data_ch2 = data_ch2 * np.blackman(NUM_ADC_SAMPLES/2) * windowscale # Apply Blackman window
#        freq_domain_ch2 = np.fft.fft(windowed_data_ch2)/(NUM_ADC_SAMPLES/2) # FFT
#        freq_domain_magnitude_ch2 = np.abs(freq_domain_ch2) # Extract magnitude
#        freq_domain_magnitude_db_ch2 = 20 * np.log10(freq_domain_magnitude_ch2/adc_amplitude)
#
#        
#        plt.figure(2)
#        plt.subplot(211)
#        plt.title('CH0 FFT')
#        plt.plot(freq_domain_magnitude_db_ch1)
#        plt.subplot(212)
#        plt.title('CH1 FFT')
#        plt.plot(freq_domain_magnitude_db_ch2)
#        plt.show()
            
    return data_bd0_ch1, data_bd0_ch2, data_bd1_ch1, data_bd1_ch2

if __name__ == '__main__':

# Data record length, PER CHANNEL

#    NUM_SAMPLES = 1 * 1024
#    NUM_SAMPLES = 2 * 1024
#    NUM_SAMPLES = 4 * 1024
#    NUM_SAMPLES = 8 * 1024
#    NUM_SAMPLES = 16 * 1024
#    NUM_SAMPLES = 32 * 1024
    NUM_SAMPLES = 64 * 1024


    
    # to use this function in your own code you would typically do
    # data_ch1, data_ch2 = ltc2323_dc1996(NUM_SAMPLES, verbose=False, do_demo=False)
    # Valid number of samples are 1024 to 65536 (powers of two)
    data_bd0_ch1, data_bd0_ch2, data_bd0_ch1, data_bd0_ch2 = ltc2323_dc1996(NUM_SAMPLES,
                            verbose=True, do_demo=True, trigger=True, timeout=15)
#
