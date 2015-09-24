'''
DC1974 / LTC2123 Interface Example

This program demonstrates how to communicate with the LTC2123 demo board through Python.


Board setup is described in Demo Manual 1974. Follow the procedure in this manual, and
verify operation with PScope software. Once operation is verified, exit PScope
and run this script.

Tested with Python 2.7, Anaconda distribution available from Continuum Analytics,
http://www.continuum.io/

Demo board documentation:
http://www.linear.com/demo/1974
http://www.linear.com/product/LTC2123#demoboards

LTC2123 product page
http://www.linear.com/product/LTC2123

REVISION HISTORY
$Revision: 3018 $
$Date: 2014-12-01 15:53:20 -0800 (Mon, 01 Dec 2014) $

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
from LTC2123_functions import *
import numpy as np


# Initialize script operation parameters
bitfile_id = 0xBE # Bitfile ID
continuous = False            # Run continuously or once
runs = 0                      # Run counter
runs_with_errors = 0          # Keep track of runs with errors
runs_with_uncaught_errors = 0 # Runs with errors that did not have SYNC~ asserted
errorcount = 0                # Initial error count

# Enable Hardware initialization. This only needs to be done on the first run.
# Can be disabled for testing purposes.
initialize_spi = 1
initialize_core = 1
initialize_reset = 1

# Display time and frequency domain plots for ADC data
plot_data = 1
# Display lots of debug messages
verbose = 1

# Set up JESD204B parameters
did=0xAB # Device ID (programmed into ADC, read back from JEDEC core)
bid=0x0C # Bank      (                 "                            )
K=10     # Frames per multiframe (subclass 1 only)
LIU = 2  # Lanes in use
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
    print "Basic LTC2123 DC1974 Interface Program"

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
    print "LTC2123 Interface Program"
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
        if(verbose != 0):
            bitfile_id_warning(bitfile_id, id)            
            
            
            print "Dumping readable FPGA registers"
            data = device.hs_fpga_read_data_at_address(CAPTURE_STATUS_REG)
            print "Register 4 (capture status): 0x{:04X}".format(data)
            data = device.hs_fpga_read_data_at_address(CLOCK_STATUS_REG)
            print "Register 6   (Clock status): 0x{:04X}".format(data)
            sleep(sleeptime)

        ################################################
        # Configuration Flow Step 9, 10: Configure ADC
        ################################################
        if(initialize_spi == 1):
            if(verbose != 0):
                print "Configuring ADC over SPI:"
            if(patterncheck != 0):
                load_ltc212x(device, 0, verbose, did, bid, LIU, K, modes, 0, 0x04)
            else:
                load_ltc212x(device, 0, verbose, did, bid, LIU, K, modes, 0, forcepattern)
                

        ################################################
        # Configuration Flow Step 11: configure JEDEC Core
        ################################################
        if(initialize_core == 1):
            if(verbose != 0):
                print "Configuring JESD204B core!!"
            write_jesd204b_reg(device, 0x08, 0x00, 0x00, 0x00, 0x01)  #Enable ILA
            write_jesd204b_reg(device, 0x0C, 0x00, 0x00, 0x00, 0x00)  #Scrambling - 0 to disable, 1 to enable
            write_jesd204b_reg(device, 0x10, 0x00, 0x00, 0x00, 0x01)  # Only respond to first SYSREF (Subclass 1 only)
            write_jesd204b_reg(device, 0x18, 0x00, 0x00, 0x00, 0x00)  # Normal operation (no test modes enabled)
            write_jesd204b_reg(device, 0x20, 0x00, 0x00, 0x00, 0x01)  # 2 octets per frame
            write_jesd204b_reg(device, 0x24, 0x00, 0x00, 0x00, K-1)   # Frames per multiframe, 1 to 32 for V6 core
            write_jesd204b_reg(device, 0x28, 0x00, 0x00, 0x00, LIU-1) # Lanes in use - program with N-1
            write_jesd204b_reg(device, 0x2C, 0x00, 0x00, 0x00, 0x00)  # Subclass 0
            write_jesd204b_reg(device, 0x30, 0x00, 0x00, 0x00, 0x00)  # RX buffer delay = 0
            write_jesd204b_reg(device, 0x34, 0x00, 0x00, 0x00, 0x00)  # Disable error counters, error reporting by SYNC~
            write_jesd204b_reg(device, 0x04, 0x00, 0x00, 0x00, 0x01)  # Reset core

        data = device.hs_fpga_read_data_at_address(CLOCK_STATUS_REG)
        print "Double-checking clock status after JESD204B configuration:"
        print "Register 6   (Clock status): 0x{:04X}".format(data)

        if(verbose != 0):
            print "Capturing data and resetting..."

        data, data_ch0, data_ch1, nSamps_per_channel, syncErr = capture2(device, n, dumpdata, dump_pscope_data, verbose)

        if(patterncheck !=0):
            errorcount = pattern_checker(data_ch0, nSamps_per_channel, dumppattern)
            errorcount += pattern_checker(data_ch1, nSamps_per_channel, dumppattern)

        if(errorcount != 0):
            outfile = open("LTC2123_python_error_log.txt", "a")
            outfile.write("Caught " + str(errorcount) + "errors on run " + str(runs) + "\n")
            byte3, byte2, byte1, byte0 = read_jesd204b_reg(device, 0x24)
            outfile.write("Register 0x24, all bytes: " + ' {:02X} {:02X} {:02X} {:02X}'.format(byte3, byte2, byte1, byte0))
            byte3, byte2, byte1, byte0 = read_jesd204b_reg(device, 0x27)
            outfile.write("Register 0x27, all bytes: " + ' {:02X} {:02X} {:02X} {:02X}'.format(byte3, byte2, byte1, byte0))
            outfile.close()
            
            outfile = open("error_data_run_" + str(runs) + ".csv", "w")
            outfile.write("channel1, channel2\n")
            for i in range(0, nSamps_per_channel):
                #print "{:d}, ,0".format((data[i]-32768)/4)
                outfile.write(str(data_ch0[i]) + ", " + str(data_ch1[i]) + "\n")
            #print "End"
            #outfile.write("End\n")
            outfile.close()        
            
            runs_with_errors += 1
            if (syncErr == False):
                runs_with_uncaught_errors += 1
            print "error count: " + str(errorcount) + " !"

# Read back 
        if(verbose != 0):
            read_xilinx_core_config(device, verbose = True)
            read_xilinx_core_ilas(device, verbose = True, lane=0)
            read_xilinx_core_ilas(device, verbose = True, lane=1)



# Plot data if not running pattern check
    if((plot_data != 0) & (patterncheck == 0)):
        from matplotlib import pyplot as plt
        plt.figure(1)
        plt.subplot(211)
        plt.plot(data_ch0)
        plt.title('CH0')
        plt.subplot(212)
        plt.title('CH1')
        plt.plot(data_ch1)
        plt.show()


        data_ch0 = data_ch0 * np.blackman(n.BuffSize/2) # Apply Blackman window
        freq_domain_ch0 = np.fft.fft(data_ch0)/(n.BuffSize/2) # FFT
        freq_domain_magnitude_ch0 = np.abs(freq_domain_ch0) # Extract magnitude
        freq_domain_magnitude_db_ch0 = 10 * np.log(freq_domain_magnitude_ch0/8192.0)

        data_ch1 = data_ch1 * np.blackman(n.BuffSize/2) # Apply Blackman window
        freq_domain_ch1 = np.fft.fft(data_ch1)/(n.BuffSize/2) # FFT
        freq_domain_magnitude_ch1 = np.abs(freq_domain_ch1) # Extract magnitude
        freq_domain_magnitude_db_ch1 = 10 * np.log(freq_domain_magnitude_ch1/8192.0)

        
        plt.figure(2)
        plt.subplot(211)
        plt.title('CH0 FFT')
        plt.plot(freq_domain_magnitude_db_ch0)
        plt.subplot(212)
        plt.title('CH1 FFT')
        plt.plot(freq_domain_magnitude_db_ch1)
        plt.show()
