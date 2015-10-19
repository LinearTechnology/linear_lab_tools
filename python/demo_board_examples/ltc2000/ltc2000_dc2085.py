# -*- coding: utf-8 -*-
'''
DC2085 / LTC2000 Interface Example
This program demonstrates how to communicate with the LTC2000 demo board through Python.
Examples are provided for generating sinusoidal data from within the program, as well
as writing and reading pattern data from a file.

Board setup is described in Demo Manual 2085. Follow the procedure in this manual, and
verify operation with the LTDACGen software. Once operation is verified, exit LTDACGen
and run this script.

Tested with Python 2.7, Anaconda distribution available from Continuum Analytics,
http://www.continuum.io/

Demo board documentation:
http://www.linear.com/demo/2085
http://www.linear.com/product/LTC2000#demoboards

LTC2000 product page
http://www.linear.com/product/LTC2000


REVISION HISTORY
$Revision$
$Date$

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

# Import standard Python library functions
from time import sleep
from math import sin, pi

# Import communication library
import sys
sys.path.append("../../")
print sys.path
import ltc_controller_comm as comm

# Import LTC2000 definitions and support functions
import ltc2000_functions as lt2k

verbose = True   # Print extra information to console
sleep_time = 1.0
do_reset = True  # Reset FPGA once (not necessary to reset between data loads)

if verbose:
    print "LTC2000 Interface Program"

# Open communication to the demo board
descriptions = ['LTC UFO Board', 'LTC Communication Interface', 'LTC2000 Demoboard', 'LTC2000, DC2085A-A']
device_info = None    
for info in comm.list_controllers(comm.TYPE_HIGH_SPEED):
    if info.get_description() in descriptions:
        device_info = info
        break
if device_info is None:
    raise(comm.HardwareError('Could not find a compatible device'))

with comm.Controller(device_info) as device:
    device.hs_set_bit_mode(comm.HS_BIT_MODE_MPSSE)
    if do_reset:
        device.hs_fpga_toggle_reset()

    # Read FPGA ID register
    id = device.hs_fpga_read_data_at_address(lt2k.FPGA_ID_REG)
    if verbose:
        print "FPGA Load ID: 0x{:04X}".format(id)    # Check FPGA PLL status
        print "Reading PLL status, should be 0x47"
        data = device.hs_fpga_read_data_at_address(lt2k.FPGA_STATUS_REG)
        print "And it is... 0x{:04X}".format(data)
        print "Turning on DAC..."

    # Turn on DAC (Discrete I/O line from FPGA to LTC2000
    device.hs_fpga_write_data_at_address(lt2k.FPGA_DAC_PD, 0x01)

    sleep(sleep_time)

    if verbose:
        print "Configuring ADC over SPI:"
# Initial register values can be taken directly from LTDACGen.
# Refer to LTC2000 datasheet for detailed register descriptions.
    device.spi_send_byte_at_address(lt2k.SPI_WRITE | lt2k.REG_RESET_PD, 0x00)
    device.spi_send_byte_at_address(lt2k.SPI_WRITE | lt2k.REG_CLK_CONFIG, 0x02)
    device.spi_send_byte_at_address(lt2k.SPI_WRITE | lt2k.REG_DCKI_PHASE, 0x07)
    device.spi_send_byte_at_address(lt2k.SPI_WRITE | lt2k.REG_PORT_EN, 0x0B)
    device.spi_send_byte_at_address(lt2k.SPI_WRITE | lt2k.REG_SYNC_PHASE, 0x00)
    #lt2k.spi_write(device, REG_PHASE_COMP_OUT
    device.spi_send_byte_at_address(lt2k.SPI_WRITE | lt2k.REG_LINER_GAIN, 0x00)
    device.spi_send_byte_at_address(lt2k.SPI_WRITE | lt2k.REG_LINEARIZATION, 0x08)
    device.spi_send_byte_at_address(lt2k.SPI_WRITE | lt2k.REG_DAC_GAIN, 0x20)
    device.spi_send_byte_at_address(lt2k.SPI_WRITE | lt2k.REG_LVDS_MUX, 0x00)
    device.spi_send_byte_at_address(lt2k.SPI_WRITE | lt2k.REG_TEMP_SELECT, 0x00)
    device.spi_send_byte_at_address(lt2k.SPI_WRITE | lt2k.REG_PATTERN_ENABLE, 0x00)
    #lt2k.spi_write(device, REG_PATTERN_DATA
       
    sleep(sleep_time) # Give some time for things to spin up...

    if verbose: # Optionally read back all registers
        lt2k.register_dump(device)

    # 64k, loop forever
    device.hs_fpga_write_data_at_address(lt2k.FPGA_CONTROL_REG, 0x20 | 0x00)
    
    sleep(sleep_time)

# Demonstrates how to generate sinusoidal data. Note that the total data record length
# contains an exact integer number of cycles.

    num_cycles = 800  # Number of sine wave cycles over the entire data record

    total_samples = 65536 # n.BuffSize
    data = total_samples * [0] 
    for i in range(0, total_samples):
        data[i] = int(32000 * sin(num_cycles*2*pi*i/total_samples))

# Demonstrate how to write generated data to a file.
    print('writing data out to file')
    outfile = open('dacdata.csv', 'w')
    for i in range(0, total_samples):
        outfile.write(str(data[i]) + "\n")
    outfile.close()
    print('done writing!')

# Demonstrate how to read data in from a file
# (Note that the same data[] variable is used)
    print('reading data from file')
    infile = open('dacdata.csv', 'r')
#    infile = open('dacdata_sinc.csv', 'r')
    for i in range(0, total_samples):
        data[i] = int(infile.readline())
    infile.close()
    print('done reading!')

    device.hs_set_bit_mode(comm.HS_BIT_MODE_FIFO)
    num_bytes_sent = device.data_send_uint16_values(data) #DAC should start running here!
    print 'num_bytes_sent (should be 131072) = ' + str(num_bytes_sent)
    
