#!/usr/bin/python
# Example application for running tests on the Arrow SoCkit board
# using the LT_soc_framework

import os, sys, socket, ctypes, struct
from subprocess import call
from time import sleep
from matplotlib import pyplot as plt
import numpy as np
# Okay, now the big one... this is the module that communicates with the SoCkit
from mem_func_client import MemClient
# Get the host from the command line argument. Can be numeric or hostname.
#HOST = sys.argv.pop() if len(sys.argv) == 2 else '127.0.0.1'
HOST = sys.argv[1] if len(sys.argv) == 2 else '127.0.0.1'

# Map out your registers here. These correspond directly to base addresses
# in the LTQSys_blob. Read and write values to these addresses, and signals in
# your design wiggle accordingly.
#NEW REGISTER MAP!! (after remapping to generic port names)
#control register offsets
EXPANDER_CTRL_OFFSET = 0x00
REV_ID_OFFSET = 0x10
START_OFFSET = 0x20
DATA_READY_OFFSET = 0x30
LED_OFFSET = 0x40
NUM_SAMPLES_OFFSET = 0x50
PID_KP_OFFSET = 0x60
PID_KI_OFFSET = 0x70
PID_KD_OFFSET = 0x80
PULSE_LOW_OFFSET = 0x90
PULSE_HIGH_OFFSET = 0xA0
PULSE_VAL_OFFSET = 0xB0
SYSTEM_CLOCK_OFFSET = 0xC0
FOS_TAU_OFFSET = 0xD0
FOS_GAIN_OFFSET = 0xE0
TUNING_WORD_OFFSET = 0xF0
#FOS_CLOCK_OFFSET = 0x50 #Hardcoded to 4 now...

# Parameters for PID example
PID_KP = 0x0030
PID_KI = 0x0040
PID_KD = 0x0030

PULSE_LOW = 2000
PULSE_HIGH = 10000
PULSE_VAL = 25000

FOS_TAU = 0x8000
FOS_GAIN = 0x0002
FOS_CLOCK = 4

SYSTEM_CLOCK = 200
NUM_SAMPLES = 32768 #8192


CONTROL_LOOP = 0x02
ADC_B_CAPTURE = 0x00
CHANNEL = ADC_B_CAPTURE

WASHERCLAMP = 0x04
MOTOR = 0x08

osr = 128
sinc1=np.ones(osr) # Dividing by 4 such that the OSR is the number of taps
                  # in the SINC4 filter.

i=0

print('Starting client')
client = MemClient(host=HOST)
#Read FPGA type and revision
rev_id = client.reg_read(REV_ID_OFFSET)
type_id = rev_id & 0x0000FFFF
rev = (rev_id >> 16) & 0x0000FFFF
print ('FPGA load type ID: %04X' % type_id)
print ('FPGA load revision: %04X' % rev)

print("Setting up system parameters.\n");
client.reg_write(SYSTEM_CLOCK_OFFSET, SYSTEM_CLOCK)
client.reg_write(NUM_SAMPLES_OFFSET, NUM_SAMPLES)
client.reg_write(PID_KP_OFFSET, PID_KP)
client.reg_write(PID_KI_OFFSET, PID_KI)
client.reg_write(PID_KD_OFFSET, PID_KD)
client.reg_write(PULSE_LOW_OFFSET, PULSE_LOW)
client.reg_write(PULSE_HIGH_OFFSET, PULSE_HIGH)
client.reg_write(PULSE_VAL_OFFSET, PULSE_VAL)

print ('Okay, now lets blink some lights and run some tests!!')
print ('First test - sweep a couple of sinewaves on ADC B')

#print ('run # %d ' % i)
client.reg_write(LED_OFFSET, 0x0F) #Was 234
sleep(0.1)
client.reg_write(LED_OFFSET, 0x00) #Was 234
sleep(0.1)
client.reg_write(TUNING_WORD_OFFSET, 10000 + i * 10000) # Sweep NCO!!!
sleep(0.1)

print("Starting Motor with washer clamped...\n");
client.reg_write(START_OFFSET, WASHERCLAMP | MOTOR | CHANNEL | 0);
sleep(3)
client.reg_write(START_OFFSET, WASHERCLAMP | MOTOR | CHANNEL | 0x00000001);
client.reg_write(START_OFFSET, WASHERCLAMP | MOTOR | CHANNEL | 0);
sleep(1); #sleep for a second
ready = client.reg_read(DATA_READY_OFFSET) # Check data ready signal
print('ready signal is %d' % ready)
print("Capture finished.\n");

print('Reading a block...')
dummy, block = client.mem_read_block(0, NUM_SAMPLES)
data = (ctypes.c_int * NUM_SAMPLES).from_buffer(bytearray(block))
print('Got a %d byte block back' % len(block))
print('first 16 values:')
for j in range(0, 16):
    print('value %d' % data[j])
print('and the last value: %d' % data[NUM_SAMPLES - 1])
pythondata = [0] * NUM_SAMPLES
for k in range(0, NUM_SAMPLES): # Fix sign extension
    if(data[k] >= 524288):
        data[k] -= 1048576
    pythondata[k] = data[k]
    
filterdata = np.convolve(pythondata, sinc1)
filterdata = filterdata / osr

plt.figure(1)
plt.subplot(2,1,1)
plt.plot(pythondata)
plt.plot(filterdata)
        


print("Starting Motor with washer released...\n");
client.reg_write(START_OFFSET, MOTOR | CHANNEL | 0x00000001);
client.reg_write(START_OFFSET, MOTOR | CHANNEL | 0);
sleep(1); #sleep for a second
ready = client.reg_read(DATA_READY_OFFSET) # Check data ready signal
print('ready signal is %d' % ready)
print("Capture finished.\n");

print('Reading a block...')
dummy, block = client.mem_read_block(0, NUM_SAMPLES)
data = (ctypes.c_int * NUM_SAMPLES).from_buffer(bytearray(block))
print('Got a %d byte block back' % len(block))
print('first 16 values:')
for j in range(0, 16):
    print('value %d' % data[j])
print('and the last value: %d' % data[NUM_SAMPLES - 1])
pythondata = [0] * NUM_SAMPLES
for k in range(0, NUM_SAMPLES): # Fix sign extension
    if(data[k] >= 524288):
        data[k] -= 1048576
    pythondata[k] = data[k]
    
filterdata = np.convolve(pythondata, sinc1)
filterdata = filterdata / osr

plt.figure(1)
plt.subplot(2,1,2)
plt.plot(pythondata)
plt.plot(filterdata)


plt.show()

client.reg_write(START_OFFSET, 0);

'''
# OLD register map, for reference
#control register offsets
LED_OFFSET = 0xE0
EXPANDER_CTRL_OFFSET = 0x00
PID_KP_OFFSET = 0xD0
PID_KI_OFFSET = 0xC0
PID_KD_OFFSET = 0xB0
PULSE_LOW_OFFSET = 0xA0
PULSE_HIGH_OFFSET = 0x90
PULSE_VAL_OFFSET = 0x80
FOS_TAU_OFFSET = 0x70
FOS_GAIN_OFFSET = 0x60
FOS_CLOCK_OFFSET = 0x50
SYSTEM_CLOCK_OFFSET = 0x40
NUM_SAMPLES_OFFSET = 0x30
START_OFFSET = 0x20
DATA_READY_OFFSET = 0x10
'''

