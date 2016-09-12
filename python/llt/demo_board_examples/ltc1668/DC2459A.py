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
        The purpose of this module is to use the DC2026C as a SPI interface to
        set the DC2459A frequency out.
"""
###############################################################################
# Libraries
###############################################################################

import sys
sys.path.append('../../utils') 
import connect_to_linduino as duino

###############################################################################
# Functions
###############################################################################

# Send 32 bit SPI data to the DC2459A from the Linduino
def send_raw_code(dc2026, code):
    # Construct the string for the Linduino
    string_data = "GMSxS" + format((code>>24)&0xFF, '02x') + 'S' +\
                  format((code>>16)&0xFF, '02x') + 'S' + \
                  format((code>>8)&0xFF, '02x') + 'S' + \
                  format(code&0xFF, '02x') + 'X'
    dc2026.port.write(string_data)

    
if __name__ == "__main__":
    linduino = duino.Linduino()   
    try:
        print "Command Summary"
        print "    1-Send raw code"
        print "    2-Set frequency"
        print "    3-Exit program"
        user_input = input("Enter a command: ")
        while(user_input != 3):
            if(user_input == 1):
               code = int(input( "Enter raw 32 bit code: "))
               send_raw_code(linduino,code)
            elif (user_input == 2):
                freq = float(input("Enter desired frequency(Hz): "))
                float_code = freq/50000000*(2**32-1)
                send_raw_code(linduino,int(float_code))
            else:
                print "**** Invalid Command ****"
            print "Command Summary"
            print "    1-Send raw code"
            print "    2-Set frequency"
            print "    3-Exit program"
            user_input = input("Enter a command: ")
    finally:
        linduino.close()
    