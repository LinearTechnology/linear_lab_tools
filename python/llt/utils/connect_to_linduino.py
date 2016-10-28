# -*- coding: utf-8 -*-
"""
    Description:
        The purpose of this module is to find and connect to Linear
        Technology's Linduino. The DC590 enhanced sketch.
    
    Created by: Noe Quintero
    E-mail: nquintero@linear.com

    REVISION HISTORY
    $Revision: $
    $Date: $
    
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
###############################################################################
# Libraries
###############################################################################
import serial
import time


# Scan for serial ports.
# Part of pySerial (http://pyserial.sf.net)
# (C) 2002-2003 <cliechti@gmx.net>
# The scan function of this module tries to open each port number from 0 to 255
# and it builds a list of those ports where this was successful.
def scan():
    """scan for available ports. return a list of tuples (num, name)"""
    available = []
    for i in range(256):
        try:
            s = serial.Serial("COM"+ str(i))
            available.append( (i, s.portstr))
            s.close()   # explicit close 'cause of delayed GC in java
        except serial.SerialException:
            pass
    return available

# Open a serial connection with Linduino
class Linduino:
     
    def __init__(self):
        self.open()
        
    def __del__(self):
        self.close()
        
    def __enter__(self):
        return self
        
    def __exit__(self, a, b, c):
        self.close()

    def open(self):
        print "\nLooking for COM ports ..."
        ports = scan()
        number_of_ports = len(ports)
        print "Available ports: " + str(ports)
        print "\nLooking for Linduino ..." 
        for x in range(0,number_of_ports):
            # Opens the port
            testser = serial.Serial(ports[x][1], 115200, timeout = 0.5) 
            time.sleep(2)   # A delay is needed for the Linduino to reset
            try:
                id_linduino = testser.read(50) # Remove the hello from buffer

                # Get ID string
                testser.write("i") 
                id_linduino = testser.read(50)
                if id_linduino[20:25] == "DC590":
                    Linduino = ports[x][1]
            except:
                pass
            testser.close()
        
        try:
            # Open serial port
            self.port = serial.Serial(Linduino, 115200, timeout = 0.05)
            time.sleep(2)       # A delay is needed for the Linduino to reset
            self.port.read(50)  # Remove the hello from buffer
            print "    Found Linduino!!!!"
        except:
            print "    Linduino was not detected"
        
    def close(self):
        try:
            self.port.close()  # Close serial port
            return 1
        except Exception:
            return 0
            
    def transfer_packets(self, send_packet, return_size = 0):
        try:
            if len(send_packet) > 0:
                self.port.write(send_packet)                       # Send packet
            if return_size > 0:            
                return self.port.read(return_size) # Receive packet
            else:
                return None # return_size of 0 implies send only
        except:
            return 0

###############################################################################
# Function Tests
###############################################################################

if __name__ == "__main__":
    
    
    try:
        linduino = Linduino() # Look for the DC590

        linduino.port.write('i')
        print "\n" + linduino.port.read(50)
        
    finally:
        linduino.close()

    print "Test Complete"  