# -*- coding: utf-8 -*-
'''
DC2303 / LTC2000 Interface Example
This program demonstrates how to communicate with the LTC2000 demo board through Python.
Examples are provided for generating sinusoidal data from within the program, as well
as writing and reading pattern data from a file.

Board setup is described in Demo Manual 2303. Follow the procedure in this manual, and
verify operation with the LTDACGen software. Once operation is verified, exit LTDACGen
and run this script.

Tested with Python 2.7, Anaconda distribution available from Continuum Analytics,
http://www.continuum.io/

Demo board documentation:
http://www.linear.com/demo/2303
http://www.linear.com/product/LTC2000#demoboards

LTC2000 product page
http://www.linear.com/product/LTC2000


REVISION HISTORY
$Revision: 4259 $
$Date: 2015-10-19 15:58:27 -0700 (Mon, 19 Oct 2015) $

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
import math
# for discoverability we avoid having a separate file with common code, so we
# had to put the Ltc2000 class in one module or the other, we chose the other
# for no particular reason, the Ltc2000 class works with either demo-board
from llt.demo_board_examples.ltc2000.ltc2000_dc2085 import Ltc2000

def ltc2000_dc2303(data, spi_regs, verbose=False):
    with Ltc2000(is_xilinx=True, spi_regs, verbose) as controller:
        controller.send_data(data)
        
if __name__ == '__main__':
    num_cycles = 800  # Number of sine wave cycles over the entire data record
    total_samples = 65536 
    data = total_samples * [0] 

    for i in range(0, total_samples):
        data[i] = int(32000 * math.sin((num_cycles*2*math.pi*i)/total_samples))

    spi_regs = [0x01, 0x00, 0x02, 0x02, 0x03, 0x07, 0x04, 0x0B, 0x05, 0x00, 0x07, 0x00,
               0x08, 0x08, 0x09, 0x20, 0x18, 0x00, 0x19, 0x00, 0x1E, 0x00]
    # to use this function in your own code you would typically do
    # ltc2000_dc303(data, spi_reg)
    ltc2000_dc2303(data, spi_regs, verbose=True)
