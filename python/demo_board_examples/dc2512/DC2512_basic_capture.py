#!/usr/bin/python
# Example application for running tests on the Arrow SoCkit board
# using the LT_soc_framework

# Big update 6/29/2015!!
# Switching to true ring buffer operation using Noe's FPGA code

# 7/23/2015 - All data paths in FPGA design are in place!!
# Splitting out a bunch of stuff into DC2390_functions.py module


import sys #, os, socket, ctypes, struct
sys.path.append("../../")
sys.path.append("../../../python/utils/")
sys.path.append("../../../python/app_examples/ltc2500_family/")
from save_for_pscope import save_for_pscope
import numpy as np
#from subprocess import call
from time import sleep
from matplotlib import pyplot as plt
# Okay, now the big one... this is the module that communicates with the SoCkit
from mem_func_client_2 import MemClient
#from DC2390_functions import *
from sockit_system_functions import *
# Get the host from the command line argument. Can be numeric or hostname.
#HOST = sys.argv.pop() if len(sys.argv) == 2 else '127.0.0.1'
HOST = sys.argv[1] if len(sys.argv) == 2 else '127.0.0.1'


mem_bw_test = False # Set to true to run a ramp test after ADC capture
NUM_SAMPLES = 2**16#65536 #131072 #8192

DEADBEEF = -559038737 # For now, need to re-justify.

ADC_DATA       = 0x00000000
RAMP_DATA  = 0x00000004

CONTROL_LOOP = 0x02
ADC_B_CAPTURE = 0x00
CHANNEL = ADC_B_CAPTURE


print('Starting client')
client = MemClient(host=HOST)
#Read FPGA type and revision
rev_id = client.reg_read(REV_ID_BASE)
type_id = rev_id & 0x0000FFFF
rev = (rev_id >> 16) & 0x0000FFFF
print ('FPGA load type ID: %04X' % type_id)
print ('FPGA load revision: %04X' % rev)


#datapath fields: lut_addr_select, dac_a_select, dac_b_select[1:0], fifo_data_select
#lut addresses: 0=lut_addr_counter, 1=dac_a_data_signed, 2=0x4000, 3=0xC000

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
client.reg_write(LED_BASE, 0x01)
sleep(0.1)
client.reg_write(LED_BASE, 0x00)
sleep(0.1)


# Capture a sine wave
client.reg_write(DATAPATH_CONTROL_BASE, ADC_DATA) # First capture ADC A
data = sockit_uns32_to_signed32(sockit_capture(client, NUM_SAMPLES, trigger = 0, timeout = 2.0))

data_ch0 = np.ndarray(NUM_SAMPLES, dtype=float)

numbits = 18
if(numbits == 18):
    for i in range(0, NUM_SAMPLES):
        data_ch0[i] = (data[i] & 0x0003FFFF)
        if(data_ch0[i] > 2**17):
            data_ch0[i] -= 2**18

if(numbits == 16):
    for i in range(0, NUM_SAMPLES):
        data_ch0[i] = (data[i] & 0x0000FFFF)
        if(data_ch0[i] > 2**15):
            data_ch0[i] -= 2**16

data_nodc0 = data_ch0 #- np.average(data)

#data_nodc *= np.blackman(NUM_SAMPLES)
#fftdata = np.abs(np.fft.fft(data_nodc)) / NUM_SAMPLES
#fftdb = 20*np.log10(fftdata / 2.0**31)
plt.figure(pltnum)
pltnum +=1
plt.plot(data_ch0)
data_for_pscopeA = data_nodc0 / 256.0

#(out_path, num_bits, is_bipolar, num_samples, dc_num, ltc_num, *data):
save_for_pscope("pscope_DC2390.adc",24 ,True, NUM_SAMPLES, "2390", "2500",
                data_for_pscopeA)

if(mem_bw_test == True):
    client.reg_write(DATAPATH_CONTROL_BASE, RAMP_DATA) # Capture a test pattern
    print("Ramp test!")
    errors = sockit_ramp_test(client, 2**21, trigger = 0, timeout = 1.0)
    print("Number of errors: " + str(errors))
    client.reg_write(DATAPATH_CONTROL_BASE, ADC_DATA) # Set datapath back to ADC
