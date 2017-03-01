#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Example application for running tests on the Arrow SoCkit board
using the LT_soc_framework


Tested with Python 2.7, Anaconda distribution available from Continuum Analytics,
http://www.continuum.io/


REVISION HISTORY
$Revision: 6460 $
$Date: 2017-01-30 14:26:33 -0800 (Mon, 30 Jan 2017) $

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

import sys , ctypes
import numpy as np
from time import sleep
from matplotlib import pyplot as plt

# Save data in PScope compatible format
from llt.utils.save_for_pscope import save_for_pscope
# this is the module that communicates with the SoCkit
from llt.common.mem_func_client_2 import MemClient
# Functions and defines specific to this board
from llt.utils.DC2390_functions import *
# Functions and defines specific to sockit system
from llt.utils.sockit_system_functions import *

# Get the host from the command line argument. Can be numeric or hostname.
HOST = sys.argv[1] if len(sys.argv) >= 2 else '127.0.0.1'

# Enable / disable simple memory bandwidth test using internal digital
# pattern generator
mem_bw_test = False

# Initial Parameters for PID example
PID_KP = 0x0010
PID_KI = 0x0040
PID_KD = 0x0050

PULSE_LOW = 20000
PULSE_HIGH = 100000
PULSE_VAL = 25000

# Set to true to write a downward ramp to DAC lookup table
test_LUT_write = True

# Timing / data record length
SYSTEM_CLOCK_DIVIDER = 199 # 50MHz / (n+1), set to 99 for 500ksps, 199 for 250ksps, etc.
LUT_NCO_DIVIDER = 0xFFFD # 0xFFFF for divide by 1
NUM_SAMPLES = 8192 #131072 #8192

DEADBEEF = -559038737 # For checking againtst constant test pattern

N = 7 #Number of samples to average (LTC2380-24)

vfs = 10.0 # Full-scale voltage, VREF * 2 for LTC25xx family

nco_word_width = 32 # A property of the NCO in the FPGA design
master_clock = 50000000 # Relies on proper configuration of LTC6954 divider
bin_number = 50 # Number of cycles over the time record for sine signal
sample_rate = master_clock / (SYSTEM_CLOCK_DIVIDER + 1) # 250ksps for 50M clock, 200 clocks per sample
cycles_per_sample = float(bin_number) / float(NUM_SAMPLES)
cycles_per_dac_sample = cycles_per_sample / (SYSTEM_CLOCK_DIVIDER + 1)
tuning_word = int(cycles_per_dac_sample * 2**nco_word_width)
print("Tuning Word:" + str(tuning_word))

print('Starting client')
client = MemClient(host=HOST)
#First thing's First!! Configure clocks...
LTC6954_configure(client, 0x04)
#Read FPGA type and revision
type_rev_check(client, 0xABCD, 0x1246)

print("Setting up system parameters.\n");
client.reg_write(SYSTEM_CLOCK_BASE, SYSTEM_CLOCK_DIVIDER)
client.reg_write(SYSTEM_CLOCK_BASE, (LUT_NCO_DIVIDER << 16 | SYSTEM_CLOCK_DIVIDER))
client.reg_write(NUM_SAMPLES_BASE, NUM_SAMPLES)
client.reg_write(PID_KP_BASE, PID_KP)
client.reg_write(PID_KI_BASE, PID_KI)
client.reg_write(PID_KD_BASE, PID_KD)
client.reg_write(PULSE_LOW_BASE, PULSE_LOW)
client.reg_write(PULSE_HIGH_BASE, PULSE_HIGH)
client.reg_write(PULSE_VAL_BASE, PULSE_VAL)


#datapath fields: lut_addr_select, dac_a_select, dac_b_select[1:0], fifo_data_select
#lut addresses: 0=lut_addr_counter, 1=dac_a_data_signed, 2=0x4000, 3=0xC000
# DAC A: 
#	.data0x ( nco_sin_out ),
#	.data1x ( pid_output ),
#	.data2x ( 16'h4000 ),
#	.data3x ( 16'hC000 ),
# DAC B:
#	.data0x ( nco_cos_out ),
#	.data1x ( lut_output ),
#	.data2x ( 16'hC000 ),
#	.data3x ( 16'h4000 ),
# FIFO Data:
# 0 = ADC A
# 1 = ADC B
# 2 = Counters
# 3 = DEADBEEF

