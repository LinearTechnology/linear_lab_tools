#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
DC2512 Basic Capture routines. DC2512 adapts certain DC718-compatible ADC
demo boards to the Arrow SoCkit FPGA board. This script assumes
FPGA load type ID: 0001 is loaded into the FPGA.



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

"""

import sys
from llt.utils.save_for_pscope import save_for_pscope
import numpy as np
import math
from time import sleep
import time
from matplotlib import pyplot as plt
# Okay, now the big one... this is the module that communicates with the SoCkit
from llt.common.mem_func_client_2 import MemClient
#from DC2390_functions import *
from llt.utils.sockit_system_functions import *
# Get the host from the command line argument. Can be numeric or hostname.
HOST = sys.argv[1] if len(sys.argv) == 2 else '127.0.0.1'

save_pscope_data = False
grab_filtered_data = False
mem_bw_test = False # Set to true to run a ramp test after ADC capture
mem_bw_test_depth = 64 * 2**20
bit_counter = False


numbits = 18 # Tested with LTC2386 / DC2290
#NUM_SAMPLES = 16 * 2**20#65536 #131072 #8192
NUM_SAMPLES = 2**20 #1 megasamples

# For BIG captures, downsample time-domain data before plotting
# and only show NUM_SAMPLES / downsample_factor bins of the FFT.
#downsample_factor = 64
downsample_factor = 1

# MUX selection
ADC_DATA       = 0x00000000
FILTERED_ADC_DATA = 0x00000001
RAMP_DATA  = 0x00000004

# A function to return every df'th element of an array
def downsample(array, df):
    outarray = []
    for i in range(len(array)/df):
        outarray.append(array[i*df])
    return outarray
    
start_time = time.time();
print('Starting client')
client = MemClient(host=HOST)
#Read FPGA type and revision
rev_id = client.reg_read(REV_ID_BASE)
type_id = rev_id & 0x0000FFFF
rev = (rev_id >> 16) & 0x0000FFFF
print ('FPGA load type ID: %04X' % type_id)
print ('FPGA load revision: %04X' % rev)
if type_id != 0x0001:
    print("FPGA type is NOT 0x0001! Make sure you know what you're doing!")

#datapath fields: lut_addr_select, dac_a_select, dac_b_select[1:0], fifo_data_select
#lut addresses: 0=lut_addr_counter, 1=dac_a_data_signed, 2=0x4000, 3=0xC000

# FIFO Data:
# 0 = ADC data
# 1 = Filtered ADC data 
# 2 = Counters
# 3 = DEADBEEF


print ('Okay, now lets blink some lights and run some tests!!')

client.reg_write(LED_BASE, 0x01)
sleep(0.1)
client.reg_write(LED_BASE, 0x00)
sleep(0.1)


# Capture data!

xfer_start_time = time.time()

if(grab_filtered_data == True):
    client.reg_write(DATAPATH_CONTROL_BASE, FILTERED_ADC_DATA) # set MUX to filtered data
    client.reg_write(CIC_RATE_BASE, 64) # Set rate change factor (decimation factor)
    data = sockit_uns32_to_signed32(sockit_capture(client, NUM_SAMPLES, trigger = 0, timeout = 2.0))

else:
    client.reg_write(DATAPATH_CONTROL_BASE, ADC_DATA)
    data = sockit_uns32_to_signed32(sockit_capture(client, NUM_SAMPLES, trigger = 0, timeout = 2.0))

xfer_time = time.time() - xfer_start_time
print("Capture / xfer time: " + str(xfer_time) + " Seconds...")

if(grab_filtered_data == False):
    # We're capguring 32-bit wide samples, only 18 of which are connected to the DC2512 header.
    # Mask data appropriately according to ADC resolution.
    # Note that filtered is LEFT justified, so it doesn't need fixing.
    if(numbits == 18):
        for i in range(0, NUM_SAMPLES):
            data[i] = (data[i] & 0x0003FFFF)
            if(data[i] > 2**17):
                data[i] -= 2**18
    
    if(numbits == 16):
        for i in range(0, NUM_SAMPLES):
            data[i] = (data[i] & 0x0000FFFF)
            if(data[i] > 2**15):
                data[i] -= 2**16
    
    if(numbits == 12):
        for i in range(0, NUM_SAMPLES):
            data[i] = (data[i] & 0x00000FFF)
            if(data[i] > 2**11):
                data[i] -= 2**12

# Simple test to make sure no bits are shorted, either to Vcc, ground, or
# to adjacent bits.
# A full-scale sinewave input should give roughly NUM_SAMPLES/2 1s
# for each bit count. Be suspicious if any bits have zero 1s, NUM_SAMPLES 1s,
# or if adjacent bits have exactly the same number of 1s.
if(bit_counter == True): 
    bitmask = 1
    for bit in range (0, numbits):
        bitcount = 0
        for point in range(0, NUM_SAMPLES):
            if((data[point] & bitmask) == bitmask):
                bitcount += 1
        print("Number of 1s in bit " + str(bit) + ": " + str(bitcount))
        bitmask *= 2 # Test next bit...

# Create a shorter dataset for plotting
timeplot_data = downsample(data, downsample_factor)





adc_amplitude = 2.0**(numbits-1)

data_no_dc = data - np.average(data) # Remove DC to avoid leakage when windowing

# Compute window function
normalization = 1.968888        
a0 = 0.35875
a1 = 0.48829
a2 = 0.14128
a3 = 0.01168

wind = [0 for x in range(NUM_SAMPLES)]
for i in range(NUM_SAMPLES):
    
    t1 = i / (float(NUM_SAMPLES) - 1.0)
    t2 = 2 * t1
    t3 = 3 * t1
    t1 -= int(t1)
    t2 -= int(t2)
    t3 -= int(t3)
    
    wind[i] = a0 - \
              a1*math.cos(2*math.pi*t1) + \
              a2*math.cos(2*math.pi*t2) - \
              a3*math.cos(2*math.pi*t3)
    
    wind[i] *= normalization;


windowed_data = data_no_dc * wind# Apply Blackman window
freq_domain = np.fft.fft(windowed_data)/(NUM_SAMPLES) # FFT
freq_domain = freq_domain[0:NUM_SAMPLES/2+1]
freq_domain_magnitude = np.abs(freq_domain) # Extract magnitude
freq_domain_magnitude[1:NUM_SAMPLES/2] *= 2 
freq_domain_magnitude_db = 20 * np.log10(freq_domain_magnitude/adc_amplitude)



#data_nodc *= np.blackman(NUM_SAMPLES)
#fftdata = np.abs(np.fft.fft(data_nodc)) / NUM_SAMPLES
#fftdb = 20*np.log10(fftdata / 2.0**31)
plt.figure(1)
if(downsample_factor == 1):
    plt.title("Time Record")
else:
    plt.title("Time Record, downsampled by a factor of " + str(downsample_factor))
plt.plot(timeplot_data)
plt.figure(2)
if(downsample_factor == 1):
    plt.title("FFT")
else:
    plt.title("FFT, first " + str(NUM_SAMPLES / (2*downsample_factor)) + " bins")
plt.plot(freq_domain_magnitude_db[0:len(freq_domain_magnitude_db)/downsample_factor])

if(save_pscope_data == True):
    save_for_pscope("pscope_DC2390.adc",24 ,True, NUM_SAMPLES, "2390", "2500",
                    data)
                




if(mem_bw_test == True):
    client.reg_write(DATAPATH_CONTROL_BASE, RAMP_DATA) # Capture a test pattern
    print("Ramp test!")
    errors = sockit_ramp_test(client, mem_bw_test_depth, trigger = 0, timeout = 1.0)
    print("Number of errors: " + str(errors))
    client.reg_write(DATAPATH_CONTROL_BASE, ADC_DATA) # Set datapath back to ADC
    
run_time = time.time() - start_time
print("Run time: " + str(run_time) + " Seconds...")
