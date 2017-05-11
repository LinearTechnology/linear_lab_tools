#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
SoCkit network communication tester. This script exercises all of the functionality
of the mem_func_client_2 / mem_func_daemon_2 pair, using both "dummy"
functions that do not require any interaction with the FPGA side of the SoC,
as well as "real" functions that assume that EITHER:

1) The cmos_32bit_capture program is loaded into the FPGA, and the A DC2511 or DC2512
is installed, and a clock is applied.
-or-
2) A DC2390 is installed (which has an onboard clock generator and takes
power directly from the SoCkit.)


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
import numpy as np
import math
from time import sleep
import time
from matplotlib import pyplot as plt
# Okay, now the big one... this is the module that communicates with the SoCkit
from llt.common.mem_func_client_2 import MemClient
from llt.utils.sockit_system_functions import *
from llt.utils.DC2390_functions import *

# Get the host from the command line argument. Can be numeric or hostname.
HOST = sys.argv[1] if len(sys.argv) == 2 else '127.0.0.1'
# Override here if desired
#HOST = "192.168.1.231"
#HOST = "10.54.6.26"

# Default script parameters
demo_board = 2390 #UN comment one of these. Only use internal ramp for DC2390,
#demo_board = 2512 # DC2512 can use either internal ramp or external 18-bit ramp generator.
save_pscope_data = False
grab_filtered_data = False
mem_bw_test = False # Set to true to run a ramp test after ADC capture
mem_bw_test_depth = 64 * 2**20

bits_18_ramp_test = True

bit_counter = False
plot_data = False

numbits = 18 # Tested with LTC2386 / DC2290
NUM_SAMPLES = 2**20 #16 * 2**20 #65536 #131072 #8192

internal_ramp = True # When exercising network functions, use internal test pattern.

# For BIG captures, downsample time-domain data before plotting
# and only show NUM_SAMPLES / downsample_factor bins of the FFT.
#downsample_factor = 64
downsample_factor = 1

# This script is also used to test the DC2512 in production. Test pattern is
# an 18-bit counter applied to the data bus. Linduino / QuikEval header must
# have a 32-bit delay between MOSI and MISO - an LTC2668 demo board (DC2025)
# can be used for this purpose.

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

if demo_board == 2512:
    type_rev_check(client, 0x0001, 0x0104)
elif demo_board == 2390:
    type_rev_check(client, 0xABCD, 0x1246)
    LTC6954_configure(client, 4 )
    client.reg_write(SYSTEM_CLOCK_BASE, 99) # 50MHz / (99 + 1) = 500ksps
    

#rev_id = client.reg_read(REV_ID_BASE)
#type_id = rev_id & 0x0000FFFF
#rev = (rev_id >> 16) & 0x0000FFFF
#print ('FPGA load type ID: %04X' % type_id)
#print ('FPGA load revision: %04X' % rev)
#if type_id != 0x0001:
#    print("FPGA type is NOT 0x0001! Make sure you know what you're doing!")

print ('Okay, now lets blink some lights and run some tests!!')

client.reg_write(LED_BASE, 0x01)
sleep(0.1)
client.reg_write(LED_BASE, 0x00)
sleep(0.1)

# Capture data!
xfer_start_time = time.time()

if(internal_ramp == True): # Using internal ramp generator, as opposed to
    client.reg_write(DATAPATH_CONTROL_BASE, RAMP_DATA) # external DC2512 test jig
else:
    client.reg_write(DATAPATH_CONTROL_BASE, ADC_DATA)

data = sockit_uns32_to_signed32(sockit_capture(client, NUM_SAMPLES, trigger = TRIG_NOW, timeout = 2.0))

xfer_time = time.time() - xfer_start_time
print("Capture / xfer time: " + str(xfer_time) + " Seconds...")


if(numbits == 18):
    for i in range(0, NUM_SAMPLES):
        data[i] = (data[i] & 0x0003FFFF)
        if(data[i] > 2**17):
            data[i] -= 2**18


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

# Create downsampled dataset for plotting, if DF > 1
timeplot_data = downsample(data, downsample_factor)

