# -*- coding: utf-8 -*-
"""
    Description:
        The purpose of this module is to perform a sweep of frequencies to
        trace the filter shape of any of the LTC2500 filters, plotted along
        with the calculated response from the filter coefficients.



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


"""

###############################################################################
# Libraries
###############################################################################

import sys #, os, socket, ctypes, struct
import numpy as np
#from subprocess import call
from time import sleep
from matplotlib import pyplot as plt
# Okay, now the big one... this is the module that communicates with the SoCkit
from llt.common.mem_func_client_2 import MemClient ## Updated to client_2
#from llt.utils.DC2390_functions import *
from llt.utils.DC2390_functions import * # Leaving here as a commend during restructuring
from llt.utils.sockit_system_functions import *
from llt.utils.linear_lab_tools_functions import *
import time


###############################################################################
# Script Parameters
# Change the parameters to run different scenarios.  
###############################################################################

#ADC 'U1' and 'U2' are the choices. UN-comment selected ADC
ADC = 'U1'
#ADC = 'U2'

# Select downsample factor - DF4 to DF16384 (powers of 2)
# 4, 8, 16, 32 correspond to the LTC2512
# 256, 1024, 4096, 16384 correspond to the LTC2508

DF_info = DF256

# UN-comment one to Select filter type.
#FT_info = FTSINC1
#FT_info = FTSINC2
#FT_info = FTSINC3
FT_info = FTSINC4
#FT_info = FTSSINC
#FT_info = FT_FLAT

# Set sample depth, for each frequency that is tested
NUM_SAMPLES = 8192
# Number of frequencies to plot
NUM_FREQS = 64

bins_per_point = 2

filename = "../../../../common/ltc25xx_filters/" + FT_info.FT_txt + "_" + DF_info.DF_txt + ".txt"
filelength = linecount(filename)
filt = np.ndarray(filelength, dtype=float)
print ("reading " + str(filelength) + " coefficients from file " + filename)
# Read in coefficients from files
with open(filename, 'r') as infile:
    for i in range(0, filelength):
        instring = infile.readline()
        filt[i] = float(instring)
print('done reading filter coefficients!')

filt /= sum(filt) # Normalize to unity gain
filt_resp_full = freqz_by_fft_numpoints(filt, 2 ** 20)

filt_resp_full_db = 20 * np.log10(abs(filt_resp_full))

filt_resp = downsample(filt_resp_full, 128*bins_per_point)
filt_resp_db = 20 * np.log10(abs(filt_resp))


# Plot out first bin time domain data, count bits for this point. Useful
# for hardware / software / Verilog debugging
DEBUG = False

if ADC == 'U1':
    mux_port = DC2390_FIFO_ADCA_FIL
else:
    mux_port = DC2390_FIFO_ADCB_FIL
    
master_clock = 50000000 # 50MHz, standard setting for DC2390
SYSTEM_CLOCK_DIVIDER = 99 # Divide by 100, 500ksps Nyquist rate



###############################################################################
# Global Constants
###############################################################################
dac_div = 128 # DAC sample rate divisor, from master_clock
LUT_NCO_DIVIDER = 0x10000 - dac_div # NCO updates every cycle
nco_word_width = 32

###############################################################################
# Main program
###############################################################################

print "\n/////////////////////////////////////////////"
print "//   LTC2500 Trace Filter Shape Demo         //"
print "///////////////////////////////////////////////"

start_time = time.time();

# Get the host from the command line argument. Can be numeric or hostname.
HOST = sys.argv[1] if len(sys.argv) == 2 else '127.0.0.1'

print '\nStarting client'
client = MemClient(host=HOST)

# Check FPGA type and revision
type_rev_check(client, 0xABCD, 0x1246)

# Set the LTC6954 to output 50 MHz
# Divisors of 5, 6 will give CLK frequencies of 40MHz, 33.3MHz. This may be
# useful for debugging FPGA timing.
LTC6954_configure(client, 4 )
client.reg_write(LED_BASE, (LTC2500_DF_64 | LTC2500_SSCIN_FLAT_FILT)) # Initial LTC2500 SYNC


print("Setting up system parameters.\n");
client.reg_write(SYSTEM_CLOCK_BASE, ((LUT_NCO_DIVIDER << 16) | SYSTEM_CLOCK_DIVIDER))
client.reg_write(NUM_SAMPLES_BASE, NUM_SAMPLES)


# Set Mux for filtered data
# Set Dac A for SIN and Dac B for LUT
client.reg_write(DATAPATH_CONTROL_BASE, mux_port | 
                 DC2390_DAC_B_NCO_COS | DC2390_DAC_A_NCO_SIN | 
                 DC2390_LUT_ADDR_COUNT | DC2390_LUT_RUN_CONT)
