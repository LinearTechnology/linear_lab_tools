#!/usr/bin/python
# Example application for running tests on the Arrow SoCkit board
# using the LT_soc_framework

# Big update 6/29/2015!!
# Switching to true ring buffer operation using Noe's FPGA code

# 7/23/2015 - All data paths in FPGA design are in place!!
# Splitting out a bunch of stuff into DC2390_functions.py module


import sys #, os, socket, ctypes, struct
sys.path.append("../../")
sys.path.append("../../utils/")
from save_for_pscope import save_for_pscope
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


# Parameters for PID example
PID_KP = 0x0010
PID_KI = 0x0040
PID_KD = 0x0050

PULSE_LOW = 20000
PULSE_HIGH = 100000
PULSE_VAL = 25000

FOS_TAU = 0x8000
FOS_GAIN = 0x0002
FOS_CLOCK = 4

SYSTEM_CLOCK_DIVIDER = 199
LUT_NCO_DIVIDER = 0xFFFF # 0xFFFF for divide by 1
NUM_SAMPLES = 65536 #131072 #8192

DEADBEEF = -559038737 # For now, need to re-justify.

CONTROL_LOOP = 0x02
ADC_B_CAPTURE = 0x00
CHANNEL = ADC_B_CAPTURE

N = 7 #Number of samples to average (LTC2380-24)

nco_word_width = 32
master_clock = 50000000
bin_number = 23 # Number of cycles over the time record
sample_rate = master_clock / (SYSTEM_CLOCK_DIVIDER + 1) # 250ksps for 50M clock, 200 clocks per sample
cycles_per_sample = float(bin_number) / float(NUM_SAMPLES)
cycles_per_dac_sample = cycles_per_sample / (SYSTEM_CLOCK_DIVIDER + 1)
tuning_word = int(cycles_per_dac_sample * 2**nco_word_width)
print("Tuning Word:" + str(tuning_word))


print('Starting client')
client = MemClient(host=HOST)
#First thing's First!! Configure clocks...
LTC6954_configure_default(client)
#Read FPGA type and revision
rev_id = client.reg_read(REV_ID_BASE)
type_id = rev_id & 0x0000FFFF
rev = (rev_id >> 16) & 0x0000FFFF
print ('FPGA load type ID: %04X' % type_id)
print ('FPGA load revision: %04X' % rev)

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

LTC6954_configure_default(client)

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
print ('First test - sweep a couple of sinewaves on ADC B')

# print ('run # %d ' % i)
client.reg_write(LED_BASE, (N << 16) | 0x0F) #Was 234
sleep(0.1)
client.reg_write(LED_BASE, (N << 16) | 0x00) #Was 234
sleep(0.1)


client.reg_write(TUNING_WORD_BASE, tuning_word) # Sweep NCO!!!
# Capture a sine wave

#client.reg_write(DATAPATH_CONTROL_BASE, DC2390_FIFO_UP_DOWN_COUNT) # Capture a test pattern
client.reg_write(DATAPATH_CONTROL_BASE, DC2390_FIFO_ADCA_NYQ) # First capture ADC A
data = capture(client, NUM_SAMPLES, trigger = 0, timeout = 2.0)

data_ch0 = np.ndarray(NUM_SAMPLES, dtype=float)
data_ch1 = np.ndarray(NUM_SAMPLES, dtype=float)
for i in range(0, NUM_SAMPLES):
    data_ch0[i] = data[i] & 0x0000FFFF
    data_ch1[i] = (data[i] & 0xFFFF0000) >> 16
    


data_nodc0 = data_ch0 #- np.average(data)
#data_nodc *= np.blackman(NUM_SAMPLES)
#fftdata = np.abs(np.fft.fft(data_nodc)) / NUM_SAMPLES
#fftdb = 20*np.log10(fftdata / 2.0**31)
plt.figure(pltnum)
pltnum +=1
plt.subplot(2, 1, 1)
plt.plot(data_ch0)
plt.subplot(2, 1, 2)
plt.plot(data_ch1)

data_for_pscopeA = data_nodc / 256.0

# Split out other channel here...

data_for_pscopeB = data_nodc / 256.0

#(out_path, num_bits, is_bipolar, num_samples, dc_num, ltc_num, *data):
data_for_pscope = data_nodc / 256.0
save_for_pscope("pscope_DC2390.adc",24 ,True, NUM_SAMPLES, "2390", "2500",
                data_for_pscopeA, data_for_pscopeB)



## Okay, here goes!! Let's try to write into the LUT:
#print("Writing out to LUT!")
#client.reg_write(CONTROL_BASE, 0x00000020); # Enable writing from blob side...
#for i in range(0, 65536):
#    client.reg_write(LUT_ADDR_DATA_BASE, (i << 16 | i))
#client.reg_write(CONTROL_BASE, 0x00000000); # Disable writing from blob side...
#print("Done writing to LUT! Hope it went okay!")