datapath_word_sines = 0x00000000
datapath_word_pid = 0x00000100
datapath_word_lut_run_once = 0x00008011
datapath_word_lut_continuous = 0x00000011 #counter as LUT address, run once
datapath_word_dist_correction = 0x00001011

pltnum = 1
# Bit fields for control register
# std_ctrl_wire = {26'bz, lut_write_enable, ltc6954_sync , gpo1, gpo0, en_trig, start };

print ('Okay, now lets blink some lights and run some tests!!')

# print ('run # %d ' % i)
client.reg_write(LED_BASE, (N << 16) | 0x0F) # LED_BASE register also contains 
sleep(0.1)
client.reg_write(LED_BASE, (N << 16) | 0x00) # LTC2500 filter configuration.
sleep(0.1)

client.reg_write(TUNING_WORD_BASE, tuning_word) # Set NCO frequency

# Capture a sine wave
client.reg_write(DATAPATH_CONTROL_BASE, datapath_word_sines) # Set data multiplexers
# Capture data - LTC2500 Nyquist data first bit is overrange, followed by MSB
data = sockit_ltc2500_to_signed32(sockit_capture(client, NUM_SAMPLES, trigger = TRIG_NOW, timeout = 1.0))
rms = np.std(data) # Useful for checking noise levels, signal amplitudes.
print("Standard Deviation: " + str(rms))
data_nodc = data - np.average(data)       # Strip out DC content, required before windowing
data_nodc *= np.blackman(NUM_SAMPLES)     # Apply Blackman window
fftdata = np.abs(np.fft.fft(data_nodc)) / NUM_SAMPLES
fftdb = 20*np.log10(fftdata / 2.0**31)
plt.figure(pltnum)
pltnum +=1
plt.subplot(2, 1, 1)
plt.title("Basic Sinewave test")
plt.plot(data)
plt.subplot(2, 1, 2)
plt.plot(fftdb)



data_ndarray = np.array(data)
data_volts = data_ndarray * (vfs / 2.0**32.0) # Convert to voltage
datarms = np.std(data_volts)
datap_p = np.max(data_volts) - np.min(data_volts)
print("RMS voltage: " + str(datarms))
print("Peak-to-Peak voltage: " + str(datap_p))
#(out_path, num_bits, is_bipolar, num_samples, dc_num, ltc_num, *data):
data_for_pscope = data_nodc / 256.0
save_for_pscope("pscope_DC2390.adc",24 ,True, NUM_SAMPLES, "2390", "2500", data_for_pscope)

# Run through lookup table continuously (Arbitrary waveform generator mode)
client.reg_write(DATAPATH_CONTROL_BASE, datapath_word_lut_continuous)
data = sockit_ltc2500_to_signed32(sockit_capture(client, NUM_SAMPLES, trigger = TRIG_NOW, timeout = 0.0))
fftdata = np.abs(np.fft.fft(data)) / len(data)
fftdb = 20*np.log10(fftdata / 2.0**31)
plt.figure(pltnum)
pltnum +=1
plt.subplot(2, 1, 1)
plt.title("Continuous arb. waveform")
plt.plot(data)
plt.subplot(2, 1, 2)
plt.plot(fftdb)

# Run through lookup table once (Arbitrary pulse mode)
client.reg_write(DATAPATH_CONTROL_BASE, datapath_word_lut_run_once)
data = sockit_ltc2500_to_signed32(sockit_capture(client, NUM_SAMPLES, trigger = TRIG_NOW, timeout = 0.0))
fftdata = np.abs(np.fft.fft(data)) / len(data)
fftdb = 20*np.log10(fftdata / 2.0**31)
plt.figure(pltnum)
pltnum +=1
plt.subplot(2, 1, 1)
plt.title("Single-shot arb. waveform")
plt.plot(data)
plt.subplot(2, 1, 2)
plt.plot(fftdb)

