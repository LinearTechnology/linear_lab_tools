# -*- coding: utf-8 -*-
"""
    E-mail: quikeval@linear.com

    Copyright (c) 2016, Linear Technology Corp.(LTC)
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
        the LTC1606 demo board through python with the DC718.
"""

import llt.common.dc718 as dc718
import llt.common.functions as funcs
import llt.common.constants as consts

def ltc1606_dc1255a_b(num_samples, verbose = False, do_plot = False, 
                      do_write_to_file = False):
    # connect to the DC1255A-B and do a collection
    with Dc1255aB(verbose) as controller:
        # You can call this multiple times with the same controller if you need to
        data = controller.collect(num_samples, consts.TRIGGER_NONE)
        
        if do_plot:
            funcs.plot(data, controller.get_num_bits(), verbose=verbose)
        if do_write_to_file:
            funcs.write_to_file_32_bit("data.txt", data, verbose=verbose)
        return data

class Dc1255aB(dc718.Demoboard):
    """
        A DC718 demo board with settings for the DC1255A-B
    """
    def __init__(self, verbose = False):
        dc718.Demoboard.__init__(self, 
                                 dc_number             = 'DC1255A-B', 
                                 is_positive_clock     = False, 
                                 num_bits              = 16, 
                                 alignment             = 16,
                                 is_bipolar            = True,                                      
                                 verbose               = verbose)

if __name__ == '__main__':
    NUM_SAMPLES = 32 * 1024
    # to use this function in your own code you would typically do
    # data = ltc1606_dc1255a_b(num_samples)
    testdata = ltc1606_dc1255a_b(NUM_SAMPLES, verbose=True, do_plot = True, 
                             do_write_to_file = True)