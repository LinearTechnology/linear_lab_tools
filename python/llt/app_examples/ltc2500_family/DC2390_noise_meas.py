# -*- coding: utf-8 -*-
"""
    Capture data for a thorough analysis of signal chain noise.

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
#from subprocess import call
from time import sleep
import time
# Okay, now the big one... this is the module that communicates with the SoCkit
from llt.common.mem_func_client_2 import MemClient
from llt.utils.DC2390_functions import *
from LTC2758 import *



###############################################################################
# Global Constants
###############################################################################

SYSTEM_CLOCK_DIVIDER = 99 # 50MHz / 100 = 500 Ksps
LUT_NCO_DIVIDER = 0xFFFF
nco_word_width = 32

# Set sample depth
NUM_FLT_SAMPLES = 2**12
NUM_NYQ_SAMPLES = 2**20
master_clock = 50000000

DF_LIST = [LTC2500_DF_4, LTC2500_DF_8, LTC2500_DF_16, LTC2500_DF_32, LTC2500_DF_64,
           LTC2500_DF_128, LTC2500_DF_256, LTC2500_DF_512,   LTC2500_DF_1024, LTC2500_DF_2048,
           LTC2500_DF_4096, LTC2500_DF_8192, LTC2500_DF_16384] # 13 downsample factors to test
DF_TXT = ["4", "8", "16", "32", "64", "128", "256", "512", "1024", "2048", "4096", "8192", "16384"]
DF_VALS = [4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384]

GAIN = "18"


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
client.reg_write(NUM_SAMPLES_BASE, NUM_NYQ_SAMPLES)

LTC6954_configure(client)


LTC2758_write(client, LTC2748_DAC_A | 
                      LTC2758_WRITE_CODE_UPDATE_ALL, 2**17) #Set DACs to half scale on 0-5V range

LTC2758_write(client, LTC2748_DAC_B | 
                      LTC2758_WRITE_CODE_UPDATE_ALL, 2**17)

###########################
# Set Mux for Nyquist data
###########################
client.reg_write(DATAPATH_CONTROL_BASE, DC2390_FIFO_ADCA_NYQ |  # DC2390_FIFO_ADCB_FIL or DC2390_FIFO_ADCB_NYQ
                 DC2390_DAC_B_CONS_HC000 | DC2390_DAC_A_PULSE_VAL | 
                 DC2390_LUT_ADDR_COUNT | DC2390_LUT_RUN_ONCE)

ltc2500_cfg_led_on  = ((LTC2500_DF_4 | LTC2500_SINC_FILT)<<6) | 0x03 | (LTC2500_N_FACTOR << 16)
ltc2500_cfg_led_off = ((LTC2500_DF_4 | LTC2500_SINC_FILT)<<6) | (LTC2500_N_FACTOR << 16)
client.reg_write(LED_BASE, ltc2500_cfg_led_on)
sleep(0.1)
client.reg_write(LED_BASE, ltc2500_cfg_led_off)
sleep(0.1)

# timeout = (SYSTEM_CLOCK_DIVIDER) / master_clock
for run in range(0, 16):
    data = capture(client, NUM_NYQ_SAMPLES, timeout = 4.0) # Enough time to capture a megapoint...
    print("Capturing nyquist data, run " + str(run))
    with open("DC2390_noise_meas\Nyq_gain_" + GAIN + "_run_" + str(run) + ".csv" , "w") as myfile:
        for i in range(len(data)):
            myfile.write(str(data[i]) + '\n')

############################
# Set Mux for Filtered data
############################
client.reg_write(DATAPATH_CONTROL_BASE, DC2390_FIFO_ADCA_FIL |  # DC2390_FIFO_ADCB_FIL or DC2390_FIFO_ADCB_NYQ
                 DC2390_DAC_B_CONS_HC000 | DC2390_DAC_A_PULSE_VAL | 
                 DC2390_LUT_ADDR_COUNT | DC2390_LUT_RUN_ONCE)
                 
numdfs = 13
for df in range(0, numdfs):
    t_o = 1000000.0 * float(DF_VALS[df] * (SYSTEM_CLOCK_DIVIDER + 1)) / float(master_clock)
    print("Calculated timeout: " + str(t_o))
    ltc2500_cfg_led_on  = ((DF_LIST[df] | LTC2500_SINC_FILT)<<6) | 0x03 | (LTC2500_N_FACTOR << 16)
    ltc2500_cfg_led_off = ((DF_LIST[df] | LTC2500_SINC_FILT)<<6) | (LTC2500_N_FACTOR << 16)
    client.reg_write(LED_BASE, ltc2500_cfg_led_on)
    sleep(0.1)
    client.reg_write(LED_BASE, ltc2500_cfg_led_off)
    sleep(0.1)
    
    # timeout = (SYSTEM_CLOCK_DIVIDER) / master_clock
    data = capture(client, NUM_FLT_SAMPLES, timeout = (t_o + 10.0))  # Timeout, with some buffer...
    
    with open("DC2390_noise_meas\Filt_gain_" + GAIN + "_df_" + DF_TXT[df] +  ".csv" , "w") as myfile:
        for i in range(len(data)):
            myfile.write(str(data[i]) + '\n')
                 