# Use DAC A data as lookup table address (Distortion correction mode)
client.reg_write(DATAPATH_CONTROL_BASE, datapath_word_dist_correction)
data = sockit_ltc2500_to_signed32(sockit_capture(client, NUM_SAMPLES, trigger = TRIG_NOW, timeout = 0.0))
plt.figure(pltnum)
pltnum +=1
plt.title("NCO as address to LUT")
plt.plot(data)

#PID controller
client.reg_write(DATAPATH_CONTROL_BASE, datapath_word_pid)
data = sockit_ltc2500_to_signed32(sockit_capture(client, NUM_SAMPLES, trigger = TRIG_NOW, timeout = 0.0))
plt.figure(pltnum)
plt.title("PID controller")
plt.plot(data)

# Change PID parameters, then run again
PID_KP = 0x0010
PID_KI = 0x0005
PID_KD = 0x0005
client.reg_write(PID_KP_BASE, PID_KP)
client.reg_write(PID_KI_BASE, PID_KI)
client.reg_write(PID_KD_BASE, PID_KD)

client.reg_write(DATAPATH_CONTROL_BASE, datapath_word_pid)
data = sockit_ltc2500_to_signed32(sockit_capture(client, NUM_SAMPLES, trigger = TRIG_NOW, timeout = 0.0))
plt.figure(pltnum)
pltnum +=1
plt.plot(data)

plt.show()

# Leave DAC set to arbitrary waveform generator
client.reg_write(DATAPATH_CONTROL_BASE, datapath_word_lut_continuous)


re_read_registers = False

if re_read_registers == True:
    print ('\nReading register block:')
    block = client.reg_read_block(REV_ID_BASE, 22)
    data_reg = block
    for i in range(0, 22):
        print (register_list[i] + ': %08X'  % data_reg[i])


# Okay, now let's try writing to the DAC lookup table remotely!
if(test_LUT_write == True):
    cDataType = ctypes.c_uint * 65536
    cData     = cDataType()
    print("Writing downward ramp to LUT!")
    for i in range(0, 65536): # Reverse ramp...
        cData[i] = (i << 16 | (65535 - i))
    
    client.reg_write(DATAPATH_CONTROL_BASE, datapath_word_lut_continuous) 
    
    client.reg_write(CONTROL_BASE, 0x00000020) # Enable writing from blob side...
    client.reg_write_LUT(LUT_ADDR_DATA_BASE, 65535, cData)
    client.reg_write(CONTROL_BASE, 0x00000000) # Disable writing from blob side...
    print("Done writing to LUT! Hope it went okay!")

if(mem_bw_test == True):
    client.reg_write(DATAPATH_CONTROL_BASE, DC2390_FIFO_UP_DOWN_COUNT) # Capture a test pattern
    
    print("Ramp test at original divisor of " + str(SYSTEM_CLOCK_DIVIDER))
    errors = ramp_test(client, 2**21, trigger = TRIG_NOW, timeout = 1.0)
    print("Number of errors: " + str(errors))
    
    client.reg_write(SYSTEM_CLOCK_BASE, (LUT_NCO_DIVIDER << 16 | 4)) # 50M / 5 = 10MSPS
    print("Ramp test at divisor of 5 (10Msps)")
    errors = ramp_test(client, 2**21, trigger = TRIG_NOW, timeout = 1.0)
    print("Number of errors: " + str(errors))
    
    client.reg_write(SYSTEM_CLOCK_BASE, (LUT_NCO_DIVIDER << 16 | 1)) # 50M / 2 = 25MSPS
    print("Ramp test at original divisor of 2 (25Msps)")
    errors = ramp_test(client, 2**21, trigger = TRIG_NOW, timeout = 1.0)
    print("Number of errors: " + str(errors))
    # Set back to original divisor
    client.reg_write(SYSTEM_CLOCK_BASE, (LUT_NCO_DIVIDER << 16 | SYSTEM_CLOCK_DIVIDER)) # 50M / 5 = 10MSPS

choice = 'n'
#choice = raw_input('Shutdown: y/n? ')
if(choice == 'y'):
    print 'Shutting down ...'
#    time.sleep(30)
    client.shutdown()

print("Test done! Enter \"client.shutdown()\" to shut down SoCkit board.")
