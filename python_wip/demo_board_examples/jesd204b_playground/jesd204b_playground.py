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
import numpy as np


# Initialize script operation parameters
tx_bitfile_id = 0xB7 # TX side Bitfile ID
rx_bitfile_id = 0xB8

continuous = False            # Run continuously or once
runs = 0                      # Run counter
runs_with_errors = 0          # Keep track of runs with errors
runs_with_uncaught_errors = 0 # Runs with errors that did not have SYNC~ asserted
errorcount = 0                # Initial error count

# Enable Hardware initialization. This only needs to be done on the first run.
# Can be disabled for testing purposes.
initialize_spi = 0
initialize_core = 0
initialize_reset = 1

# Display time and frequency domain plots for ADC data
plot_data = 1
# Display lots of debug messages
verbose = 1

# Set up JESD204B parameters
did=0xAB # Device ID (programmed into ADC, read back from JEDEC core)
bid=0x0C # Bank      (                 "                            )
K=10     # Frames per multiframe (subclass 1 only)
LIU = 12  # Lanes in use
modes = 0x00 # Enable FAM, LAM (Frame / Lane alignment monitorning)
#modes = 0x18 #Disable FAM, LAM (for testing purposes)

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

device = None
do_reset = True  # Reset FPGA once (not necessary to reset between data loads)

if verbose:
    print "JESD204B Playground Test Script!"

# Open communication to the demo board
descriptions = ['LTC UFO Board', 'LTC Communication Interface', 'LTC2000 Demoboard', 'LTC2000, DC2085A-A']
device_info = None
for info in comm.list_controllers(comm.TYPE_HIGH_SPEED):
    if info.get_description() in descriptions:
        device_info = info
        break
if device_info is None:
    raise(comm.HardwareError('Could not find a compatible device'))

while((runs < 1 or continuous == True) and runs_with_errors < 100000):
    runs += 1
#    if(verbose != 0):
    print "Run number: " + str(runs)
    print "\nRuns with errors: " + str(runs_with_errors) + "\n"
    if (runs_with_uncaught_errors > 0):
        print "***\n***\n***\n*** UNCAUGHT error count: " + str(runs_with_uncaught_errors) + \
        "!\n***\n***\n***\n"

    ################################################
    # Configuration Flow Step 6: Issue Reset Pulse
    ################################################
    
    with comm.Controller(device_info) as device:
        device.hs_set_bit_mode(comm.HS_BIT_MODE_MPSSE)
        if do_reset:
            device.hs_fpga_toggle_reset()
        ################################################
        # Configuration Flow Step 7, 8:
        # Check ID and Clock Status register
        ################################################

        id = device.hs_fpga_read_data_at_address(ID_REG) # Read FPGA ID register
        
		# for TX
		if(id == tx_bitfile_id):
            print "Tx board detected"
		else if(id == rx_bitfile_id):
			print "Rx board detected"
		else
			print "Board not detected"
            
            
        print "Dumping readable FPGA registers"
#       data = device.hs_fpga_read_data_at_address(CAPTURE_STATUS_REG)
#       print "Register 4 (capture status): 0x{:04X}".format(data)
		data = device.hs_fpga_read_data_at_address(CLOCK_STATUS_REG)
		print "Register 2   (Clock status): 0x{:04X}".format(data)
		
		# for TX
		if(data & 0x03 == 0x03):
			print "TX FPGA board system and reference clock available"
		else
			print "Check TX FPGA board system and reference clock available"
		sleep(sleeptime)

        ################################################
        # Configuration Flow Step 9, 10: Configure ADC
        ################################################

                

        ################################################
        # Configuration Flow Step 11: configure JEDEC Core
        ################################################
        if(initialize_core == 1):
            if(verbose != 0):
                print "Configuring JESD204B core!!"
				
			# for RX
            write_jesd204b_reg(device, 0x08, 0x00, 0x00, 0x00, 0x01)  #Enable ILA
            write_jesd204b_reg(device, 0x0C, 0x00, 0x00, 0x00, 0x00)  #Scrambling - 0 to disable, 1 to enable
            write_jesd204b_reg(device, 0x10, 0x00, 0x00, 0x00, 0x01)  # Only respond to first SYSREF (Subclass 1 only)
            write_jesd204b_reg(device, 0x18, 0x00, 0x00, 0x00, 0x00)  # Normal operation (no test modes enabled)
            write_jesd204b_reg(device, 0x20, 0x00, 0x00, 0x00, 0x01)  # 2 octets per frame
            write_jesd204b_reg(device, 0x24, 0x00, 0x00, 0x00, 0x1F)   # Frames per multiframe, 1 to 32 for V6 core
            write_jesd204b_reg(device, 0x28, 0x00, 0x00, 0x00, 0x0B) # Lanes in use - program with N-1
            write_jesd204b_reg(device, 0x2C, 0x00, 0x00, 0x00, 0x01)  # Subclass 1
            write_jesd204b_reg(device, 0x30, 0x00, 0x00, 0x00, 0x00)  # RX buffer delay = 0
            write_jesd204b_reg(device, 0x34, 0x00, 0x00, 0x00, 0x00)  # Disable error counters, error reporting by SYNC~
            write_jesd204b_reg(device, 0x04, 0x00, 0x00, 0x00, 0x01)  # Reset core
			
			# for TX
            write_jesd204b_reg(device, 0x08, 0x00, 0x00, 0x00, 0x01)  #Enable ILA
            write_jesd204b_reg(device, 0x0C, 0x00, 0x00, 0x00, 0x00)  #Scrambling - 0 to disable, 1 to enable
            write_jesd204b_reg(device, 0x10, 0x00, 0x00, 0x00, 0x01)  # Only respond to first SYSREF (Subclass 1 only)
			write_jesd204b_reg(device, 0x14, 0x00, 0x00, 0x00, 0x03)  # Multiframes in ILA = 4
            write_jesd204b_reg(device, 0x18, 0x00, 0x00, 0x00, 0x00)  # Normal operation (no test modes enabled)
            write_jesd204b_reg(device, 0x20, 0x00, 0x00, 0x00, 0x01)  # 2 octets per frame
            write_jesd204b_reg(device, 0x24, 0x00, 0x00, 0x00, 0x1F)   # Frames per multiframe, 1 to 32 for V6 core
            write_jesd204b_reg(device, 0x28, 0x00, 0x00, 0x00, 0x0B) # Lanes in use - program with N-1
            write_jesd204b_reg(device, 0x2C, 0x00, 0x00, 0x00, 0x01)  # Subclass 1
            
			
            write_jesd204b_reg(device, 0x04, 0x00, 0x00, 0x00, 0x01)  # Reset core

        data = device.hs_fpga_read_data_at_address(CLOCK_STATUS_REG)
        print "Double-checking clock status after JESD204B configuration:"
        print "Register 2   (Clock status): 0x{:04X}".format(data)

        if(verbose != 0):
            print "Reading JESD204B core registers..."

#        data, data_ch0, data_ch1, nSamps_per_channel, syncErr = capture2(device, n, dumpdata, dump_pscope_data, verbose)


# Read back 
        if(verbose != 0):
            read_xilinx_core_config(device, verbose = True)
            read_xilinx_core_ilas(device, verbose = True, lane=0)
            read_xilinx_core_ilas(device, verbose = True, lane=1)




