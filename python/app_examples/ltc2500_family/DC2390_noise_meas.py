# -*- coding: utf-8 -*-
"""
    Created by: Noe Quintero
    E-mail: nquintero@linear.com

    REVISION HISTORY
    $Revision: 2583 $
    $Date: 2014-06-27 17:21:46 -0700 (Fri, 27 Jun 2014) $
    
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
        The purpose of this module is to perform a sweep of frequencies to
        trace the filter shape of the LTC2512.
"""

###############################################################################
# Libraries
###############################################################################

import sys #, os, socket, ctypes, struct
sys.path.append("../../")
sys.path.append("../../utils/")
import numpy as np
#from subprocess import call
from time import sleep
from matplotlib import pyplot as plt
# Okay, now the big one... this is the module that communicates with the SoCkit
from mem_func_client import MemClient
from DC2390_functions import *
import time


###############################################################################
# Global Constants
###############################################################################

SYSTEM_CLOCK_DIVIDER = 99
LUT_NCO_DIVIDER = 0xFFFF
nco_word_width = 32

# Set sample depth
NUM_SAMPLES = 2**15
master_clock = 50000000


###############################################################################
# Main program
###############################################################################

# Get the host from the command line argument. Can be numeric or hostname.
HOST = sys.argv[1] if len(sys.argv) == 2 else '127.0.0.1'

print '\nStarting client'
client = MemClient(host=HOST)

#Read FPGA type and revision
rev_id = client.reg_read(REV_ID_BASE)
type_id = rev_id & 0x0000FFFF
rev = (rev_id >> 16) & 0x0000FFFF
print 'FPGA load type ID: %04X' % type_id
print 'FPGA load revision: %04X' % rev

start_time = time.time();

print("Setting up system parameters.\n");
client.reg_write(SYSTEM_CLOCK_BASE, ((LUT_NCO_DIVIDER << 16) | SYSTEM_CLOCK_DIVIDER))
client.reg_write(NUM_SAMPLES_BASE, NUM_SAMPLES)

LTC6954_configure_default(client)

# Set Mux for filtered data
# Set Dac A for SIN and Dac B for LUT
client.reg_write(DATAPATH_CONTROL_BASE, DC2390_FIFO_ADCB_FIL | 
                 DC2390_DAC_B_CONS_HC000 | DC2390_DAC_A_PULSE_VAL | 
                 DC2390_LUT_ADDR_COUNT | DC2390_LUT_RUN_ONCE)

ltc2500_cfg_led_on  = ((LTC2500_DF_16384 | LTC2500_SINC_FILT)<<6) | 0x03 | (LTC2500_N_FACTOR << 16)
ltc2500_cfg_led_off = ((LTC2500_DF_16384 | LTC2500_SINC_FILT)<<6) | (LTC2500_N_FACTOR << 16)
client.reg_write(LED_BASE, ltc2500_cfg_led_on)
sleep(0.1)
client.reg_write(LED_BASE, ltc2500_cfg_led_off)
sleep(0.1)


data = capture(client, NUM_SAMPLES, timeout = 30.0)

# Apply windowing to data    
#data = data * np.blackman(NUM_SAMPLES)    

# Convert time domain data to frequncy domain
fftdata = np.abs(np.fft.fft(data)) / len(data)
fftdb = 20*np.log10(fftdata / 2.0**31)
#
plt.plot(fftdb)
#

with open("Filt_gain_18_df_16384.csv" , "w") as myfile:
    for i in range(len(data)):
        myfile.write(str(data[i]) + '\n')

