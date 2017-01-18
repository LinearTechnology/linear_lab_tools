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
        the LTC2320 demo board through python with the DC890.
"""

import llt.common.dc890 as dc890
import llt.common.functions as funcs
import llt.common.constants as consts
import llt.common.exceptions as errs

def ltc2320_16_dc2395a_a(num_samples, verbose = False, do_plot = False, 
                         do_write_to_file = False):
    with Ltc2320(dc_number = 'DC2395A-A', 
                 num_channels = 8,
                 num_bits = 16,
                 verbose = verbose) as controller:
        # You can call this multiple times with the same controller if you need to
        ch0, ch1, ch2, ch3, ch4, ch5, ch6, ch7 = controller.collect(num_samples, consts.TRIGGER_NONE)

        if do_plot:
            funcs.plot_channels(controller.get_num_bits(), 
                       ch0, ch1, ch2, ch3, ch4, ch5, ch6, ch7,
                       verbose=verbose)
        if do_write_to_file:
            funcs.write_channels_to_file_32_bit("data.txt",
                                       ch0, ch1, ch2, ch3, ch4, ch5, ch6, ch7,
                                       verbose=verbose)
        return ch0, ch1, ch2, ch3, ch4, ch5, ch6, ch7

###############################################################################
# The following code is a little complicated. Just skip to the bottom
# for the sample call.
###############################################################################
class Ltc2320(dc890.Demoboard):
    """
        A DC890 demo board with settings for the LTC2320
    """
    def __init__(self, dc_number, num_channels, num_bits, verbose = False):
        dc890.Demoboard.__init__(self, 
                                 dc_number             = dc_number, 
                                 fpga_load             = 'CMOS',
                                 num_channels          = num_channels,
                                 is_positive_clock     = False, 
                                 num_bits              = num_bits,
                                 alignment             = 32,
                                 is_bipolar            = True,
                                 spi_reg_values        = [], # No SPI registers
                                 verbose               = verbose)
                                 
    def collect(self, num_samples, trigger, timeout = 5, is_randomized = False, 
                is_alternate_bit = False):
        MAX_TOTAL_SAMPLES = 64 * 1024
        if (num_samples * self.num_channels) > MAX_TOTAL_SAMPLES:
            raise ValueError("Num samples must be <= {}".format(
                MAX_TOTAL_SAMPLES/self.num_channels))
        data = dc890.Demoboard.collect(self, 2*num_samples, trigger, timeout, 
                                       is_randomized, is_alternate_bit)
        return data

    def _get_start_sample(self, first_sample):
        channel = first_sample & 0x7
        return channel if channel == 0 else self.num_channels - channel
        
    def _get_data(self, data):
        num_samples = len(data)/2
        start_sample = self._get_start_sample(data[0])
        data = data[start_sample:num_samples+start_sample]
        for i in range(len(data)):
            if data[i] & 0x7 != i % self.num_channels:
                raise errs.HardwareError("Unexpected channel number in metadata")
            data[i] = data[i] >> 16
        return data

    def fix_data(self, raw_data, is_randomized, is_alternate_bit):
        raw_data = self._get_data(raw_data)
        return funcs.fix_data(raw_data, self.num_bits, 16,
                              self.is_bipolar, is_randomized, is_alternate_bit)
    
if __name__ == '__main__':
    NUM_SAMPLES = 8 * 1024
    # to use this function in your own code you would typically do
    # data = ltc2320_16_dc2395a_a(num_samples)
    ltc2320_16_dc2395a_a(NUM_SAMPLES, verbose=True, do_plot=True, do_write_to_file=True)