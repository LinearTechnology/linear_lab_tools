# -*- coding: utf-8 -*-
"""
    Created by: Noe Quintero
    E-mail: nquintero@linear.com

    Copyright (c) 2015, Linear Technology Corp.(LTC)
    All rights reserved.

    Redistribution and use in source and binary forms, with or without
    modification, are permitted provided that the following conditions are met:

    1. Redistributions of source code must retain the above copyright notice, 
       this list of conditions and the following disclaimer.
    2. Redistributions in binary form must reproduce the above copyright 
       notice, this list of conditions and the following disclaimer in the 
       documentation and/or other materials provided with the distribution.

    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
    AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE 
    IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE 
    ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE 
    LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
    CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF 
    SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS 
    INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN 
    CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
    ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE 
    POSSIBILITY OF SUCH DAMAGE.

    The views and conclusions contained in the software and documentation are 
    those of the authors and should not be interpreted as representing official
    policies, either expressed or implied, of Linear Technology Corp.

    Description:
        The purpose of this module is to excersice the LTC25xx for Seismeic 
        Applications
"""



###############################################################################
# Libraries
###############################################################################

import time
import sys # os, socket, ctypes, struct
import numpy as np
from time import sleep
from matplotlib import pyplot as plt
import DC2390_functions as DC2390
from llt.utils.mem_func_client_2 import MemClient
from llt.utils.sockit_system_functions import *


###############################################################################
# Parameters for running different tests
###############################################################################

SYSTEM_CLOCK_DIVIDER = 99 # 50MHz / 200 = 250 Ksps
NUM_SAMPLES = 2**20
SINC_LEN = 2048
FILTER_TYPE = 1



###############################################################################
# Functions
###############################################################################
def capture_seismic_data(client, filter_type):
    """
        Captures and plots data for the DC2390
        Filter_type options - 0: sinc
                            - 1: ssinc 256
                            - 2: ssinc 1024
                            - 3: ssinc 4096
    """
    # Construct or extract filter coefficients
    if filter_type == 1:
        length = 256
        with open('../../../../common/ltc25xx_filters/ssinc_256.txt') as filter_coeff_file:
            ltc25xx_filter = [float(line) for line in filter_coeff_file]
        # Normalize to unity gain
        sum_ltc25xx_filter = sum(ltc25xx_filter)
        ltc25xx_filter[:] = [x / sum_ltc25xx_filter for x in ltc25xx_filter] 
    elif filter_type == 2:    
        length = 1024
        with open('../../../../common/ltc25xx_filters/ssinc_1024.txt') as filter_coeff_file:
            ltc25xx_filter = [float(line) for line in filter_coeff_file]
        # Normalize to unity gain
        sum_ltc25xx_filter = sum(ltc25xx_filter)
        ltc25xx_filter[:] = [x / sum_ltc25xx_filter for x in ltc25xx_filter]
    elif filter_type == 3:  
        length = 4096
        with open('../../../../common/ltc25xx_filters/ssinc_4096.txt') as filter_coeff_file:
            ltc25xx_filter = [float(line) for line in filter_coeff_file]
        # Normalize to unity gain
        sum_ltc25xx_filter = sum(ltc25xx_filter)
        ltc25xx_filter[:] = [x / sum_ltc25xx_filter for x in ltc25xx_filter]
    else:
        length = SINC_LEN
        ltc25xx_filter = np.ones(SINC_LEN)      # Create the sinc filter coeff
        ltc25xx_filter /= sum(ltc25xx_filter)   # Normalize to unity gain

    # Read the unfiltered nyquist data
    # -------------------------------------------------------------------------
    # Set Mux for raw Nyquist data
    # Set Dac A for SIN and Dac B for LUT
    client.reg_write(DC2390.DATAPATH_CONTROL_BASE,DC2390.DC2390_FIFO_ADCB_NYQ |
                                                  DC2390.DC2390_DAC_B_LUT |
                                                  DC2390.DC2390_DAC_A_NCO_SIN |
                                                  DC2390.DC2390_LUT_ADDR_COUNT |
                                                  DC2390.DC2390_LUT_RUN_ONCE)
    sleep(2.5) # Allow LUT to run through until end...
    # Capture the data
    nyq_data_c = sockit_uns32_to_signed32(sockit_capture(client, NUM_SAMPLES, trigger = 0, timeout = 1.0))
    nyq_data = np.zeros(len(nyq_data_c))
    nyq_data += nyq_data_c
    nyq_data *= (5.0 / 2147483648.0)
    # Remove offset, based on a slice of data points near the end
    avg = np.average(nyq_data[len(nyq_data)-2000:len(nyq_data)-1000])
    nyq_data = nyq_data - avg    

    # Read the LTC25xx filtered data 
    # -------------------------------------------------------------------------
    # Set Mux for filtered data
    # Set Dac A for SIN and Dac B for LUT
    client.reg_write(DC2390.DATAPATH_CONTROL_BASE, DC2390.DC2390_FIFO_ADCB_FIL |
                                                   DC2390.DC2390_DAC_B_LUT |
                                                   DC2390.DC2390_DAC_A_NCO_SIN |
                                                   DC2390.DC2390_LUT_ADDR_COUNT |
                                                   DC2390.DC2390_LUT_RUN_ONCE)
    sleep(0.25)
                                                  
    # Capture the data
    filt_25xx_data_c = sockit_uns32_to_signed32(sockit_capture(client, NUM_SAMPLES/length, trigger = 0, 
                          timeout = 1))
    filt_25xx_data = np.zeros(len(filt_25xx_data_c))
    filt_25xx_data += filt_25xx_data_c
    filt_25xx_data *= (5.0 / 2147483648.0)
    avg = np.average(filt_25xx_data[len(filt_25xx_data)-200:len(filt_25xx_data)-100])
    filt_25xx_data = filt_25xx_data - avg    

    # Apply the digital filter to the raw Nyquist data by convolution
    # -------------------------------------------------------------------------
    convt_time = time.time();
    nyq_filt_data = np.convolve(nyq_data,ltc25xx_filter, mode='valid') # Apply the filter coeff to the 
                                            # nyquist data
    print "The program took", time.time() - convt_time, "sec to run convolution"        
    return nyq_data, nyq_filt_data, filt_25xx_data
    
    
