'''
DC2226 / dual LTC2123 with LTC6951 clocking solution Example

This program demonstrates a dual LTC2123 JESD204B interface clocked by
LTC6951 PLL with integrated VCO and clock distribution.

Tested with Python 2.7, Anaconda distribution available from Continuum Analytics,
http://www.continuum.io/

Demo board documentation:
http://www.linear.com/demo/2226
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
from LTC2123_functions import * # Import support functions
from DC2226_clock_configuration import * # Import clock configuration functions
import numpy as np # Import NumPy for analysis

# Initialize script operation parameters
bitfile_id = 0xC0 # Bitfile ID
continuous = 0 # Run continuously, or just once
runs = 0 # Initial run count
runs_with_errors = 0 # Runs with PRBS errors (only valid if PRBStest is enabled)
runs_with_uncaught_errors = 0 # Runs with errors that did NOT indicate SYNC~ assertion during capture

do_reset = True  # Reset FPGA once (not necessary to reset between data loads)
initialize_adcs = 1 # Initialize ADC registers (only need to do on first run)
initialize_clocks = 1 # Initialize onboard clocks (only need to do on first run)
initialize_core = 1 # Initialize JEDEC core in FPGA (only need to do on first run)

verbose = 1 # Print out extra debug information
plot_data = 1 # Plot time and frequency data after capture

patterncheck = 0 # greater than zero to Enable PRBS check, ADC data otherwise
dumppattern = 16 # Dump pattern analysis

dumpdata = 16 # Set to 1 and select an option below to dump to STDOUT:
hexdump = 1     # Data dump format, can be either hex, decimal, or both
dec = 0     # (if both, hex is first, followed by decimal)

dump_pscope_data = 1 # Writes data to "pscope_data.csv", append to header to open in PScope

n = NumSamp64K # Set number of samples here.

# Common ADC / JEDEC Core / Clock parameter(s) 
K = 16 #Frames per multiframe - Note that not all ADC / Clock combinations
# support all values of K.

# ADC configuration parameters
#Configure other ADC modes here to override ADC data / PRBS selection
forcepattern = 0    #Don't override ADC data / PRBS selection
#forcepattern = 0x04 #PRBS
#forcepattern = 0x06 #Test Samples test pattern
#forcepattern = 0x07 #RPAT test pattern
#forcepattern = 0x02 # K28.7 (minimum frequency)
#forcepattern = 0x03 # D21.5 (maximum frequency)

did0=0xEF # JESD204B device ID for ADC 0
did1=0xAB # JESD204B device ID for ADC 1
bid=0x0C # Bank ID (only low nibble is significant)
modes=0x00
#modes=0x18 #Disable FAM/LAM
#modes=0x1A #Disable SYSREF

if(patterncheck != 0):
    pattern0=0x04
    pattern1=0x04
else:
    pattern0=0x00
    pattern1=0x00


verbose = True   # Print extra information to console
sleeptime = 0.5


if verbose:
    print "\n\nLTC2123 DC2226 dual clocking solution Interface Program"

# Open communication to the demo board
device = None
descriptions = frozenset(['LTC UFO Board', 'LTC Communication Interface', 'LTC2000 Demoboard', 'LTC2000, DC2085A-A'])
device_info = None    
for info in comm.list_controllers(comm.TYPE_HIGH_SPEED):
    if info.get_description() in descriptions:
        device_info = info
        break
if device_info is None:
    raise(comm.HardwareError('Could not find a compatible device'))


while((runs < 1 or continuous == 1) and runs_with_errors < 100000):
    runs += 1
    print "Run number: " + str(runs)
    print "\nRuns with errors: " + str(runs_with_errors) + "\n"
    if (runs_with_uncaught_errors > 0):
        print "***\n***\n***\n*** UNCAUGHT error count: " + str(runs_with_uncaught_errors) + \
        "!\n***\n***\n***\n"

    ################################################
    # Configuration Flow Steps 4, 5: 
    # MPSSE Mode, Issue Reset Pulse
    ################################################
    with comm.Controller(device_info) as device:
        device.hs_set_bit_mode(comm.HS_BIT_MODE_MPSSE)
        if do_reset:
            device.hs_fpga_toggle_reset()

        ################################################
        # Configuration Flow Step 6:
        # Check ID register
        ################################################
        id = device.hs_fpga_read_data_at_address(ID_REG) # Read FPGA ID register
        if(verbose != 0):
            #print "FPGA Load ID: 0x{:04X}".format(id)
            bitfile_id_warning(bitfile_id, id)

        ################################################
        # Configuration Flow Step 9, 10: Configure ADC
        ################################################
        if(initialize_adcs == 1):
            load_ltc212x(device, 0, verbose, did0, bid, 2, K, modes, 1, pattern0)
            load_ltc212x(device, 1, verbose, did1, bid, 2, K, modes, 1, pattern1)
            initialize_adcs = 0 # Only initialize on first run
    
        if(initialize_clocks == 1):
            #initialize_DC2226_version2_clocks_300(device, verbose)
            initialize_DC2226_version2_clocks_250(device, verbose)
            initialize_clocks = 0

        ################################################
        # Configuration Flow Step 11: Reset Capture Engine
        ################################################
        device.hs_fpga_write_data_at_address(CAPTURE_RESET_REG, 0x01) #Reset
    
        ################################################
        # Configuration Flow Step 19: Check Clock Status
        ################################################
        if(verbose != 0):
            print "Reading Clock Status register; should be 0x16 (or at least 0x04 bit set)"
            data = device.hs_fpga_read_data_at_address(CLOCK_STATUS_REG)
            print "Register 6   (Clock status): 0x{:04X}".format(data)
            sleep(sleeptime)
    
        ################################################
        # Configuration Flow Step 11: configure JEDEC Core
        # Refer to Xilinx user manual for detailed register descriptioins
        ################################################
        if(initialize_core == 1):
            if(verbose != 0):
                print "Configuring V6 JESD204B core!!"
            write_jesd204b_reg(device, 0x08, 0x00, 0x00, 0x00, 0x01)  #Enable ILA
            write_jesd204b_reg(device, 0x0C, 0x00, 0x00, 0x00, 0x00)  #Scrambling - 0 to disable, 1 to enable
            write_jesd204b_reg(device, 0x10, 0x00, 0x00, 0x00, 0x01)  # Only respond to first SYSREF (Subclass 1 only)
            write_jesd204b_reg(device, 0x18, 0x00, 0x00, 0x00, 0x00)  # Normal operation (no test modes enabled)
            write_jesd204b_reg(device, 0x20, 0x00, 0x00, 0x00, 0x01)  # 2 octets per frame
            write_jesd204b_reg(device, 0x24, 0x00, 0x00, 0x00,  K-1)  # Frames per multiframe, 1 to 32 for V6 core
            write_jesd204b_reg(device, 0x28, 0x00, 0x00, 0x00, 0x03)  # Lanes in use - program with N-1
            write_jesd204b_reg(device, 0x2C, 0x00, 0x00, 0x00, 0x01)  # Subclass = 1
            write_jesd204b_reg(device, 0x30, 0x00, 0x00, 0x00, 0x00)  # RX buffer delay = 0
            write_jesd204b_reg(device, 0x34, 0x00, 0x00, 0x00, 0x00)  # Disable error counters, error reporting by SYNC~
            write_jesd204b_reg(device, 0x04, 0x00, 0x00, 0x00, 0x01)  # Reset core

        if(verbose != 0):
            print "Capturing data and resetting..."
        data_ch0, data_ch1, data_ch2, data_ch3, nSamps_per_channel, syncErr = capture4(device, n, dumpdata, dump_pscope_data, verbose)
    
        errorcount = 0
        if(patterncheck !=0):
            errorcount = pattern_checker(data_ch0, n.BuffSize/2, dumppattern)
            errorcount += pattern_checker(data_ch1, n.BuffSize/2, dumppattern)
            errorcount += pattern_checker(data_ch2, n.BuffSize/2, dumppattern)
            errorcount += pattern_checker(data_ch3, n.BuffSize/2, dumppattern)
            print "error count: " + str(errorcount) + " !"

        if(errorcount != 0):
            outfile = open("LTC2123_python_error_log.txt", "a")
            outfile.write("Caught " + str(errorcount) + "errors on run " + str(runs) + "\n")
            byte3, byte2, byte1, byte0 = read_jesd204b_reg(device, 0x24)
            outfile.write("Register 0x24, all bytes: " + ' {:02X} {:02X} {:02X} {:02X}'.format(byte3, byte2, byte1, byte0))
            byte3, byte2, byte1, byte0 = read_jesd204b_reg(device, 0x27)
            outfile.write("Register 0x27, all bytes: " + ' {:02X} {:02X} {:02X} {:02X}'.format(byte3, byte2, byte1, byte0))        
            outfile.close()

            runs_with_errors += 1
            if (syncErr == False):
                runs_with_uncaught_errors += 1


# Stopgap to get PScope data out. Need to make a single, 4-channel file at some point
# (use LTC2175 to generate template...)
        if((n == NumSamp64K) & dump_pscope_data == 1):
            write_1ch_32k_pscope_file(data_ch0, ("ch0_data.adc"))
            write_1ch_32k_pscope_file(data_ch1, ("ch1_data.adc"))
            write_1ch_32k_pscope_file(data_ch2, ("ch2_data.adc"))
            write_1ch_32k_pscope_file(data_ch3, ("ch3_data.adc"))
            
        if((plot_data != 0) & (patterncheck == 0)):
            from matplotlib import pyplot as plt
            plt.figure(1)
            plt.subplot(411)
            plt.plot(data_ch0)
            plt.title('CH0')
            plt.subplot(412)
            plt.title('CH1')
            plt.plot(data_ch1)
            plt.subplot(413)
            plt.title('CH2')
            plt.plot(data_ch2)
            plt.subplot(414)
            plt.title('CH3')
            plt.plot(data_ch3)
            plt.show()

            fftlength = n.BuffSize/2
            data_ch0 = data_ch0 * np.blackman(fftlength) # Apply Blackman window
            freq_domain_ch0 = np.fft.fft(data_ch0)/(fftlength) # FFT
            freq_domain_magnitude_ch0 = np.abs(freq_domain_ch0) # Extract magnitude
            freq_domain_magnitude_db_ch0 = 10 * np.log(freq_domain_magnitude_ch0/fftlength)
    
            data_ch1 = data_ch1 * np.blackman(fftlength) # Apply Blackman window
            freq_domain_ch1 = np.fft.fft(data_ch1)/(fftlength) # FFT
            freq_domain_magnitude_ch1 = np.abs(freq_domain_ch1) # Extract magnitude
            freq_domain_magnitude_db_ch1 = 10 * np.log(freq_domain_magnitude_ch1/fftlength)
    
            data_ch2 = data_ch2 * np.blackman(fftlength) # Apply Blackman window
            freq_domain_ch2 = np.fft.fft(data_ch2)/(fftlength) # FFT
            freq_domain_magnitude_ch2 = np.abs(freq_domain_ch2) # Extract magnitude
            freq_domain_magnitude_db_ch2 = 10 * np.log(freq_domain_magnitude_ch2/fftlength)
            
            data_ch3 = data_ch3 * np.blackman(fftlength) # Apply Blackman window
            freq_domain_ch3 = np.fft.fft(data_ch3)/(fftlength) # FFT
            freq_domain_magnitude_ch3 = np.abs(freq_domain_ch3) # Extract magnitude
            freq_domain_magnitude_db_ch3 = 10 * np.log(freq_domain_magnitude_ch3/fftlength)
            
            plt.figure(2)
            plt.subplot(411)
            plt.title('CH0 FFT')
            plt.plot(freq_domain_magnitude_db_ch0)
            plt.subplot(412)
            plt.title('CH1 FFT')
            plt.plot(freq_domain_magnitude_db_ch1)
            plt.subplot(413)
            plt.title('CH2 FFT')
            plt.plot(freq_domain_magnitude_db_ch2)
            plt.subplot(414)
            plt.title('CH3 FFT')
            plt.plot(freq_domain_magnitude_db_ch3)
            plt.show()
            searchstart = 5 
# Let's try to measure phases... only look in first half of FFT to avoid being confused
            peak_index0 = np.argmax(freq_domain_magnitude_ch0[searchstart:fftlength/2])
            peak_index1 = np.argmax(freq_domain_magnitude_ch1[searchstart:fftlength/2])
            peak_index2 = np.argmax(freq_domain_magnitude_ch2[searchstart:fftlength/2])
            peak_index3 = np.argmax(freq_domain_magnitude_ch3[searchstart:fftlength/2])
            print("Found peaks in these bins:")
            print (peak_index0 + searchstart)
            print (peak_index1 + searchstart)
            print (peak_index2 + searchstart)
            print (peak_index3 + searchstart)
# Now find phases of these bins
            print ("with these phases:")
            print(np.angle(freq_domain_ch0[peak_index0+searchstart]))
            print(np.angle(freq_domain_ch1[peak_index1+searchstart]))
            print(np.angle(freq_domain_ch2[peak_index2+searchstart]))
            print(np.angle(freq_domain_ch3[peak_index3+searchstart]))
            

# Read out JESD204B core registers
        if(verbose != 0):
            read_xilinx_core_config(device, verbose = True)
            read_xilinx_core_ilas(device, verbose = True, lane=0)
            read_xilinx_core_ilas(device, verbose = True, lane=1)
            read_xilinx_core_ilas(device, verbose = True, lane=2)
            read_xilinx_core_ilas(device, verbose = True, lane=3)

    
    

