# -*- coding: utf-8 -*-
"""
    Created by: Noe Quintero
    E-mail: nquintero@linear.com

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

@author: Noe Quintero
"""
###############################################################################
# Functions
###############################################################################

# Function used to Store data into a file for PScope
def write_1ch_128k_pscope_file(data_vector, filename):
    f = open(filename, "w")
    f.write('Version,115\n')
    f.write('Retainers,0,1,131072,128,6,0.250000000000000,0,1\n')
    f.write('Placement,44,2,3,-1,-1,-1,-1,171,92,1192,816\n')
    f.write('WindMgr,6,2,0\n')
    f.write('Page,0,2\n')
    f.write('Col,3,1\n')
    f.write('Row,2,1\n')
    f.write('Row,3,146\n')
    f.write('Row,5,232\n')
    f.write('Row,1,547\n')
    f.write('Col,2,1452\n')
    f.write('Row,4,1\n')
    f.write('Row,0,319\n')
    f.write('Page,1,2\n')
    f.write('Col,1,1\n')
    f.write('Row,1,1\n')
    f.write('Col,2,1452\n')
    f.write('Row,4,1\n')
    f.write('Row,0,319\n')
    f.write('DemoID,DC2135A,LTC2378-20,0\n')
    f.write('RawData,1,131072,20,-231730,231700,0.250000000000000,-5.242880e+005,5.242880e+005\n')	
    for i in range(0, 131072):
        f.write(str(data_vector[i]))      # str() converts to string
        f.write('\n')
    f.write('End\n')
    f.close()

# Funtion for converting frequency to tunning word for the NCO
def Hz_2_tuning_word(master_clk, tunnig_width, desired_freq):
    return int((float(desired_freq)/master_clk * (2**tunnig_width)))

###############################################################################
# Libraries
###############################################################################
import time
import sys 
import numpy as np
#from subprocess import call
from time import sleep
from matplotlib import pyplot as plt
# Module that communicates with the SoCkit
from mem_func_client import MemClient
from DC2390_functions import *

###############################################################################
# ADC performance test
###############################################################################

# Start time of test
start_time = time.time();

# Get the host
HOST = sys.argv[1] if len(sys.argv) == 2 else '127.0.0.1'

# Set the sps
SYSTEM_CLOCK_DIVIDER = 199
# Set sample depth
NUM_SAMPLES = 131072

# Set the NCO tunning word width
nco_word_width = 32

# The FPGA system clock
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

print("Setting up system parameters.\n");
client.reg_write(SYSTEM_CLOCK_BASE, SYSTEM_CLOCK_DIVIDER)
client.reg_write(NUM_SAMPLES_BASE, NUM_SAMPLES)

LTC6954_configure_default(client)

# Set the NCO to 1KHz
tuning_word = Hz_2_tuning_word(master_clock, nco_word_width, 2000)
client.reg_write(TUNING_WORD_BASE, tuning_word)

# Configure the LTC2500
ltc2500_cfg_led_on  = (((LTC2500_DF_64 | LTC2500_SSINC_FILT)<<6) | 0x03 | 
                       (LTC2500_N_FACTOR << 16))
ltc2500_cfg_led_off = (((LTC2500_DF_64 | LTC2500_SSINC_FILT)<<6) | 
                        (LTC2500_N_FACTOR << 16))

client.reg_write(LED_BASE, ltc2500_cfg_led_on)
sleep(0.1)
client.reg_write(LED_BASE, ltc2500_cfg_led_off)
sleep(0.1)

# ADC A nyquist test noncoherent signal
# -----------------------------------------------------------------------------

# Set Mux for raw Nyquist data
# Set Dac A for SIN and Dac B for LUT
client.reg_write(DATAPATH_CONTROL_BASE, DC2390_FIFO_ADCA_NYQ |
                 DC2390_DAC_B_LUT | DC2390_DAC_A_NCO_SIN | 
                 DC2390_LUT_ADDR_COUNT | DC2390_LUT_RUN_CONT)

# Capture the data
data = capture(client, NUM_SAMPLES, trigger = 0, timeout = 1.0)

# Convert the 32 bits data to 20 bits
for x in range(0, len(data)):
        data[x] = data[x]/(2**12)

# Plot the time domain data
plt.figure(1)
plt.title('Nyquist ADC A')
plt.plot(data)

# Convert time domain data to frequncy domain
fftdata = np.abs(np.fft.fft(data))
fftdb = 20*np.log10(fftdata / np.max(fftdata))

# Plot the FFT 
plt.figure(2)
plt.plot(fftdb)

# Store data to pscope ADC file
write_1ch_128k_pscope_file(data, 'adc_test_nc.adc')

# Find the bin with the peak
peak_bin = np.argmax(fftdb[1:NUM_SAMPLES/2])

# bin_width = Fs / N
bin_width = float(master_clock/(SYSTEM_CLOCK_DIVIDER + 1)) / (NUM_SAMPLES)
print '  bin width = ' + str(bin_width)

# Calculate the frequency bin
freq_bin = bin_width * peak_bin
print '  freq Bin = ' + str(freq_bin)

# ADC A nyquist test coherent signal
# -----------------------------------------------------------------------------

# Set the DAC to the closest bin
tuning_word = Hz_2_tuning_word(master_clock, nco_word_width, freq_bin)
print 'NCO: ' + str(tuning_word) 
client.reg_write(TUNING_WORD_BASE, tuning_word)

# Wait for user to injection lock the input
input('Lock the oscilator, then enter a char ')

# Capture the data
data = capture(client, NUM_SAMPLES, trigger = 0, timeout = 1.0)

# Convert the 32 bits data to 20 bits
for x in range(0, len(data)):
        data[x] = data[x]/(2**12)

# Store data to pscope ADC file
write_1ch_128k_pscope_file(data, 'adc_test_c.adc')

# Convert time domain data to frequncy domain
fftdata = np.abs(np.fft.fft(data))
fftdb = 20*np.log10(fftdata / np.max(fftdata))

# Plot the FFT with the noncoherent FFT
plt.figure(2)
plt.plot(fftdb)

# Show the plots
plt.show()

print "My program took", time.time() - start_time, "to run"