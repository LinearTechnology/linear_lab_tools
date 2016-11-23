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
        the LTC2261 demo board through python with the DC890.
"""

import llt.common.dc890 as dc890
import llt.common.functions as funcs
import llt.common.constants as consts
import llt.common.exceptions as errs

def ltc2380_24_dc2289a_a(num_samples, osr, verify, is_disributed_rd, 
                         verbose = False, do_plot = False, 
                         do_write_to_file = False):
    with Dc2289aA(osr, verify, is_disributed_rd, verbose) as controller:
        # You can call this multiple times with the same controller if you need to
        data = controller.collect(num_samples, consts.TRIGGER_NONE)

        # To change the OSR, verify, and/or distributed read, call the following
        # function before a collect.
        # config_cpld(osr, verify, is_disributed_rd)

        if do_plot:
            funcs.plot(data,
                       controller.get_num_bits(), 
                       verbose=verbose)
        if do_write_to_file:
            funcs.write_to_file_32_bit("data.txt",
                                                data,
                                                verbose=verbose)
        return data

###############################################################################
# The following code is a little complicated due to the nature of the CPLD
# setup. You dont need to pay any attention to it. Just skip to the bottom
# for the sample call.
###############################################################################
class Dc2289aA(dc890.Demoboard):
    """
        A DC890 demo board with settings for the DC2289A-A
    """
    def __init__(self, osr, verify, is_disributed_rd, verbose = False):
        dc890.Demoboard.__init__(self, 
                                 dc_number             = 'DC2289A-A', 
                                 fpga_load             = 'CMOS',
                                 num_channels          = 1,
                                 is_positive_clock     = False, 
                                 num_bits              = 24,
                                 alignment             = 24,
                                 is_bipolar            = True,
                                 spi_reg_values        = [], # No SPI registers
                                 verbose               = verbose)
        self.config_cpld(osr, verify, is_disributed_rd)
        
    def collect(self, num_samples, trigger, timeout = 5, is_randomized = False, 
                is_alternate_bit = False):
        data = dc890.Demoboard.collect(self, num_samples*2, trigger, timeout, 
                                       is_randomized, is_alternate_bit)
        return data

    def config_cpld(self, osr, verify, is_disributed_rd):
        if verify and is_disributed_rd:
            raise errs.NotSupportedError("Cannot use verify and distributed read")
        if is_disributed_rd and osr < 25:
            raise errs.NotSupportedError("OSR Must be >=25 for distributed read")
        self.verify = verify
        self.osr = osr
        # Bit Map
        # 7 => WRIN (CS)
        # 6 => SDI
        # 5 => SCK
        # 4 => AUX0
        # 3 => AUX1 (Always set)
        # 2 => AUX2 (~Disributed/normal)
        # 1 => Unused
        # 0 => ~VERIFY (~Verify/normal)
        WRITE_IN    = 0x80
        AUX_0       = 0x10
        AUX_1       = 0x08
        AUX_2       = 0x04
        VERIFY_N    = 0x01
        base = AUX_1
        if not is_disributed_rd:
            base |= AUX_2
        if not self.verify:
            base |= VERIFY_N

        # Configure CPLD port
        self.controller.dc890_gpio_spi_set_bits(0, 5, 6)
        
        # Bring everything down to make sure the CPLD is not listening
        self.controller.dc890_gpio_set_byte(0x00)

        self.controller.dc890_gpio_set_byte(base)
        self.controller.spi_send_no_chip_select([(osr>>8) & 0xFF, osr & 0xFF])
        
        # Now pull WRIN high
        self.controller.dc890_gpio_set_byte(base | WRITE_IN)
        
        # Now pull AUX0 high
        self.controller.dc890_gpio_set_byte(base | WRITE_IN | AUX_0)
    
    def _format_data(self, data, meta_data):
        osr_1 = self.osr - 1
        raw_data = [d & 0xFFFFFF for d in data]
        osr = [((d0>>24) & 0xFF) | ((d1>>16) & 0xFF00) for d0, d1 in zip(data, meta_data)]
        for o in osr:
            if o != osr_1:
                raise errs.HardwareError("Invalid OSR data")
        return raw_data

    def _get_data(self, data):
        osr_1 = self.osr - 1        
        data_0 = data[0::2]
        data_1 = data[1::2]
        
        if osr_1 & 0xFF !=  (osr_1 >> 8) & 0xFF: 
            if (data_0[0]>>24) & 0xFF == osr_1 & 0xFF:
                # data_0 is the data
                return self._format_data(data_0, data_1)
            else:
                # data_1 is the data
                return self._format_data(data_1, data_0)
        else:
            for d0, d1 in zip(data_0, data_1):
            
                if d0 & 0xFFFFFF != 0x000000:
                    # data_0 is the data 
                    return self._format_data(data_0, data_1)
                elif d1 & 0xFFFFFF != 0x000000:
                    # data_1 is the data 
                    return self._format_data(data_1, data_0)
            return self._format_data(data_0, data_1) # Data is all zeroes

    def fix_data(self, raw_data, is_randomized, is_alternate_bit):
        if self.verify:
            raw_data = self._get_data(raw_data)
        return funcs.fix_data(raw_data,self.num_bits, self.alignment,
                              self.is_bipolar, is_randomized, is_alternate_bit)
    
if __name__ == '__main__':
    NUM_SAMPLES = 32 * 1024
    OSR = 4
    # to use this function in your own code you would typically do
    # data = ltc2380_24_dc2289a_a(num_samples, osr, verify, is_disributed_rd)
    ltc2380_24_dc2289a_a(NUM_SAMPLES, OSR, verify=False, is_disributed_rd=False, 
                         verbose=True, do_plot=True, do_write_to_file=True)

