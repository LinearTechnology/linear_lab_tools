# -*- coding: utf-8 -*-
"""
    Copyright (c) 2017, Linear Technology Corp.(LTC)
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
        the LTC2372 demo board through python with the DC890.
"""

import llt.common.functions as funcs
import llt.common.constants as consts
import llt.demo_board_examples.ltc23xx.ltc2373.ltc2373_18_dc2071a_a as dc2071

CH_MUX_P0_N1   = (0x0 << 3) | 0x80
CH_MUX_P2_N3   = (0x1 << 3) | 0x80
CH_MUX_P4_N5   = (0x2 << 3) | 0x80
CH_MUX_P6_N7   = (0x3 << 3) | 0x80
CH_MUX_P1_N0   = (0x4 << 3) | 0x80
CH_MUX_P3_N2   = (0x5 << 3) | 0x80
CH_MUX_P5_N4   = (0x6 << 3) | 0x80
CH_MUX_P7_N6   = (0x7 << 3) | 0x80
CH_MUX_P0_NCOM = (0x8 << 3) | 0x80
CH_MUX_P1_NCOM = (0x9 << 3) | 0x80
CH_MUX_P2_NCOM = (0xA << 3) | 0x80
CH_MUX_P3_NCOM = (0xB << 3) | 0x80
CH_MUX_P4_NCOM = (0xC << 3) | 0x80
CH_MUX_P5_NCOM = (0xD << 3) | 0x80
CH_MUX_P6_NCOM = (0xE << 3) | 0x80
CH_MUX_P7_NCOM = (0xF << 3) | 0x80

CH_RANGE_PSEUDO_DIFF_UNI   = 0x0 << 1
CH_RANGE_PSEUDO_DIFF_BIP   = 0x1 << 1
CH_RANGE_FULL_DIFF_BIN     = 0x2 << 1
CH_RANGE_FULL_DIFF_2S_COMP = 0x3 << 1

CH_ENABLE_DGC  = 0x1
CH_DISABLE_DGC = 0x0


def ltc2372_18_dc2071a_b(num_samples, spi_registers, verbose = False, do_plot = False, 
                         do_write_to_file = False):
    with Ltc2372(dc_number = 'DC2071A-B',
                 spi_registers = spi_registers,
                 num_channels = len(spi_registers),
                 num_bits = 18,
                 verbose = verbose) as controller:
        # You can call this multiple times with the same controller if you need to
        data = controller.collect(num_samples, consts.TRIGGER_NONE)

        if do_plot:
            funcs.plot_channels(controller.get_num_bits(), 
                       *data,
                       verbose=verbose)
        if do_write_to_file:
            funcs.write_channels_to_file_32_bit("data.txt",
                                       *data,
                                       verbose=verbose)
        return data

###############################################################################
# The following code is a little complicated. Just skip to the bottom
# for the sample call.
###############################################################################
class Ltc2372(dc2071.Ltc2372):
    """
        A DC890 demo board with settings for the LTC2372
    """
    pass # Same as Ltc2373 class

if __name__ == '__main__':
    NUM_SAMPLES = 8 * 1024
    spi_reg =  [ CH_MUX_P0_N1 | CH_RANGE_FULL_DIFF_2S_COMP | CH_DISABLE_DGC,
                 CH_MUX_P2_N3 | CH_RANGE_FULL_DIFF_2S_COMP | CH_DISABLE_DGC,
                 CH_MUX_P5_N4 | CH_RANGE_FULL_DIFF_2S_COMP | CH_DISABLE_DGC,
                 CH_MUX_P6_N7 | CH_RANGE_FULL_DIFF_2S_COMP | CH_DISABLE_DGC,
               ]
    # to use this function in your own code you would typically do
    # data = ltc2372_16_dc2071a_b(num_samples)
    ltc2372_16_dc2071a_b(NUM_SAMPLES, spi_reg, verbose=True, do_plot=True, do_write_to_file=True)