def capture_plot(client, plot, gain, filter_type):
    """
        Captures and plots data for the DC2390
        Filter_type options - 0: sinc
                            - 1: ssinc 256
                            - 2: ssinc 1024
                            - 3: ssinc 4096
    """
    # Construct or extract filter coefficients
    if filter_type == 1:
        length = 256
        with open('../../../../common/ltc25xx_filters/ssinc_256.txt') as filter_coeff_file:
            ltc25xx_filter = [float(line) for line in filter_coeff_file]
        # Normalize to unity gain
        sum_ltc25xx_filter = sum(ltc25xx_filter)
        ltc25xx_filter[:] = [x / sum_ltc25xx_filter for x in ltc25xx_filter] 
    elif filter_type == 2:    
        length = 1024
        with open('../../../../common/ltc25xx_filters/ssinc_1024.txt') as filter_coeff_file:
            ltc25xx_filter = [float(line) for line in filter_coeff_file]
        # Normalize to unity gain
        sum_ltc25xx_filter = sum(ltc25xx_filter)
        ltc25xx_filter[:] = [x / sum_ltc25xx_filter for x in ltc25xx_filter]
    elif filter_type == 3:  
        length = 4096
        with open('../../../../common/ltc25xx_filters/ssinc_4096.txt') as filter_coeff_file:
            ltc25xx_filter = [float(line) for line in filter_coeff_file]
        # Normalize to unity gain
        sum_ltc25xx_filter = sum(ltc25xx_filter)
        ltc25xx_filter[:] = [x / sum_ltc25xx_filter for x in ltc25xx_filter]
    else:
        length = SINC_LEN
        ltc25xx_filter = np.ones(SINC_LEN)      # Create the sinc filter coeff
        ltc25xx_filter /= sum(ltc25xx_filter)   # Normalize to unity gain

    # Read the unfiltered nyquist data
    # -------------------------------------------------------------------------
    # Set Mux for raw Nyquist data
    # Set Dac A for SIN and Dac B for LUT
    client.reg_write(DC2390.DATAPATH_CONTROL_BASE,DC2390.DC2390_FIFO_ADCB_NYQ |
                                                  DC2390.DC2390_DAC_B_LUT |
                                                  DC2390.DC2390_DAC_A_NCO_SIN |
                                                  DC2390.DC2390_LUT_ADDR_COUNT |
                                                  DC2390.DC2390_LUT_RUN_ONCE)
    
    # Capture the data
    data = sockit_uns32_to_signed32(sockit_capture(client, NUM_SAMPLES, trigger = 0, timeout = 1.0))
    avg = np.average(data[len(data)-1002:len(data)-2])
    data -= avg
    data *= gain
    plot.subplot(3, 1, 1)
    plot.title('Raw Nyquist Data')
    plot.xlim([0,NUM_SAMPLES])
    plot.plot(data)

    # Apply the digital filter to the raw Nyquist data by convolution
    # -------------------------------------------------------------------------
    convt_time = time.time();
    data = np.convolve(data,ltc25xx_filter) # Apply the filter coeff to the 
                                            # nyquist data
    print "The program took", time.time() - convt_time, "sec to run convolution"    

    plot.subplot(3, 1, 2)
    plot.title('Nyquist Data convolved with the Digital Filter')
    plot.ylim([-1.5*10**9,2.5*10**9])
    plot.xlim([0,NUM_SAMPLES])
    plot.plot(data)
    
    # Read the LTC25xx filtered data 
    # -------------------------------------------------------------------------
    # Set Mux for filtered data
    # Set Dac A for SIN and Dac B for LUT
    client.reg_write(DC2390.DATAPATH_CONTROL_BASE, DC2390.DC2390_FIFO_ADCB_FIL |
                                                   DC2390.DC2390_DAC_B_LUT |
                                                   DC2390.DC2390_DAC_A_NCO_SIN |
                                                   DC2390.DC2390_LUT_ADDR_COUNT |
                                                   DC2390.DC2390_LUT_RUN_ONCE)
    sleep(1.0) # Let any wiggles in progress die out
    # Capture the data
    data = sockit_uns32_to_signed32(sockit_capture(client, NUM_SAMPLES/length, trigger = 0, 
                          timeout = 1))
    avg = np.average(data[len(data)-6:len(data)-2])
    data = data - avg
    data = data * gain
    
    plot.subplot(3, 1, 3)
    plot.title('Filtered Data')
    plot.ylim([-1.5*10**9,2.5*10**9])
    plot.xlim([0,NUM_SAMPLES/length])
    plot.plot(data)


