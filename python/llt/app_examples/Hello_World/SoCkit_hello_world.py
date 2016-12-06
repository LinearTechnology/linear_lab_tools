#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Blink a light on the SoCkit board!

As simple as this is, it demonstrates a large fraction of the functionality
of the Linear Technology / SoCkit converter evaluation platform. Tested with
FPGA load type 0x0001, which is the basic 32-bit capture engine compatible with
DC2511 and DC2512. It is not necessary to connect either of these boards for this script.

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

import sys # Needed so we can get command line arguments

from time import sleep # So we can make delays that humans can detect
# Okay, now the big one... this is the module that communicates with the SoCkit
from llt.common.mem_func_client_2 import MemClient
from llt.utils.sockit_system_functions import * # More functions for talking to the SoCkit

# Get the host from the command line argument. Can be numeric or hostname.
# If no host given, assume local machine (such as the SoCkit board itself)
HOST = sys.argv[1] if len(sys.argv) == 2 else '127.0.0.1'

# For example, if you're using the default fixed address that the SoCkit assigns
# itself if DHCP fails, you would run:
# python DC2390_hello_world.py "192.168.1.231"

# If you're running this script ON the sockit board itself, you would run:
# python DC2390_hello_world.py


# Now we create an instance of MemClient, called "client", pointing it at
# the SoCkit's IP address. This is the "pipeline" that allows us to communicate.
print('Starting client')
client = MemClient(host=HOST)

# The following routines read and write registers in the FPGA. These can be
# either read or write (or both), depending on the exact design.
# But fundamentally, when reading or writing a register from a script such as
# this one, you are reading or setting the state of a signal in the FPGA design.
# The addresses of the registers we will be talking to are defined in
# sockit_system_functions.py, imported above. If you open it up, you will see these lines:
#
# REV_ID_BASE = 0x10
# LED_BASE = 0x40


# Here, we use the reg_read() function to read the register that contains
# the FPGA bitfile's type and revision. This allows us to keep track of
# lots of projects, and software (such as this script) can verify that it's
# talking to the correct FPGA code. It's a 32-bit wide register, with the type
# in the lower 16-bits and the revision in the upper 16-bits.
# The reg_read takes the register address as the argument, and returns the
# value read out.

# In the FPGA design, this register is an input, with these values hard-coded.
# Other input registers are used to monitor other signals that may change,
# such as the status of an ADC capture.

rev_id = client.reg_read(REV_ID_BASE)   # The line that actually talks to the FPGA
type_id = rev_id & 0x0000FFFF           # Extract the lower 16-bits
rev = (rev_id >> 16) & 0x0000FFFF       # Extract the upper 16-bits.
print ('FPGA load type ID: %04X' % type_id)
print ('FPGA load revision: %04X' % rev)

# Next, we use the reg_write() function to blink a light! LED0 is connected to
# the least significant bit of register 0x40, and writing a "1" will turn the
# light on. reg_write takes the register address as the first argument, and the
# value to write as the second argument.

print ('Okay, now lets blink some lights!!')
for i in range (0, 10):
    client.reg_write(LED_BASE, 0x00000001) # The line that actually talks to the FPGA
    sleep(0.5)
    client.reg_write(LED_BASE, 0x00000000) # The line that actually talks to the FPGA
    sleep(0.5)

# The next section shows how to properly shut down the SoCkit board. It's a
# Linux computer after all, with nonvolatile storage that should be unmounted
# cleanly. Just cutting the power will force a filesystem check (fsck) on the
# next boot. You can either set "choice = 'y'" below, or type
# "client.shutdown()" in the Python console

# What client.shutdown() really does is execute the command:
# "shutdown -h now"
# on the SoCkit board.


choice = 'n'
#choice = raw_input('Shutdown: y/n? ')
if(choice == 'y'):
    print 'Shutting down ...'
#    time.sleep(30)
    client.shutdown()


