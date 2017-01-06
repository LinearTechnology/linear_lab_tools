# -*- coding: utf-8 -*-
'''
Functions that tend to be the same across all SoCkit FPGA loads


Tested with Python 2.7, Anaconda distribution available from Continuum Analytics,
http://www.continuum.io/


REVISION HISTORY
$Revision: 5385 $
$Date: 2016-06-28 16:04:33 -0700 (Tue, 28 Jun 2016) $

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

Mark Thoren
Linear Technology Corporation
July, 2016
'''

from time import sleep
import time
import ctypes

# Map out your registers here. These correspond directly to base addresses
# in the LTQSys_blob. Read and write values to these addresses, and signals in
# your design wiggle accordingly.
#NEW REGISTER MAP!! (after remapping to generic port names)
#control register offsets

EXPANDER_CTRL_BASE = 0x00
REV_ID_BASE = 0x10
CONTROL_BASE = 0x20
DATA_READY_BASE = 0x30
LED_BASE = 0x40
NUM_SAMPLES_BASE = 0x50
PID_KP_BASE = 0x60
PID_KI_BASE = 0x70
PID_KD_BASE = 0x80
PULSE_LOW_BASE = 0x90
PULSE_HIGH_BASE = 0xA0
PULSE_VAL_BASE = 0xB0
SYSTEM_CLOCK_BASE = 0xC0
DATAPATH_CONTROL_BASE = 0xD0
LUT_ADDR_DATA_BASE = 0xE0
TUNING_WORD_BASE = 0xF0
BUFFER_ADDRESS_BASE = 0x00000100
SPI_PORT_BASE = 0x00000800
SPI_RXDATA = 0x00
SPI_TXDATA = 0x04
SPI_STATUS = 0x08
SPI_CONTROL = 0x0C
SPI_SS = 0x14

TRIG_NOW = 0x00000002 # Trigger immediately.
TRIG_KEY1 = 0x00000000 # 
TRIG_X10 = 0x00000040 # Trigger on test point X10
CW_START = 0x00000001 # START is sort of a misnomer. When asserted, ring buffer is running.

#Additional register definitions for CMOS_32_BIT_CAPTURE load
CIC_RATE_BASE = 0x60


def sockit_capture(client, recordlength, trigger = TRIG_NOW, timeout = 0.0):
    dmy = False #Consider adding this as an argument.
#    print("Starting Capture system...\n");
    client.reg_write(NUM_SAMPLES_BASE, recordlength)
    client.reg_write(CONTROL_BASE, CW_START)
    sleep(0.1) #sleep for a second
    if(trigger == TRIG_NOW):
        print("Software immediate trigger...")
    if(trigger == TRIG_KEY1):
        print("Waiting for trigger on KEY1...")
    if(trigger == TRIG_X10):
        print("Waiting for trigger on X10...")
    client.reg_write(CONTROL_BASE, trigger|CW_START)
#    client.reg_write(CONTROL_BASE, (TRIG_NOW)) # Drive trigger enable high, then low.

#    client.reg_write(CONTROL_BASE, CW_START)
#    sleep(timeout) #sleep for a second
    cap_start_time = time.time();
    ready = client.reg_read(DATA_READY_BASE) # Check data ready signal
    while((ready & 0x01) == 1):
        time.sleep(0.5) ########## VERY IMPORTANT - It's NOT a good idea to keep hammering on a
        ########################## port in a tight busy loop - it (may) leave the port in a
        ########################## "half-open" state too many times...
        ready = client.reg_read(DATA_READY_BASE) # Check data ready signal
    cap_time = time.time() - cap_start_time
    print('ready signal is %d' % ready)
    print("After " + str(cap_time) + " Seconds...")
    if(cap_time > timeout):
        print("TIMED OUT!!")
    client.reg_write(CONTROL_BASE, 0x0)
#    print("Control system execution finished.\n")
#    print("Pulling START signal low.")

#    print("attempting to read stop address...")
    stopaddress = client.reg_read(BUFFER_ADDRESS_BASE)
#    print("Ending address of ring buffer: " + str(stopaddress))
    read_start_address = stopaddress - 4*recordlength - 128*4