if __name__ == "__main__":
    
    PREFIX = "run2_120dB"
    WRITE_FILES = False
    
    if FILTER_TYPE == 1:
        filt = DC2390.LTC2500_SSINC_FILT
        df = DC2390.LTC2500_DF_256
    elif FILTER_TYPE == 2:
        filt = DC2390.LTC2500_SSINC_FILT
        df = DC2390.LTC2500_DF_1024
    elif FILTER_TYPE == 3:
        filt = DC2390.LTC2500_SSINC_FILT
        df = DC2390.LTC2500_DF_4096
    else:
        filt = DC2390.LTC2500_SINC_FILT
        df = DC2390.LTC2500_DF_2048

    # Keep track of start time
    start_time = time.time();
    
    # Get the host from the command line argument. Can be numeric or hostname.
    HOST = sys.argv[1] if len(sys.argv) == 2 else '127.0.0.1'
    
    # Connect to the SoC 
    client = MemClient(host=HOST)
    
    # Verify the FPGA bistream
    #--------------------------------------------------------------------------
    #Read FPGA type and revision
    rev_id = client.reg_read(DC2390.REV_ID_BASE)
    type_id = rev_id & 0x0000FFFF
    rev = (rev_id >> 16) & 0x0000FFFF
    
    if (type_id != 0xABCD) or (rev != 0x1238):
        print "Wrong FPGA bitstream on the FPGA"
        print 'FPGA load type ID: %04X' % type_id
        print 'FPGA load revision: %04X' % rev
    else:
        print "Correct bitstream file found !!"
    
    # Initialize the FPGA
    #--------------------------------------------------------------------------
    print("Setting up system parameters.\n");
    
    # Set the LTC695 to 50 MHz
    DC2390.LTC6954_configure(client, 0x04)
    
    # Set the clock divider
#    client.reg_write(DC2390.SYSTEM_CLOCK_BASE, 0xF5000000 | SYSTEM_CLOCK_DIVIDER) # Approx. 400ms sinc period
#    client.reg_write(DC2390.SYSTEM_CLOCK_BASE, 0xFA800000 | SYSTEM_CLOCK_DIVIDER) # Approx. 200ms sinc period
    client.reg_write(DC2390.SYSTEM_CLOCK_BASE, 0xFDFF0000 | SYSTEM_CLOCK_DIVIDER) # Approx. 200ms sinc period
    
    # Set the sample depth
    client.reg_write(DC2390.NUM_SAMPLES_BASE, NUM_SAMPLES)
    
    # Configure the LTC2500
    ltc2500_cfg_led_on  = (((df | filt)<<6) | 
                             0x03 | (DC2390.LTC2500_N_FACTOR << 16))
    ltc2500_cfg_led_off = (((df | filt)<<6) | 
                            (DC2390.LTC2500_N_FACTOR << 16))
    
    client.reg_write(DC2390.LED_BASE, ltc2500_cfg_led_on)
    sleep(0.1)
    client.reg_write(DC2390.LED_BASE, ltc2500_cfg_led_off)
    sleep(0.1)
    
    # Start the application test
    #--------------------------------------------------------------------------
    raw_input("Set the Jumper for -120 dB, then hit enter")
