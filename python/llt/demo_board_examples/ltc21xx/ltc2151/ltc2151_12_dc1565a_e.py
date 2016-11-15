# -*- coding: utf-8 -*-
"""
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
        the LTC2151-12 demo board through python with the DC1371.
"""

import llt.common.dc1371 as dc1371
import llt.common.functions as funcs
import llt.common.constants as consts

def ltc2151_12_dc1565a_e(num_samples, spi_registers, verbose = False, do_plot = False, 
                      do_write_to_file = False):
    with Dc1565aE(spi_registers, verbose) as controller:
        # You can call this multiple times with the same controller if you need to
        ch0 = controller.collect(num_samples, consts.TRIGGER_NONE)
        
        if do_plot:
            funcs.plot_channels(controller.get_num_bits(), 
                                ch0, 
                                verbose=verbose)
        if do_write_to_file:
            funcs.write_channels_to_file_32_bit("data.txt", 
                                                ch0,
                                                 verbose=verbose)
        return ch0

class Dc1565aE(dc1371.Demoboard):
    """
        A DC1371 demo board with settings for the DC1565A-E
    """
    def __init__(self, spi_registers, verbose = False):
        dc1371.Demoboard.__init__(self, 
                                  dc_number      = 'DC1565A-E', 
                                  fpga_load      = 'S2157',
                                  num_channels   = 1,
                                  num_bits       = 12,
                                  alignment      = 16,
                                  is_bipolar     = True,
                                  demo_config    = 0x20000000,
                                  spi_reg_values = spi_registers,
                                  verbose        = verbose)

if __name__ == '__main__':
    NUM_SAMPLES = 32 * 1024
    spi_reg = [ # addr, value
                  0x00, 0x80,
                  0x01, 0x00,
                  0x02, 0x00,
                  0x03, 0x00,
                  0x04, 0x00
              ]
    # to use this function in your own code you would typically do
    # data = ltc2151_12_dc1565a_e(num_samples, spi_reg)
    ltc2151_12_dc1565a_e(NUM_SAMPLES, spi_reg, verbose=True, do_plot=True, do_write_to_file=True)

