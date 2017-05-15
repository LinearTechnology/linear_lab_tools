# -*- coding: utf-8 -*-
"""
Created on Mon Aug 03 15:46:20 2015

@author: Noe
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
from llt.common.mem_func_client_2 import MemClient
from llt.utils.DC2390_functions import *
# Get the host from the command line argument. Can be numeric or hostname.
#HOST = sys.argv.pop() if len(sys.argv) == 2 else '127.0.0.1'
HOST = sys.argv[1] if len(sys.argv) == 2 else '127.0.0.1'

SYSTEM_CLOCK_DIVIDER = 199
NUM_SAMPLES = 8192

nco_word_width = 32
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
client.reg_write(SYSTEM_CLOCK_BASE, 0xFFFF0000 | SYSTEM_CLOCK_DIVIDER)
client.reg_write(NUM_SAMPLES_BASE, NUM_SAMPLES)

LTC6954_configure(client, 0x04)

# Set the NCO to 1KHz
tuning_word = Hz_2_tuning_word(master_clock, nco_word_width, 500)# 1953.0)
client.reg_write(TUNING_WORD_BASE, tuning_word)

# Configure the LTC2500
ltc2500_cfg_led_on  = (((LTC2500_DF_128 | LTC2500_SINC_FILT)<<6) | 0x03 | 
                       (LTC2500_N_FACTOR << 16))
ltc2500_cfg_led_off = (((LTC2500_DF_128 | LTC2500_SINC_FILT)<<6) | 
                        (LTC2500_N_FACTOR << 16))

client.reg_write(LED_BASE, ltc2500_cfg_led_on)
sleep(0.1)
client.reg_write(LED_BASE, ltc2500_cfg_led_off)
sleep(0.1)

# ADC A nyquist test
# -----------------------------------------------------------------------------

# Set Mux for raw Nyquist data
# Set Dac A for SIN and Dac B for LUT
client.reg_write(DATAPATH_CONTROL_BASE, DC2390_FIFO_ADCA_NYQ |
                 DC2390_DAC_B_NCO_COS | DC2390_DAC_A_NCO_SIN | 
                 DC2390_LUT_ADDR_COUNT | DC2390_LUT_RUN_CONT)

# Capture the data
data = capture(client, NUM_SAMPLES, trigger = 0, timeout = 1.0)
#for i in range(NUM_SAMPLES):
#    data[i] = int(((data[i] & 0x7FFFFFFF) << 1))

plt.figure(1)
plt.title('Nyquist ADC A')
plt.plot(data)


# ADC B nyquist test
# -----------------------------------------------------------------------------

# Set Mux for raw Nyquist data
# Set Dac A for SIN and Dac B for LUT
client.reg_write(DATAPATH_CONTROL_BASE, DC2390_FIFO_ADCB_NYQ |
                 DC2390_DAC_B_NCO_COS | DC2390_DAC_A_NCO_SIN | 
                 DC2390_LUT_ADDR_COUNT | DC2390_LUT_RUN_CONT)

# Capture the data
data = capture(client, NUM_SAMPLES, trigger = 0, timeout = 1.0)
plt.figure(2)
plt.title('Nyquist ADC B')
plt.plot(data)


# ADC A filter test
# -----------------------------------------------------------------------------

# Set Mux for filtered data
# Set Dac A for SIN and Dac B for LUT
client.reg_write(DATAPATH_CONTROL_BASE, DC2390_FIFO_ADCA_FIL | 
                 DC2390_DAC_B_NCO_COS | DC2390_DAC_A_NCO_SIN | 
                 DC2390_LUT_ADDR_COUNT | DC2390_LUT_RUN_CONT)

# Capture the data
data = capture(client, NUM_SAMPLES, trigger = 0, timeout = 1.0)
plt.figure(3)
plt.title('filt ADC A')
plt.plot(data)

#for i in range(32):
#    print format(data[i] & 0xFFFFFFFF, '#032b')


# ADC B filter test
# -----------------------------------------------------------------------------

# Set Mux for raw Nyquist data
# Set Dac A for SIN and Dac B for LUT
client.reg_write(DATAPATH_CONTROL_BASE, DC2390_FIFO_ADCB_FIL |
                 DC2390_DAC_B_NCO_COS | DC2390_DAC_A_NCO_SIN |
                 DC2390_LUT_ADDR_COUNT | DC2390_LUT_RUN_CONT)

# Capture the data
data = capture(client, NUM_SAMPLES, trigger = 0, timeout = 1.0)
plt.figure(4)
plt.title('filt ADC B')
plt.plot(data)


# Formatter Nyquist test
# -----------------------------------------------------------------------------

# Set Mux for raw Nyquist data
# Set Dac A for SIN and Dac B for LUT
client.reg_write(DATAPATH_CONTROL_BASE, DC2390_FIFO_FORMATTER_NYQ |
                 DC2390_DAC_B_NCO_COS | DC2390_DAC_A_NCO_SIN |
                 DC2390_LUT_ADDR_COUNT | DC2390_LUT_RUN_CONT)

# Capture the data
data = capture(client, NUM_SAMPLES, trigger = 0, timeout = 1.0)

# Parse the data
data1 = []
data2 = []
for i in range(0,len(data)/2-1):
    data1.append(data[i*2])
    data2.append(data[i*2+1])

plt.figure(5)
plt.title('Nyquist Formatter')
plt.subplot(2, 1, 1)
plt.plot(data1)
plt.subplot(2, 1, 2)
plt.plot(data2)


# Formatter filtered test
# -----------------------------------------------------------------------------

# Set Mux for raw Nyquist data
# Set Dac A for SIN and Dac B for LUT
client.reg_write(DATAPATH_CONTROL_BASE, DC2390_FIFO_FORMATTER_FILT |
                 DC2390_DAC_B_NCO_COS | DC2390_DAC_A_NCO_SIN |
                 DC2390_LUT_ADDR_COUNT | DC2390_LUT_RUN_CONT)

# Capture the data
data = capture(client, NUM_SAMPLES, trigger = 0, timeout = 1.0)

data1 = []
data2 = []
data3 = []
data4 = []
data5 = []
data6 = []
data7 = []
data8 = []
data9 = []
data10 = []
data11 = []
data12 = []
data13 = []
data14 = []
data15 = []
data16 = []


for i in range(0,len(data)/16-1):
    data1.append(data[i*16])
    data2.append(data[i*16+1])
    data3.append(data[i*16+2])
    data4.append(data[i*16+3])
    data5.append(data[i*16+4])
    data6.append(data[i*16+5])
    data7.append(data[i*16+6])
    data8.append(data[i*16+7])
    data9.append(data[i*16+8])
    data10.append(data[i*16+9])
    data11.append(data[i*16+10])
    data12.append(data[i*16+11])
    data13.append(data[i*16+12])
    data14.append(data[i*16+13])
    data15.append(data[i*16+14])
    data16.append(data[i*16+15])

plt.figure(6)
plt.title('Filtered Formatter')

plt.subplot(4,1,1)
plt.plot(data1)
#plt.subplot(16,1,2)
#plt.plot(data2)
plt.subplot(4,1,2)
plt.plot(data3)
#plt.subplot(16,1,4)
#plt.plot(data4)
#plt.subplot(16,1,5)
#plt.plot(data5)
#plt.subplot(16,1,6)
#plt.plot(data6)
#plt.subplot(16,1,7)
#plt.plot(data7)
#plt.subplot(16,1,8)
#plt.plot(data8)
plt.subplot(4,1,3)
plt.plot(data9)
#plt.subplot(16,1,10)
#plt.plot(data10)
plt.subplot(4,1,4)
plt.plot(data11)
#plt.subplot(16,1,12)
#plt.plot(data12)
#plt.subplot(16,1,13)
#plt.plot(data13)
#plt.subplot(16,1,14)
#plt.plot(data14)
#plt.subplot(16,1,15)
#plt.plot(data15)
#plt.subplot(16,1,16)
#plt.plot(data16)

def pos32bithexstring(value):
    if value < 0:
        value = ((abs(value) ^ 0xFFFFFFFF) + 1) & 0xFFFFFFFF
    valuestring = "0x{:08X}".format(value)
    return(valuestring)

print ("data2 first element: " + pos32bithexstring(data2[0]))
print ("data4 first element: " + pos32bithexstring(data4[0]))
print ("data5 first element: " + pos32bithexstring(data5[0]))
print ("data6 first element: " + pos32bithexstring(data6[0]))
print ("data7 first element: " + pos32bithexstring(data7[0]))
print ("data8 first element: " + pos32bithexstring(data8[0]))
print ("data10 first element: " + pos32bithexstring(data10[0]))
print ("data12 first element: " + pos32bithexstring(data12[0]))
print ("data13 first element: " + pos32bithexstring(data13[0]))
print ("data14 first element: " + pos32bithexstring(data14[0]))
print ("data15 first element: " + pos32bithexstring(data15[0]))
print ("data16 first element: " + pos32bithexstring(data16[0]))

#for i in range(0,len(data)/2-1):
#    data1.append(data[i*2])
#    data2.append(data[i*2+1])
#
#plt.figure(1)
#plt.subplot(2, 1, 1)
#plt.plot(data1)
#plt.subplot(2, 1, 2)
#plt.plot(data2)
#    
#for x in range (1,2):
#    tuning_word = Hz_2_tuning_word(master_clock, nco_word_width, 1000*x)
#    print "Tuning Word:" + str(tuning_word)
#    
#    ltc2500_cfg_led_on  = ((LTC2500_DF_4 | LTC2500_SSINC_FILT)<<6) | 0x03 | (LTC2500_N_FACTOR << 16)
#    ltc2500_cfg_led_off = ((LTC2500_DF_4 | LTC2500_SSINC_FILT)<<6) | (LTC2500_N_FACTOR << 16)
#    
#    client.reg_write(LED_BASE, ltc2500_cfg_led_on)
#    sleep(0.1)
#    client.reg_write(LED_BASE, ltc2500_cfg_led_off)
#    sleep(0.1)
#    
#    client.reg_write(TUNING_WORD_BASE, tuning_word)
#    
#    # capture raw data 
#    client.reg_write(DATAPATH_CONTROL_BASE, DC2390_FIFO_FORMATTER_NYQ | DC2390_DAC_B_LUT | DC2390_DAC_A_NCO_SIN | DC2390_LUT_ADDR_COUNT | DC2390_LUT_RUN_CONT)
#    
#    plt.clf()
#    
#    data = capture(client, NUM_SAMPLES, trigger = 0, timeout = 10.0)
#    data1 = []
#    data2 = []    
#    for i in range(0,len(data)/2-1):
#        data1.append(data[i*2])
#        data2.append(data[i*2+1])
#
#    
#
#    
#    plt.figure(1)
#    plt.subplot(2, 1, 1)
#    plt.plot(data1)
##    plt.ylim([-2147483647,2147483647])
##    plt.title("Data 1")
#    plt.subplot(2, 1, 2)
#    plt.plot(data2)
#    
##    fftdata2 = np.abs(np.fft.fft(data2))
##    
##    fftdb2 = 20*np.log10(fftdata2 / np.max(fftdata2))
##    
##    plt.subplot(4, 1, 3)
##    plt.title("Data 2")
##    plt.plot(data2)
##    #plt.ylim([-2147483647,2147483647])
##    plt.subplot(4, 1, 4)
##    plt.plot(fftdb2)
#    
##    # Capture filtered data
##    client.reg_write(DATAPATH_CONTROL_BASE, 0x6)
##    
##    
###    sleep(.5)
##    data = capture(client, NUM_SAMPLES, trigger = 0, timeout = 10.0)
##    #data = data * np.blackman(NUM_SAMPLES);
##    #data = data * np.hanning(NUM_SAMPLES);
##    
##    Min = min(data)
##    Max = max(data)
##    vpp_filt = Max - Min
##    
##    fftdata = np.abs(np.fft.fft(data))
##    
##    fftdb = 20*np.log10(fftdata / np.max(fftdata))
##    
##    plt.subplot(4, 1, 3)
##    plt.title("Filtered data")
##    plt.plot(data)
##    plt.ylim([-2147483647,2147483647])
##    plt.subplot(4, 1, 4)
##    plt.plot(fftdb)
##
##    plt.show()
##    gain.append(20*np.log10(float(vpp_filt)/vpp_nyq))
#
#
##plt.figure(2)
##plt.plot(gain)
##plt.ylim([0,1])
#
plt.show()
print "My program took", time.time() - start_time, "to run"