#    read_start_address = stopaddress - 16*NUM_SAMPLES # Trying to find triggered data!!


#    print('Reading a block...')
    print 'Starting address: '
    print read_start_address

# Calculate number of 1M blocks
    blocklength = 2**20
    numblocks = 1
    block = [0] * recordlength
    if(recordlength > blocklength):
        numblocks = recordlength / blocklength # Separate into blocks of a megapoint
        print("Reading " + str(numblocks) + " 1M blocks")
        for blocknum in range (0, numblocks): # Read out remaining blocks
            print("Reading out block " + str(blocknum))
            block[(blocknum * blocklength):((blocknum + 1) * blocklength)] = client.mem_read_block(read_start_address, blocklength, dummy = dmy)
            read_start_address += (4 * blocklength)

    else: # Length less than 1M
        print("Reading a block of less than 1M points")
        #block[0:(recordlength-1)] = client.mem_read_block(read_start_address, recordlength)
        block = client.mem_read_block(read_start_address, recordlength)
    return block


    

def sockit_ramp_test(client, recordlength, trigger = 0, timeout = 0.0):
#    print("Starting Capture system...\n");
    client.reg_write(NUM_SAMPLES_BASE, recordlength)
    client.reg_write(CONTROL_BASE, CW_START)
    sleep(0.1) #sleep for a second
    client.reg_write(CONTROL_BASE, TRIG_NOW|CW_START)

# First, capture pattern data
    cap_start_time = time.time();
    ready = client.reg_read(DATA_READY_BASE) # Check data ready signal
    
    while((ready & 0x01) == 1):
        time.sleep(0.5) ########## VERY IMPORTANT - It's NOT a good idea to keep hammering on a
        ########################## port in a tight busy loop - it (may) leave the port in a
        ########################## "half-open" state too many times...
        ready = client.reg_read(DATA_READY_BASE) # Check data ready signal    

    cap_time = time.time() - cap_start_time
    print('ready signal is %d' % ready)
    print("After " + str(cap_time) + " Seconds...")
    if(cap_time > timeout):
        print("TIMED OUT!!")
    client.reg_write(CONTROL_BASE, 0x0)
    stopaddress = client.reg_read(BUFFER_ADDRESS_BASE)
    read_start_address = stopaddress - 4*recordlength
    if(read_start_address < 0):
        print("Original Memory starting address: %d" % read_start_address)
        read_start_address += 2**30
        print("Rolling over zero, let's see if we can deal with it!")
    print("Memory starting address: %d" % read_start_address)

# Calculate number of 1M blocks
    numblocks = 1
    if(recordlength >= 2**20):
        numblocks = recordlength / 2**20 # Separate into blocks of a megapoint
    print("Testing " + str(numblocks) + "blocks")

    errors = 0
    firstblock = True
    blocklength = recordlength / numblocks
    for blocknum in range (0, numblocks):
        print("Testing block " + str(blocknum))
    
    
    #    print('Reading a block...')
        block = client.mem_read_block(read_start_address, blocklength)
        read_start_address += (4 * blocklength)
    #    dummy, block = client.mem_read_block(stopaddress, NUM_SAMPLES) # Trying to find triggered data!!
        data = block#(ctypes.c_int * (blocklength)).from_buffer(bytearray(block))
        print('Got a %d byte block back' % len(block))
        print('First value: %d' % data[0])
        print(' Last value: %d' % data[blocklength - 1])
        if(firstblock == True):
            seed = data[0]
            firstblock = False
        for i in range (0, (recordlength / numblocks)):
            if(data[i] - 1 != seed):
                errors += 1
            seed = data[i]
    print("Pardon the Obi-One error, we'll fix it shortly... we promise.")
    return errors

# A handy function to turn unsigned values from mem_read_block to signed
# 32-bit values
def sockit_uns32_to_signed32(data):
    for i in range(0, len(data)):    
        if(data[i] > 0x7FFFFFFF):
            data[i] -= 0xFFFFFFFF
    return data
    
def sockit_ltc2500_to_signed32(data):
    for i in range(0, len(data)):
        data[i] = (data[i] & 0x7FFFFFFF) << 1
        if(data[i] > 0x7FFFFFFF):
            data[i] -= 0xFFFFFFFF
    return data