if plot_data:
    #data_nodc *= np.blackman(NUM_SAMPLES)
    #fftdata = np.abs(np.fft.fft(data_nodc)) / NUM_SAMPLES
    #fftdb = 20*np.log10(fftdata / 2.0**31)
    plt.figure(1)
    if(downsample_factor == 1):
        plt.title("Time Record")
    else:
        plt.title("Time Record, downsampled by a factor of " + str(downsample_factor))
    plt.plot(timeplot_data)


if(mem_bw_test == True):
    client.reg_write(DATAPATH_CONTROL_BASE, RAMP_DATA) # Capture a test pattern
    print("Ramp test!")
    errors = sockit_ramp_test(client, mem_bw_test_depth, trigger = TRIG_NOW, timeout = 1.0)
    print("Number of errors: " + str(errors))
    client.reg_write(DATAPATH_CONTROL_BASE, ADC_DATA) # Set datapath back to ADC
    
    
if bits_18_ramp_test == True:
    seed = data[0]
    errors = 0
    for i in range (1, NUM_SAMPLES):
        if(data[i] - 1 != seed):
            errors += 1
        if(data[i] == 131072): # Account for rollover...
            seed = -131072
        else:
            seed = data[i]
    print("DC2512 Production test!!")
    print("Number of errors: " + str(errors))
    
    Linduino_Loopback_test(client)



# no need for any configuration
verbose = True
dummy = False
error = 0

reg_address = 0x60 # This is basically an unused address for the 32bit capture (corresponds to KP, KI, KD for DC2390)
reg_value = 0xB7 # A random starting value (Consider making a REAL random number in the future)
mem_address = 0x88 # Starting address for external DDR3 memory
mem_value = 0xB5 # A random starting value (Consider making a REAL random number in the future)
number_of_writes = 3 # Write to 3 consecutive registers/ DDR3 locations
number_of_reads = 50
starting_address = reg_address

reg_values = []
mem_values = []
for i in range(0, number_of_writes):
    reg_values.append(i*2)
    mem_values.append(i*2)

i2c_output_base_reg = 0x120
i2c_input_base_reg = 0x140

# Testing reg_write
if(verbose == True):    print 'Writing 0x%X to register 0x%X...' %(reg_value, reg_address)
written_address = client.reg_write(reg_address, reg_value, dummy)
if (written_address != reg_address):    
    print 'ERROR in Register Write. Returned wrong address.'
    error = error + 1
    
# Testing reg_read
if(verbose == True):    print 'Reading back register 0x%X...' % reg_address
reg_value_read = client.reg_read(reg_address, dummy)
if(verbose == True):    print 'Value at register 0x%X: 0x%X' % (reg_address, reg_value_read)
if(reg_value_read != reg_value):    
    print 'ERROR in Register Read. Returned wrong value.'
    error = error + 1
    
print '** Tested Reg read and write. **\n'

# Testing mem write
if(verbose == True):    print 'Writing 0x%X to memory location 0x%X...' % (mem_value, mem_address)
written_address = client.mem_write(mem_address, mem_value, dummy)
if (written_address != mem_address):    
    print 'ERROR in Memory Write. Returned wrong address.'
    error = error + 1

# Testing mem read
if(verbose == True):    print 'Reading back memory location 0x%X...'% mem_address
mem_value_read = client.mem_read(mem_address, dummy)
if(verbose == True):    print 'Value at memory location 0x%X : 0x%X' % (mem_address, mem_value_read)
if(mem_value_read != mem_value):
    print 'ERROR in Memroy Read. Returned wrong value.'
    error = error + 1
    
print '** Tested Mem read and write. **\n'

# Testing reg write block
if(verbose == True):    print 'Writing block of %d values to register location 0x%X...' % (number_of_writes, starting_address)
last_location = client.reg_write_block(starting_address, number_of_writes, reg_values, dummy)
if(verbose == True):    print 'Last location written into: 0x%X' % last_location
if(last_location != (starting_address + (number_of_writes-1)*4)):
    print 'ERROR in Reg Write Block. Returned wrong last location'
    error = error + 1