#    capture_plot(client, plt, (100 * 100 * 100)/2, FILTER_TYPE)

    nyq_data_120, nyq_filt_data_120, filt_25xx_data_120 = capture_seismic_data(client, FILTER_TYPE)
    if(WRITE_FILES == True):
        # write the data to a file
        print('Writing nyq_data_120 data to file')
        with open('data/' + PREFIX + 'nyq_data_120.txt', 'w') as f:
            for i, item in enumerate(nyq_data_120):
                f.write(str(item) + '\n') 
        print('Writing nyq_filt_data_120 data to file')
        with open('data/' + PREFIX + 'nyq_filt_data_120.txt', 'w') as f:
            for i, item in enumerate(nyq_filt_data_120):
                f.write(str(item) + '\n')
        print('Writing filt_25xx_data_120 data to file')
        with open('data/' + PREFIX + 'filt_25xx_data_120.txt', 'w') as f:
            for i, item in enumerate(filt_25xx_data_120):
                f.write(str(item) + '\n')
            
            
#    raw_input("Set the Jumper for -80 dB, then hit enter")
#    capture_plot(client, plt, 100 * 100, FILTER_TYPE)
    
#    raw_input("Set the Jumper for -40 dB, then hit enter")
#    capture_plot(client, plt, 100, FILTER_TYPE)
    
    raw_input("Set the Jumper for 0 dB, then hit enter")
#    capture_plot(client, plt, 1, FILTER_TYPE)
    nyq_data_0, nyq_filt_data_0, filt_25xx_data_0 = capture_seismic_data(client, FILTER_TYPE)  
    if(WRITE_FILES == True):
        print('Writing nyq_data_0 data to file')
        with open('data/' + PREFIX + 'nyq_data_0.txt', 'w') as f:
            for i, item in enumerate(nyq_data_0):
                f.write(str(item) + '\n') 
        print('Writing nyq_filt_data_0 data to file')
        with open('data/' + PREFIX + 'nyq_filt_data_0.txt', 'w') as f:
            for i, item in enumerate(nyq_filt_data_0):
                f.write(str(item) + '\n')
        print('Writing filt_25xx_data_0 data to file')
        with open('data/' + PREFIX + 'filt_25xx_data_0.txt', 'w') as f:
            for i, item in enumerate(filt_25xx_data_0):
                f.write(str(item) + '\n')


    # Display the graphs
    
    plt.figure(1)    
    plt.subplot(2, 1, 1)
    plt.title("LTC2378-20 mode seismic capture")
    plt.plot(nyq_data_0)
    plt.subplot(2, 1, 2)
    plt.plot(nyq_data_120)
    
    plt.figure(2)
    plt.subplot(2, 1, 1)
    plt.title("LTC2378-20 mode, post-processed w/ LTC2508 DF256 filter")
    plt.plot(nyq_filt_data_0)
    plt.subplot(2, 1, 2)
    plt.plot(nyq_filt_data_120)

    plt.figure(3)
    plt.subplot(2, 1, 1)
    plt.title("LTC2508, DF256 seismic capture")
    plt.plot(filt_25xx_data_0)
    plt.subplot(2, 1, 2)
    plt.plot(filt_25xx_data_120)    
    
    plt.show()
    
    # For testing purposes, let the LUT run continuously...
    client.reg_write(DC2390.DATAPATH_CONTROL_BASE,DC2390.DC2390_FIFO_ADCB_NYQ |
                                                  DC2390.DC2390_DAC_B_LUT |
                                                  DC2390.DC2390_DAC_A_NCO_SIN |
                                                  DC2390.DC2390_LUT_ADDR_COUNT |
                                                  DC2390.DC2390_LUT_RUN_CONT)        
    
    print "The program took", (time.time() - start_time)/60, "min to run"