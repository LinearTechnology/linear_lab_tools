'''
JESD204B Playground
This program demonstrates how to 
Tested with Python 2.7, Anaconda distribution available from Continuum Analytics,
http://www.continuum.io/

Demo board documentation:
http://www.linear.com/demo/xxxx
http://www.linear.com/product/xxxx

LTC2123 product page
http://www.linear.com/product/LTC2123

REVISION HISTORY
$Revision: 4258 $
$Date: 2015-10-19 15:29:19 -0700 (Mon, 19 Oct 2015) $

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
import sys
sys.path.append("../../")
import ltc_controller_comm as comm
from jesd204b_playground_functions import *

# Initialize script operation parameters
tx_bitfile_id = 0xB7 # TX side Bitfile ID
rx_bitfile_id = 0xB8

# Enable Hardware initialization. This only needs to be done on the first run.
# Can be disabled for testing purposes.
initialize_spi = 0
initialize_core = 0

# Display lots of debug messages
verbose = True



#patterncheck = 32 #Enable PRBS check, ADC data otherwise
patterncheck = 0 # Zero to disable PRBS check, dumps number of samples to console for numbers >0
dumppattern = 32 #Dump pattern analysis

dumpdata = 32 # Set to 1 and select an option below to dump to STDOUT:

dump_pscope_data = 1 # Writes data to "pscope_data.csv", append to header to open in PScope

n = NumSamp64K # Set number of samples here.

#Configure other ADC modes here to override ADC data / PRBS selection
forcepattern = 0    #Don't override ADC data / PRBS selection
# Other options:
# 0x04 = PRBS, 0x06 Test Samples test pattern, 0x07 = RPAT,
# 0x02 = K28.7 (minimum frequency), 0x03 = D21.5 (maximum frequency)

sleeptime = 0.1

devices = [None] * 2
device = None
rxdevice = None
txdevice = None

do_reset = True  # Reset FPGA once (not necessary to reset between data loads)
num_devices = 0
test_mode = TEST_MODE0
SCR = 1

if verbose:
    print "\n\tJESD204B Playground Test Script!\n"
    print "Verify that TX and RX reference and device clocks are turned on!"
    raw_input("Press Enter when done...")
    
# Open communication to the demo board
descriptions = ['LTC UFO Board', 'LTC Communication Interface', 'LTC2000 Demoboard', 'LTC2000, DC2085A-A']
num_devices, device_info = find_devices(descriptions)

#######################################################################
# Configuration Flow Step 1, 2: Configure TX's and Rx's FTDI MPSSE mode
#######################################################################
txdevice_index, rxdevice_index = detect_TXRX(num_devices, device_info, tx_bitfile_id, rx_bitfile_id)

####################################################################################
# Configuration Flow Step 3: Check TX FPGA board system an reference clock available
####################################################################################
print "\nChecking TX FPGA system and reference clock..."
check_reference_clock(comm.Controller(device_info[txdevice_index]), TX_CLOCK_STATUS_REG)
print "\nChecking RX FPGA system and reference clock..."
check_reference_clock(comm.Controller(device_info[rxdevice_index]), RX_CLOCK_STATUS_REG)
    
######################################################################
# Configuration Flow Step 7: TX FPGA Reset 
# Configuration Flow Step 8: RX FPGA Reset and release
# Configuration Flow Step 9: Check RX reference clock and board system
######################################################################
print "\nResetting TX..."
reset_fpga(comm.Controller(device_info[txdevice_index]), do_reset)
print "Resetting RX..."
reset_fpga(comm.Controller(device_info[rxdevice_index]), do_reset)
print "\nChecking RX FPGA system and reference clock..."
check_reference_clock(comm.Controller(device_info[rxdevice_index]), RX_CLOCK_STATUS_REG)

#############################################################
# Configuration Flow Step 10: Generate RX Sysref 312.5 MHz/64
#############################################################
print "\nVerify that RX Sysref 312.5 MHz/64 is generated!"
raw_input("Press Enter when done...")
     
##################################################################
# Configuration Flow Step 11: Configure JESD204B RX core registers
##################################################################
with comm.Controller(device_info[rxdevice_index]) as rxdevice:
    b3, b2, b1, b0 = read_jesd204b_reg(rxdevice, 0x00)          # Read version
    print "\nRX Version: ", b3, b2, b1, b0
    print "Configuring JESD204B RX core registers..."
    write_jesd204b_reg(rxdevice, 0x08, 0x00, 0x00, 0x00, 0x01)  #Enable ILA
    write_jesd204b_reg(rxdevice, 0x0C, 0x00, 0x00, 0x00, SCR)   #Scrambling - 0 to disable, 1 to enable
    write_jesd204b_reg(rxdevice, 0x10, 0x00, 0x00, 0x00, 0x00)  # Only respond to first SYSREF (Subclass 1 only)
    write_jesd204b_reg(rxdevice, 0x18, 0x00, 0x00, 0x00, test_mode)  # Select Test modes		
    write_jesd204b_reg(rxdevice, 0x20, 0x00, 0x00, 0x00, 0x01)  # 2 octets per frame
    write_jesd204b_reg(rxdevice, 0x24, 0x00, 0x00, 0x00, 0x1F)  # Frames per multiframe, 1 to 32 for V6 core
    write_jesd204b_reg(rxdevice, 0x28, 0x00, 0x00, 0x00, 0x0B)  # Lanes in use - program with N-1
    write_jesd204b_reg(rxdevice, 0x2C, 0x00, 0x00, 0x00, 0x01)  # Subclass 1
    write_jesd204b_reg(rxdevice, 0x30, 0x00, 0x00, 0x00, 0x00)  # RX buffer delay = 0
    write_jesd204b_reg(rxdevice, 0x34, 0x00, 0x00, 0x01, 0x00)  # Disable error counters, error reporting by SYNC~
    write_jesd204b_reg(rxdevice, 0x04, 0x00, 0x00, 0x00, 0x01)  # Reset core    
    sleep(sleeptime)
    b3, b2, b1, b0 = read_jesd204b_reg(rxdevice, 0x04)
    if((b3, b2, b1, b0) == (0, 0, 0, 0)):
        print "RX Core Reset complete!"    
    else:
        print "RX Core Reset not complete!"

#######################################################################
# Configuration Flow Step 12: TX FPGA Reset and release
# Configuration Flow Step 13: Check TX reference clock and board system
#######################################################################
print "Resetting TX..."
reset_fpga(comm.Controller(device_info[txdevice_index]), do_reset)  
print "\nChecking TX FPGA system and reference clock..."
check_reference_clock(comm.Controller(device_info[txdevice_index]), TX_CLOCK_STATUS_REG)
    
##################################################################
# Configuration Flow Step 14: Configure JESD204B tX core registers
##################################################################
with comm.Controller(device_info[txdevice_index]) as txdevice:
    b3, b2, b1, b0 = read_jesd204b_reg(txdevice, 0x00)          # Read version
    print "\nTX Version: ", b3, b2, b1, b0
    print "Configuring JESD204B TX core registers..."
    write_jesd204b_reg(txdevice, 0x08, 0x00, 0x00, 0x00, 0x01)  # Enable ILA
    write_jesd204b_reg(txdevice, 0x0C, 0x00, 0x00, 0x00, SCR)   # Scrambling - 0 to disable, 1 to enable
    write_jesd204b_reg(txdevice, 0x10, 0x00, 0x00, 0x00, 0x00)  # Only respond to first SYSREF (Subclass 1 only)
    write_jesd204b_reg(txdevice, 0x14, 0x00, 0x00, 0x00, 0x03)  # Multiframes in ILA = 4
    write_jesd204b_reg(txdevice, 0x18, 0x00, 0x00, 0x00, test_mode)  # Select Test modes	
    write_jesd204b_reg(txdevice, 0x20, 0x00, 0x00, 0x00, 0x01)  # 2 octets per frame
    write_jesd204b_reg(txdevice, 0x24, 0x00, 0x00, 0x00, 0x1F)  # Frames per multiframe, 1 to 32 for V6 core
    write_jesd204b_reg(txdevice, 0x28, 0x00, 0x00, 0x00, 0x0B)  # Lanes in use - program with N-1
    write_jesd204b_reg(txdevice, 0x2C, 0x00, 0x00, 0x00, 0x01)  # Subclass 1
    write_jesd204b_reg(txdevice, 0x80C, (LIU - 1), 0x00, bid, did)  # Subclass 1
    write_jesd204b_reg(txdevice, 0x810, CS, (Nt - 1), (N - 1), (M - 1))  # Subclass 1
    write_jesd204b_reg(txdevice, 0x814, 0x00, 0x00, 0x00, 0x01)  # Subclass 1
    write_jesd204b_reg(txdevice, 0x818, 0x00, 0x00, 0x00, 0x01)  # Subclass 1
    write_jesd204b_reg(txdevice, 0x04, 0x00, 0x00, 0x00, 0x01)  # Subclass 1
    write_jesd204b_reg(txdevice, 0x04, 0x00, 0x00, 0x00, 0x01)  # Reset core
    sleep(sleeptime)
    b3, b2, b1, b0 = read_jesd204b_reg(txdevice, 0x04)
    if((b3, b2, b1, b0) == (0, 0, 0, 0)):
        print "TX Core Reset complete!"  
    else:
        print "TX Core Reset not complete!"

#####################################################################
# Configuration Flow Step 15: Check TX JEDEC core embedded PLL locked
#####################################################################		
print "\nChecking TX clock status after JESD204B configuration..."
check_PLL_lock(comm.Controller(device_info[txdevice_index]), TX_CLOCK_STATUS_REG, check_sync = False)

#############################################################
# Configuration Flow Step 16: Generate TX Sysref 312.5 MHz/64
#############################################################
# WAIT FOR TX SYSREF
with comm.Controller(device_info[rxdevice_index]) as rxdevice:
    rxdevice.hs_set_bit_mode(comm.HS_BIT_MODE_MPSSE)
    
    ##########################################################
    # Configuration Flow Step 17: Check JESD204B RX is in sync
    ##########################################################
    sleep(sleeptime)
    b3, b2, b1, b0 = read_jesd204b_reg(rxdevice, 0x38)
    if(b0 & 0x01 == 0x01):
        print "RX Sync complete..."
    sleep(sleeptime)
    
#####################################################################
# Configuration Flow Step 18: Check RX JEDEC core embedded PLL locked
#####################################################################
print "\nChecking RX clock status after JESD204B configuration..."
check_PLL_lock(comm.Controller(device_info[rxdevice_index]), RX_CLOCK_STATUS_REG, check_sync = True)

############################################################################
# Configuration Flow Step 19: Configure TX buffer size and transfer mode
# Configuration Flow Step 20: Verify TX buffer is empty
# Configuration Flow Step 21: Configure TX's FTDI as Sync FIFO mode
# Configuration Flow Step 22: TX start to feed the FTDI buffer to send data
# Configuration Flow Step 23: Configure TX's FTDI as MPSSE mode
# Configuration Flow Step 24: Check TX loading is done
############################################################################
#with comm.Controller(device_info[txdevice_index]) as txdevice:
#    check_TX_buffer_empty(txdevice)
#    print "\nReading TX JESD204B core registers..."
#    read_xilinx_core_config(txdevice, verbose = True, read_link_erroe = False)   
#    transmit_file_data(txdevice, 'dacdata_counter.csv')
#    check_TX_loading_done(txdevice)
#    check_TX_start_playback(txdevice)
    
with comm.Controller(device_info[txdevice_index]) as txdevice:
    print("\nReading TX JESD204B core registers...")
    read_xilinx_core_config(txdevice, verbose = True, read_link_erroe = False)

total_samples = (1024 * 12)
transmit_file_data(comm.Controller(device_info[txdevice_index]), 'dacdata_counter.csv', total_samples)

#rx_data = receive_data(comm.Controller(device_info[rxdevice_index]), total_samples)
rx_data = read_rx_data(comm.Controller(device_info[rxdevice_index]), verbose = True)    
    
# Demonstrate how to write generated data to a file.
print('writing data out to file')
outfile = open('dacdata_received.csv', 'w')
for i in range(0, total_samples):
    outfile.write(str(hex(rx_data[i])) + "\n")
outfile.close()
print('done writing!')
    


# Read back RX ILAS registers
with comm.Controller(device_info[rxdevice_index]) as rxdevice:
    rxdevice.hs_set_bit_mode(comm.HS_BIT_MODE_MPSSE)
    print("Reading out RX registers to clear errors...")
    read_xilinx_core_config(rxdevice, verbose = False, read_link_erroe = False)  
    print("Waiting for 5 seconds to see if we accumulate some errors...")
    sleep(5.0)
    if(verbose != 0):
        print "\nReading RX JESD204B core registers..."

    read_xilinx_core_config(rxdevice, verbose = True, read_link_erroe = True)   
    for i in range(0, 4):
        read_xilinx_core_ilas(rxdevice, verbose = True, lane=i, split_all = True)

###############################################
# Configuration Flow Step 26: Check RX output data
# is valid
################################################
with comm.Controller(device_info[rxdevice_index]) as rxdevice:
    rxdevice.hs_set_bit_mode(comm.HS_BIT_MODE_MPSSE)
	
    sleep(sleeptime)
    
    data = rxdevice.hs_fpga_read_data_at_address(RX_CAPTURE_STATUS_REG)
    print "\n RX Capture Status: 0x{:04X}".format(data)
  
  
  
  
  
  
  
  
  
#    
################################################
## Configuration Flow Step 26: Check RX output data
## is valid
#################################################
#with comm.Controller(device_info[rxdevice_index]) as rxdevice:
#    rxdevice.hs_set_bit_mode(comm.HS_BIT_MODE_MPSSE)
#	
#    sleep(sleeptime)
#    
#    data = rxdevice.hs_fpga_read_data_at_address(RX_CAPTURE_STATUS_REG)
#    print "\n RX Capture Status: 0x{:04X}".format(data)
#  
#    print "\n\n          CONVERTING TO TEST MODE 3....."
#    
#    write_jesd204b_reg(rxdevice, 0x18, 0x00, 0x00, 0x00, TEST_MODE3)  # Select Test modes	
#    #write_jesd204b_reg(rxdevice, 0x04, 0x00, 0x00, 0x00, 0x01)  # Reset core
#    sleep(sleeptime)
#    b3, b2, b1, b0 = read_jesd204b_reg(rxdevice, 0x04)
#    if((b3, b2, b1, b0) == (0, 0, 0, 0)):
#        print "RX Core Reset complete!"    
#    else:
#        print "RX Core Reset not complete!"
#
#with comm.Controller(device_info[txdevice_index]) as txdevice:
#    txdevice.hs_set_bit_mode(comm.HS_BIT_MODE_MPSSE)
#    sleep(sleeptime)
#    write_jesd204b_reg(txdevice, 0x18, 0x00, 0x00, 0x00, TEST_MODE3)  # Select Test modes	
#    #write_jesd204b_reg(txdevice, 0x04, 0x00, 0x00, 0x00, 0x01)  # Reset core
#    sleep(sleeptime)
#    
#transmit_file_data(comm.Controller(device_info[txdevice_index]), 'dacdata_rpat.csv', total_samples)
#
#new_data = receive_data(comm.Controller(device_info[rxdevice_index]), total_samples)
#         
#        
## Demonstrate how to write generated data to a file.
#print('writing data out to file')
#outfile = open('dacdata_received_1.csv', 'w')
#for i in range(0, total_samples):
#    outfile.write(str(hex(new_data[i])) + "\n")
#outfile.close()
#print('done writing!')
#
#    