print '** Tested reg_write_block. **\n'
    
# Testing reg read block
values = client.reg_read_block(starting_address, number_of_reads, dummy)
if(verbose):
    print 'Reading out block of %d values from register location 0x%X... ' % (number_of_reads, starting_address)
    print 'Values read out:'
    print values
print '** Tested reg_read_block. **\n'

# Testing mem_write_block
if(verbose == True):    print 'Writing block of %d values to memory location 0x%X...' % (number_of_writes, starting_address)
last_location = client.mem_write_block(starting_address, number_of_writes, mem_values, dummy)
if(verbose == True):    print 'Last location written into: 0x%X' % last_location
if(last_location != (starting_address + (number_of_writes-1)*4)):
    print 'ERROR in Mem Write Block. Returned wrong last location'
    error = error + 1
print '** Tested mem_write_block. **\n'

# Testing mem_read_block
values = client.mem_read_block(starting_address, number_of_reads, dummy)
if(verbose):
    print 'Reading out block of %d values from memory location 0x%X... ' % (number_of_reads, starting_address)
    print 'Values read out:'
    print values
print '** Tested mem_read_block. **\n'

# Testing mem_read_to_file
if(verbose):    print 'Reading block of memory and writing into file...'
client.mem_read_to_file(starting_address, number_of_reads, 'hello.txt', dummy)
print '** Tested mem_read_to_file. **\n'

# Testing mem_write_from_file
if(verbose):    print 'Reading a file and writing into memory...'
client.mem_write_from_file(starting_address + 100, number_of_reads, 'hello.txt', dummy)
values = client.mem_read_block(starting_address + 100, number_of_reads, dummy)
if(verbose):
    print 'Values read out:'
    print values
print '** Tested mem_write_from_file**\n'

# Testing file transfer
file_to_read = "../../../common/ltc25xx_filters/ssinc_4.txt" # Grab a handy file that
file_write_path = "/home/sockit/ssinc_4.txt" # we know exists, send to sockit's home dir.
if(verbose):
    print 'Transferring a file to deamon...'
    print 'File to read: %s' % file_to_read
    print 'File write path: %s' % file_write_path
client.file_transfer(file_to_read, file_write_path)
print '**Tested File transfer**\n'

# Testing DC590 commands - Non-dummy functions
print 'TESTING DC590 COMMANDS'
print 'Enter 0 to stop.'
command = ""
while(command != "0"):
    command = raw_input("\nEnter a string: ")   
    if(command != "0"):
        rawstring = client.send_dc590(i2c_output_base_reg, i2c_input_base_reg, command)
        print("Raw data, no interpretation: %s") % rawstring
    
# Testing Read EEPROM    
print '\nReading EEPROM...'
eeprom_id = client.read_eeprom_id(i2c_output_base_reg, i2c_input_base_reg)
if(verbose):    print 'EEPROM ID string: %s' % eeprom_id
print 'IC identified: %s' %(eeprom_id.split(','))[0]

print '**Tested DC590 commands**\n'




############client.send_json("cd fpga_bitfiles")

#### I2C stuff - to be tested again. #####

#print 'Detecting I2C devices. Number of device: ',
#print client.i2c_identify()

#print 'I2C Testing... ',
#print client.i2c_testing()
#
#slave_address = 0x73  # Globoal 7-bit address: 111 0011
#part_command = 0x2F      # 0010 (write and update all) 1111 (all DACs)
#num_of_bytes = 2
#vals = [0x00, 0x00]
#print 'I2C write byte... ',
#print client.i2c_write_byte(slave_address, part_command, num_of_bytes, vals, dummy = True)
#
#print 'I2C read EEPROM... ',
#print client.i2c_read()
#
choice = raw_input('\nShutdown: y/n? ')
if(choice == 'y'):
    shut = client.shutdown(dummy = False)
    print('Shutting down...' if shut == True else 'Shutdown Failed!')
    



run_time = time.time() - start_time
print("Run time: " + str(run_time) + " Seconds...")
print ("To shut down SoCkit, type \"client.shutdown()\" in console, then hit enter.")