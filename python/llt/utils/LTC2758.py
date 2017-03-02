# -*- coding: utf-8 -*-
"""
    Created by: Noe Quintero
    E-mail: nquintero@linear.com

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

    Description:
        The purpose of this module is to interface with the LTC2758 for the 
        DC2390.
"""

###############################################################################
# Libraries
###############################################################################

import sys # os, socket, ctypes, struct
import llt.utils.DC2390_functions as DC2390
import math


from llt.common.mem_func_client_2 import MemClient

###############################################################################
# Constants
###############################################################################

# LTC2758 Command codes
# OR'd together with the DAC address to form the command byte
LTC2758_WRITE_SPAN_DAC          = 0x20  # Write Span DAC n
LTC2758_WRITE_CODE_DAC          = 0x30  # Write Code DAC n
LTC2758_UPDATE_DAC              = 0x40  # Update DAC n
LTC2758_UPDATE_ALL              = 0x50  # Update All DACs 
LTC2758_WRITE_SPAN_UPDATE_DAC   = 0x60  # Write Span DAC n and Update DAC n
LTC2758_WRITE_CODE_UPDATE_DAC   = 0x70  # Write Code DAC n and Update DAC n
 
LTC2758_WRITE_SPAN_UPDATE_ALL   = 0x80  # Write Span DAC n and Update All DACs
LTC2758_WRITE_CODE_UPDATE_ALL   = 0x90  # Write Code DAC n and Update All DACs
LTC2758_READ_INPUT_SPAN_REG     = 0xA0  # Read Input Span Register DAC n
LTC2758_READ_INPUT_CODE_REG     = 0xB0  # Read Input Code Register DAC n
LTC2758_READ_DAC_SPAN_REG       = 0xC0  # Read DAC Span Register DAC n
LTC2758_READ_DAC_CODE_REG       = 0xD0  # Read DAC Code Register DAC n
LTC2758_PREVIOUS_CMD            = 0xF0  # Set by previous command

# LTC2758 DAC Addresses
LTC2748_DAC_A                   = 0x00
LTC2748_DAC_B                   = 0x02
LTC2748_ALL_DACS                = 0x0E

# Span Codes
LTC2748_UNIPOLAR_0_P5           = 0x00 # 0V to 5V
LTC2748_UNIPOLAR_0_P10          = 0x01 # 0V to 10V
LTC2748_BIPOLAR_N5_P5           = 0x02 # -5V to 5V
LTC2748_BIPOLAR_N10_P10         = 0x03 # -10V to 10V
LTC2748_BIPOLAR_N2_5_P2_5       = 0x04 # -2.5V to 2.5v
LTC2748_BIPOLAR_N2_5_P7_5       = 0x05 # -2.5v to 7.5V

###############################################################################
# Function Definitions
###############################################################################

# Sends 32 bits to the SPI port: 8-bit command byte + 24-bits of data
def LTC2758_write(client, command, data):
    client.reg_write(DC2390.SPI_PORT_BASE | DC2390.SPI_SS, 0x00000002) # CS[0]
    client.reg_write(DC2390.SPI_PORT_BASE | DC2390.SPI_CONTROL, 0x00000400) # Drop CS
    client.reg_write(DC2390.SPI_PORT_BASE | DC2390.SPI_TXDATA, command)
    client.reg_write(DC2390.SPI_PORT_BASE | DC2390.SPI_TXDATA, (data >> 10) & 0xFF)
    client.reg_write(DC2390.SPI_PORT_BASE | DC2390.SPI_TXDATA, (data >> 2) & 0xFF)
    client.reg_write(DC2390.SPI_PORT_BASE | DC2390.SPI_TXDATA, (data<<6) & 0xFF)
    client.reg_write(DC2390.SPI_PORT_BASE | DC2390.SPI_CONTROL, 0x00000000) #Raise CS
    
def LTC2758_voltage_to_code(desired_voltage, v_ref, span_range):
    # Calculate the min and max output voltage based on the reference    
    if span_range == LTC2748_UNIPOLAR_0_P5:
        max_output = v_ref
        min_output = 0.0
    elif span_range == LTC2748_UNIPOLAR_0_P10:
        max_output = 2.0 * v_ref
        min_output = 0.0
    elif span_range == LTC2748_BIPOLAR_N5_P5:
        max_output = v_ref
        min_output = -v_ref
    elif span_range == LTC2748_BIPOLAR_N10_P10:
        max_output = 2.0 * v_ref
        min_output = -2.0 * v_ref
    elif span_range == LTC2748_BIPOLAR_N2_5_P2_5:
        max_output = 0.5 * v_ref
        min_output = -0.5 * v_ref
    else:
        max_output = 1.5 * v_ref
        min_output = -0.5 * v_ref
    
    # Calculate the DAC code
    code = 262143.0 * (desired_voltage - min_output) / (max_output - min_output) 

    # Round
    if code > (math.floor(code) + 0.5):
        math.ceil(code)
    else:
        math.floor(code)
    # Limit the range
    if code < 0.0: 
        code = 0.0
    if code > 262143.0: 
        code = 262143.0
        
    return int(code) # Convert to integer
    
if __name__ == "__main__": 
    
    # Get the host from the command line argument. Can be numeric or hostname.
    HOST = sys.argv[1] if len(sys.argv) == 2 else '127.0.0.1'
    
    # Connect to the SoC 
    client = MemClient(host=HOST)
    
    # Verify the FPGA bistream
    #Read FPGA type and revision
    rev_id = client.reg_read(DC2390.REV_ID_BASE)
    type_id = rev_id & 0x0000FFFF
    rev = (rev_id >> 16) & 0x0000FFFF
    
    if (type_id != 0xABCD) or (rev != 0x1238):
        print "Wrong FPGA bitstream on the FPGA"
        print 'FPGA load type ID: %04X' % type_id
        print 'FPGA load revision: %04X' % rev
    else:
        print "Correct bitstream file found !!"

    # Set the LTC695 to 50 MHz
    DC2390.LTC6954_configure(client, 0x04)
    
    v_out = 1.2345
    
    code = LTC2758_voltage_to_code(v_out, 5.0, LTC2748_UNIPOLAR_0_P5)
    
    LTC2758_write(client, LTC2748_ALL_DACS | LTC2758_WRITE_CODE_UPDATE_ALL, code)
        
    print "Ideal code: " + str(code)
    
    v_ref = input("Measure the Ref and enter the true voltage")

    code = LTC2758_voltage_to_code(v_out, v_ref, LTC2748_UNIPOLAR_0_P5)
    print "Corrected code: " + str(code)
    LTC2758_write(client, LTC2748_ALL_DACS | LTC2758_WRITE_CODE_UPDATE_ALL, code)
    
    print "done"