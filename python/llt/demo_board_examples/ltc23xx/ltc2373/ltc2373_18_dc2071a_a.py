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
        the LTC2373 demo board through python with the DC890.
"""

import llt.common.dc890 as dc890
import llt.common.functions as funcs
import llt.common.constants as consts
import llt.common.exceptions as errs

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


def ltc2373_16_dc2071a_a(num_samples, spi_registers, verbose = False, do_plot = False, 
                         do_write_to_file = False):
    with Ltc2373(dc_number = 'DC2071A-A',
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
class Ltc2373(dc890.Demoboard):
    """
        A DC890 demo board with settings for the LTC2373
    """
    def __init__(self, dc_number, spi_registers, num_channels, num_bits, verbose = False):
        dc890.Demoboard.__init__(self, 
                                 dc_number             = dc_number, 
                                 fpga_load             = 'CMOS',
                                 num_channels          = num_channels,
                                 is_positive_clock     = False, 
                                 num_bits              = num_bits,
                                 alignment             = 32,
                                 is_bipolar            = True,
                                 spi_reg_values        = spi_registers,
                                 verbose               = verbose)
                                 
    def collect(self, num_samples, trigger, timeout = 10, is_randomized = False, 
                is_alternate_bit = False):
        data = dc890.Demoboard.collect(self, 2*num_samples, trigger, timeout, 
                                       is_randomized, is_alternate_bit)
        return data
    
    def set_spi_registers(self, register_values):
        self.spi_reg_values = register_values
        
        # IO expander bit numbers        
        WRITE_IN_2_BIT  = 7
        SDI_BIT         = 6
        SCK_BIT         = 5
        CNV_BIT         = 4
        WRITE_IN_1_BIT  = 3
        #HIGH_SPEED_BIT = 2
        UNUSED_1_BIT    = 1
        UNUSED_0_BIT    = 0
        
        base = (1 << UNUSED_1_BIT) | (1 << UNUSED_0_BIT)

        self.controller.dc890_gpio_spi_set_bits(0, SCK_BIT, SDI_BIT)
        
        for val in self.spi_reg_values:
            if val & 0x80 == 0:
                raise errs.ValueError("Most significant bit must be set.")

            self.controller.dc890_gpio_set_byte(base)
        
            self.controller.spi_send_no_chip_select([val])
        
        base |= 1 << WRITE_IN_2_BIT
        self.controller.dc890_gpio_set_byte(base)
        
        base |= (1 << CNV_BIT) | (1 << WRITE_IN_1_BIT) 
        self.controller.dc890_gpio_set_byte(base)

    def _get_data_subset(self, data):
        seq_len = len(self.spi_reg_values)
        for i in range(seq_len):
            found_start = True
            for j in range(seq_len):
                check_idx = (i+j) % seq_len
                if (data[j]>>1) & 0x7F != self.spi_reg_values[check_idx] & 0x7F:
                    found_start = False
                    break
            if found_start:
                start = 0 if i == 0 else seq_len - i
                return data[start:len(data)/2 + start]
        raise errs.HardwareError("Could not find correct config from data")

    def _check_data(self, data):
        seq_len = len(self.spi_reg_values)
        check_idx = 0
        for d in data:
            if (d >> 1) & 0x7F != self.spi_reg_values[check_idx] & 0x7F:
                raise errs.HardwareError("Detected incorrect config in data")
            check_idx = (check_idx + 1) % seq_len

    def fix_data(self, raw_data, is_randomized, is_alternate_bit):
        raw_data = self._get_data_subset(raw_data)
        self._check_data(raw_data)
        return funcs.fix_data([d >> 14 for d in raw_data], self.num_bits, 18,
                              self.is_bipolar, is_randomized, is_alternate_bit)
    
if __name__ == '__main__':
    NUM_SAMPLES = 8 * 1024
    spi_reg =  [ CH_MUX_P0_N1 | CH_RANGE_FULL_DIFF_2S_COMP | CH_DISABLE_DGC,
                 CH_MUX_P2_N3 | CH_RANGE_FULL_DIFF_2S_COMP | CH_DISABLE_DGC,
                 CH_MUX_P5_N4 | CH_RANGE_FULL_DIFF_2S_COMP | CH_DISABLE_DGC,
                 CH_MUX_P6_N7 | CH_RANGE_FULL_DIFF_2S_COMP | CH_DISABLE_DGC,
               ]
    # to use this function in your own code you would typically do
    # data = ltc2373_16_dc2071a_a(num_samples)
    ltc2373_16_dc2071a_a(NUM_SAMPLES, spi_reg, verbose=True, do_plot=True, do_write_to_file=True)