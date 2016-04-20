# -*- coding: utf-8 -*-
"""
    Created by: Noe Quintero
    E-mail: nquintero@linear.com

    REVISION HISTORY
    $Revision: 2583 $
    $Date: 2014-06-27 17:21:46 -0700 (Fri, 27 Jun 2014) $
    
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
        The purpose of this module is to create the packets for the Linduino to
        comminicate to the SPI to Avalon bus
"""

import connect_to_linduino as duino
import AvalonMM_packets as av_pack

# Write data to the Avalon bus
def transaction_write(dc2026, base, write_size, data):
    # Create the packet
    packet = av_pack.create_packet(av_pack.CONST_SEQUENTIAL_WRITE, write_size, 
                                   base, data)
    # Convert to dc2026 string
    packet = av_pack.packet_to_DC590(packet, 4)
    # Send/receive packets via dc2026
    data_packet = dc2026.transfer_packets(packet, 4)
    # Convert dc2026 return packet string to int list 
    data_packet = av_pack.DC590_to_packet(data_packet)
    # Decode packet to data
    data = av_pack.packet_to_data(data_packet)
    return data

# Reads data to the Avalon bus
def transaction_read(dc2026, base, read_size):
    # Create the packet
    packet = av_pack.create_packet(av_pack.CONST_SEQUENTIAL_READ, read_size, 
                                   base)
    #print packet
    # Convert to dc2026 string
    packet = av_pack.packet_to_DC590(packet, read_size)
    #print packet
    # Send/receive packets via DC59
    data_packet = dc2026.transfer_packets(packet, read_size)
    # Convert dc2026 return packet string to int list 
    data_packet =av_pack.DC590_to_packet(data_packet)
    # Decode packet to data
    data = av_pack.packet_to_data(data_packet)
    return data
    
#*************************************************
# Function Tests
#*************************************************

if __name__ == "__main__":
    
    linduino = duino.Linduino() # Look for the Linduino
    try:
        linduino.port.write("M3")
        linduino.transfer_packets('G',0) # Set the GPIO HIGH
        
        print transaction_write(linduino, 0, 4, [0xE3,0x36 ,0x1A, 0x00])
        print transaction_read(linduino, 0, 4)
         
    finally:
        linduino.close()
    print "Test Complete"