# Set up filter type / DF and blink a light
ltc2500_cfg_led_on  = (((DF_info.DF_ctrl_bits | FT_info.FT_ctrl_bits)) | 0x03) # | (LTC2500_N_FACTOR << 16)
ltc2500_cfg_led_off = (((DF_info.DF_ctrl_bits | FT_info.FT_ctrl_bits))       )# | (LTC2500_N_FACTOR << 16)

client.reg_write(LED_BASE, ltc2500_cfg_led_on)
sleep(0.1)
client.reg_write(LED_BASE, ltc2500_cfg_led_off)
sleep(0.1)


# Sweep the DAC freq and measure the filter respose
filt_shape_measured = []
filt_shape_ideal = []
freq_bin = []

fig1 = plt.figure(1)
plt.subplot(1, 1, 1)

plt.title('LTC25xx Filter Shape')
plt.xlabel("Bin")
plt.ylabel("dB")
plt.xlim([0,NUM_FREQS])
mng = plt.get_current_fig_manager()
#mng.window.showMaximized()
plt.ion() # Go interactive...

sample_rate = master_clock / (SYSTEM_CLOCK_DIVIDER + 1) # 250ksps for 50M clock, 200 clocks per sample
dac_sample_rate = master_clock / dac_div

haxis = np.linspace(0.0, sample_rate, NUM_SAMPLES) # Horizontal axis, Hz

lw = 4


for x in range(0, NUM_FREQS):
    print("Data point: " + str(x))
    # Calculate the NCO to coherent bin
    bin_number = (x + 1) * bins_per_point
    
    
    cycles_per_sample = float(bin_number) / float(NUM_SAMPLES)
    hz_per_bin = sample_rate / NUM_SAMPLES
    sine_frequency = bin_number * hz_per_bin
    
    cycles_per_dac_sample = cycles_per_sample / (SYSTEM_CLOCK_DIVIDER + 1)
    tuning_word = int(cycles_per_dac_sample * 2**nco_word_width)
    tuning_word = int(2**nco_word_width * sine_frequency / dac_sample_rate)
    print("Tuning Word:" + str(tuning_word))
    print("Bin Number:" + str(bin_number) + " / " + str(NUM_SAMPLES/2))
    freq_bin.append(bin_number)
    
    # Set the NCO
    client.reg_write(TUNING_WORD_BASE, tuning_word)
    
    # Capture the data
#    data = capture(client, NUM_SAMPLES, timeout = 1.0) # Updating to new capture...
    sleep(0.5)
    data_pre = sockit_capture(client, NUM_SAMPLES, trigger = TRIG_NOW, timeout = 1.0)
    data = sockit_uns32_to_signed32(data_pre)
    
    # Remove DC content
    data -= np.average(data)
    
    # Apply windowing to data    
#    data = data * np.blackman(NUM_SAMPLES)    
    
    # Convert time domain data to frequncy domain
    fftdata = np.abs(np.fft.fft(data))
    rms = np.std(data)
    
    if x == 0:
        max_amp = np.amax(fftdata)
        max_rms = np.std(data)
    
    # Convert to dB
    fftdb = 20*np.log10(fftdata / max_amp)
    rmsdb = 20*np.log10(rms / max_rms)

# Choose one method
#    amplitude = np.amax(fftdb)
    amplitude = rmsdb
    
    print("Amplitude of filtered data: " + str(amplitude))
    filt_shape_measured.append(amplitude)
    filt_shape_ideal.append(filt_resp_full_db[(x+1) * 256 ])

    plt.cla()
    plt.title('LTC25xx Filter Shape')
    plt.xlabel("Bin")
    plt.ylabel("dB")

    plt.plot(haxis[1:x+2], filt_shape_measured, marker='o',markersize=15, linestyle='None', color="red")
    plt.plot(haxis[1:x+2], filt_shape_ideal, marker='.', linestyle='-', linewidth=lw, color="blue")
    plt.show()
    plt.axis([0, haxis[x+2], -100, 10])
    plt.pause(0.0001) # Small delay







    # Extra debug info - for first bin, plot time domain data and bit counter    
    if(x == 1 and DEBUG == True):
    # Plot time domain data
        plt.figure(2) # Plot for time domain data
        plt.plot(data)
        plt.show()        
        
        bitmask = 1
        for bit in range (0, 32):
            bitcount = 0
            for point in range(0, NUM_SAMPLES):
                if((data_pre[point] & bitmask) == bitmask):
                    bitcount += 1
            print("Number of 1s in bit " + str(bit) + ": " + str(bitcount))
            bitmask *= 2 # Test next bit...


# Plot the results
#plt.figure(1)
#plt.plot(freq_bin,filt_shape_measured)
#plt.title('LTC2512 Filter Shape')
#plt.xlabel("Bin")
#plt.ylabel("dB")
#plt.show()

print "The program took", (time.time() - start_time)/60, "min to run"
