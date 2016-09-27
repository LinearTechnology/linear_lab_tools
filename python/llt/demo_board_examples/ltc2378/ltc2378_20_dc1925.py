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
        The purpose of this module is to demonstrate how to communicate with 
        the LTC2378-20 demo board through python with the DC890.
"""

import llt.common.dc890 as dc890
import llt.common.functions as funcs
import llt.common.constants as consts

def ltc2378_20_DC1925(num_samples, verbose = False, do_plot = False, 
                      do_write_to_file = False):
    # connect to the DC2125 and do a collection
    with DC1925(verbose) as controller:
        # You can call this multiple times with the same controller if you need to
        data = controller.collect(num_samples, consts.TRIGGER_NONE)
        
        if do_plot:
            funcs.plot(data)
        if do_write_to_file:
            funcs.write_to_file_32_bit(data, "data.txt")
        return data

class DC1925(dc890.Demoboard):
    """
        A DC890 demo board with settings for the DC1925
    """
    def __init__(self, verbose = False):
        dc890.Demoboard.__init__(self, 
                                      dc_number             = 'DC1925', 
                                      fpga_load             = 'CMOS',
                                      is_multichannel       = True,
                                      is_positive_clock     = True, 
                                      is_high_byte_first    = True,
                                      num_bits              = 20, 
                                      alignment             = 20,
                                      is_bipolar            = True,                                      
                                      verbose               = verbose)

if __name__ == '__main__':
    NUM_SAMPLES = 64 * 1024
    # to use this function in your own code you would typically do
    # data = ltc2378_20_DC1925(num_samples)
    # Valid number of samples are 1024 to 65536 (powers of two)
    testdata = ltc2378_20_DC1925(NUM_SAMPLES, verbose=True, do_plot = True, 
                                 do_write_to_file = True)
