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
        The purpose of this module is to measure the signal chain noise 
        performance.
"""

###############################################################################
# Libraries
###############################################################################

import time
import sys # os, socket, ctypes, struct
import numpy as np
from time import sleep
from matplotlib import pyplot as plt
import llt.utils.DC2390_functions as DC2390
from llt.common.mem_func_client_2 import MemClient

###############################################################################
# Parameters for running test
###############################################################################

AVERAGING_NUMBER = 100
SYS_CLK = 50000000
SYSTEM_CLOCK_DIVIDER = 99 # 50MHz / 100 = 500 Ksps
NUM_SAMPLES = 8192#2**20
GAIN_OF_OPAMP = 1


if __name__ == "__main__": 
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
    client.reg_write(DC2390.SYSTEM_CLOCK_BASE, 0xF5000000 | SYSTEM_CLOCK_DIVIDER)
    
    # Set the sample depth
    client.reg_write(DC2390.NUM_SAMPLES_BASE, NUM_SAMPLES)
    
    # Configure the LTC2500
    ltc2500_cfg_led_on  = (((DC2390.LTC2500_DF_64 | DC2390.LTC2500_SSINC_FILT)<<6) | 0x03 | 
                           (DC2390.LTC2500_N_FACTOR << 16))
    ltc2500_cfg_led_off = (((DC2390.LTC2500_DF_64 | DC2390.LTC2500_SSINC_FILT)<<6) | 
                            (DC2390.LTC2500_N_FACTOR << 16))
    
    client.reg_write(DC2390.LED_BASE, ltc2500_cfg_led_on)
    sleep(0.1)
    client.reg_write(DC2390.LED_BASE, ltc2500_cfg_led_off)
    sleep(0.1)
    
    # Start the application test
    #--------------------------------------------------------------------------
    
    avg_fft = np.zeros(NUM_SAMPLES, dtype = float)
    for x in range(0, AVERAGING_NUMBER):
        # Set Mux for raw Nyquist data
        # Set Dac A for SIN and Dac B for
        client.reg_write(DC2390.DATAPATH_CONTROL_BASE,DC2390.DC2390_FIFO_ADCB_NYQ | 
                         DC2390.DC2390_DAC_B_LUT | DC2390.DC2390_DAC_A_NCO_SIN | 
                         DC2390.DC2390_LUT_ADDR_COUNT | DC2390.DC2390_LUT_RUN_ONCE)
                         
        
        # Capture the data
        data = DC2390.capture(client, NUM_SAMPLES, trigger = 0, timeout = 1.0)
        lsb = 10.0/(2**32-1) 
        data_volts = np.multiply(data , lsb)
        print np.average(data_volts)
        print np.std(data_volts)
        # Convert time domain data to frequncy domain
        fftdata = np.abs(np.fft.fft(data_volts))/len(data_volts)
        
        avg_fft = np.add(avg_fft, fftdata)
    
    avg_fft /= AVERAGING_NUMBER
    
    # Convert to nV/sqrt(Hz)
    
#    lsb =100000
    number_bins = NUM_SAMPLES / 2.0
    sampling_freq = SYS_CLK / (SYSTEM_CLOCK_DIVIDER + 1)
    bin_width = sampling_freq / number_bins
    
#    avg_fft *= lsb
    
    
    avg_fft /= np.sqrt(bin_width)
    
    
    avg_fft[0] = 0 # remove DC info
    
    avg_fft /= GAIN_OF_OPAMP
    plt.semilogx(avg_fft[0:NUM_SAMPLES/2])    
    plt.show()
    
    print "The program took", (time.time() - start_time)/60, "min to run"