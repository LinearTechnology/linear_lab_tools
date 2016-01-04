# -*- coding: utf-8 -*-
"""
Created on Thu Aug 27 11:31:13 2015

@author: noe_q
"""

def Hz_2_tuning_word(master_clk, tunnig_width, desired_freq):
    return int((float(desired_freq)/master_clk * (2**tunnig_width)))
import time
import sys 
import numpy as np
#from subprocess import call
from time import sleep
from matplotlib import pyplot as plt
# Okay, now the big one... this is the module that communicates with the SoCkit
from mem_func_client import MemClient
from DC2390_functions import *
# Get the host from the command line argument. Can be numeric or hostname.
#HOST = sys.argv.pop() if len(sys.argv) == 2 else '127.0.0.1'
HOST = sys.argv[1] if len(sys.argv) == 2 else '127.0.0.1'

SYSTEM_CLOCK_DIVIDER = 199
LUT_NCO_DIVIDER = 0xFFFF
NUM_SAMPLES = 8192

nco_word_width = 32

# Set sample depth
NUM_SAMPLES = 4096 

master_clock = 50000000

print '\nStarting client'
client = MemClient(host=HOST)
#Read FPGA type and revision
rev_id = client.reg_read(REV_ID_BASE)
type_id = rev_id & 0x0000FFFF
rev = (rev_id >> 16) & 0x0000FFFF
print 'FPGA load type ID: %04X' % type_id
print 'FPGA load revision: %04X' % rev
freq = []
gain = []


fs = master_clock / (SYSTEM_CLOCK_DIVIDER + 1) # 250ksps for 50M clock, 200 clocks per sample

start_time = time.time();
print("Setting up system parameters.\n");
client.reg_write(SYSTEM_CLOCK_BASE, (LUT_NCO_DIVIDER << 16 | SYSTEM_CLOCK_DIVIDER))
client.reg_write(NUM_SAMPLES_BASE, NUM_SAMPLES)

LTC6954_configure(client, 0x0A)

# Set Mux for filtered data
# Set Dac A for SIN and Dac B for LUT
client.reg_write(DATAPATH_CONTROL_BASE, DC2390_FIFO_ADCA_FIL | 
                 DC2390_DAC_B_NCO_COS | DC2390_DAC_A_NCO_SIN | 
                 DC2390_LUT_ADDR_COUNT | DC2390_LUT_RUN_CONT)

filter_shape = []
freq = []
for x in range(0, 100):
    tuning_word = Hz_2_tuning_word(master_clock, nco_word_width, 10*(x+1))
    freq.append(10*(x+1))
    print "Tuning Word:" + str(tuning_word)    
    client.reg_write(TUNING_WORD_BASE, tuning_word)
    
    ltc2500_cfg_led_on  = ((LTC2500_DF_128 | LTC2500_SSCIN_FLAT_FILT)<<6) | 0x03 | (LTC2500_N_FACTOR << 16)
    ltc2500_cfg_led_off = ((LTC2500_DF_128 | LTC2500_SSCIN_FLAT_FILT)<<6) | (LTC2500_N_FACTOR << 16)
    client.reg_write(LED_BASE, ltc2500_cfg_led_on)
    sleep(0.1)
    client.reg_write(LED_BASE, ltc2500_cfg_led_off)
    sleep(0.1)
     
    data = capture(client, NUM_SAMPLES, trigger = 0, timeout = 10.0)
    data = data * np.blackman(NUM_SAMPLES)    
    
    # Convert time domain data to frequncy domain
    fftdata = np.abs(np.fft.fft(data))
    if x == 0:
        max_amp = np.max(fftdata)
    fftdb = 20*np.log10(fftdata / max_amp)
    
    filter_shape.append(np.amax(fftdb[5:NUM_SAMPLES/2-1]))


plt.plot(freq,filter_shape)
#plt.title('Filer Shape')
plt.show()

print "My program took", (time.time() - start_time)/60, "min to run"
