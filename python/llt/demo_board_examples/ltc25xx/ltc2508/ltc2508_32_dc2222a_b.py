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
        the LTC508-32 demo board through python with the DC890.
"""

import llt.common.dc890 as dc890
import llt.common.functions as funcs
import llt.common.constants as consts
import llt.common.exceptions as errs

def ltc2508_24_dc2222a_b(num_samples, osr, verify, is_disributed_rd,
                         is_filtered_data, verbose = False, do_plot = False, 
                         do_write_to_file = False):
    with Dc2222aB(osr, verify, is_disributed_rd, verbose) as controller:
        # You can call this multiple times with the same controller if you need tos
        data, cm_data = controller.collect(num_samples, consts.TRIGGER_NONE)

        # To change the OSR, verify, and/or distributed read, call the following
        # function before a collect.
        # config_cpld(osr, verify, is_disributed_rd)

        if do_plot:
            funcs.plot(controller.get_num_bits(), 
                       data,
                       verbose=verbose)
            
            if cm_data is not None:
                from matplotlib import pyplot as plt
                plt.figure(1)
                plt.plot(cm_data)
                plt.title('Common Mode Time Domain Samples')
                plt.show()
        if do_write_to_file:
            funcs.write_to_file_32_bit("data.txt",
                                       data,
                                       verbose=verbose)
            if cm_data is not None:
                funcs.write_to_file_32_bit("cm_data.txt",
                                           cm_data,
                                           verbose=verbose)
        return data

###############################################################################
# The following code is a little complicated due to the nature of the CPLD
# setup. You dont need to pay any attention to it. Just skip to the bottom
# for the sample call.
###############################################################################
class Dc2222aB(dc890.Demoboard):
    """
        A DC890 demo board with settings for the DC2289A-A
    """
    def __init__(self, osr, verify, is_disributed_rd, is_filtered_data, 
                 verbose = False):
        self.osr_dict = {256: 0, 1024: 1, 4096: 2, 16384: 3}
        if osr not in self.osr_dict:
            raise ValueError("OSR must be one of 256, 1024, 4096, 16384")
        dc890.Demoboard.__init__(self, 
                                 dc_number             = 'DC2222A-B', 
                                 fpga_load             = 'CMOS',
                                 num_channels          = 1,
                                 is_positive_clock     = False, 
                                 num_bits              = 32,
                                 alignment             = 32,
                                 is_bipolar            = True,
                                 spi_reg_values        = [], # No SPI registers
                                 verbose               = verbose)
        self.config_cpld(osr, verify, is_disributed_rd, is_filtered_data)
        
    def collect(self, num_samples, trigger, timeout = 5, is_randomized = False, 
                is_alternate_bit = False):
        if self.verify:
            num_samples *= 2
        data = dc890.Demoboard.collect(self, num_samples, trigger, timeout, 
                                       is_randomized, is_alternate_bit)
        return data

    def config_cpld(self, osr, verify, is_disributed_rd, is_filtered_data):
        self.verify = verify
        self.osr = osr
        self.is_filtered_data = is_filtered_data
        # order of events:
        # 1. Bring down WRTIN_I2C and both chip selects (and verify if needed).
        # 2. Send main config info with SDI1/SCK1.
        # 3. Send variable OSR if needed with SDI2/SCK2.
        # 4. Bring up CS2.
        # 5. Bring up CS1 and WRTIN_I2C
        # steps two and three can be done in either order.
        
        # Dist. Read: bit 11
        # OSR code (0-> OSR 256, 1-> OSR 1024, 2-> OSR 4096, 3-> 16384) bits 8:5
        # A/B (0->nyquist data, 1->filtered data) bit 0
        
        # IO expander bit numbers        
        CS1_BIT      = 7
        SDI1_BIT     = 6
        SCK1_BIT     = 5
        N_VERIFY_BIT = 4
        WRITE_IN_BIT = 3
        CS2_BIT      = 2
        # SDI2_BIT     = 1
        # SCK2_BIT     = 0
        
        # IO expander byte values
        CS1      = 1 << CS1_BIT
        N_VERIFY = 1 << N_VERIFY_BIT
        WRITE_IN = 1 << WRITE_IN_BIT
        CS2      = 1 << CS2_BIT

        DIST_READ = 0x08
        FILTERED  = 0x01
        osr_code = self.osr_dict[osr];        
        if is_filtered_data:
            msb = DIST_READ if is_disributed_rd else 0x00
            lsb = FILTERED | (osr_code << 5)
        else:
            msb = 0
            lsb = 0
                
        base = 0x00 # bring everything down
        if not verify:
            base |= N_VERIFY
        
        self.controller.dc890_gpio_spi_set_bits(0, SCK1_BIT, SDI1_BIT)
        self.controller.dc890_gpio_set_byte(base)
        
        self.controller.spi_send_no_chip_select([msb & 0xFF, lsb & 0xFF])

        base |= CS2        
        self.controller.dc890_gpio_set_byte(base)
        base = base | CS1 | WRITE_IN
        self.controller.dc890_gpio_set_byte(base)

    def _get_data_and_check_osr(self, data):
        
        # figure out the expected metadata
        osr_code = self.osr_dict[self.osr]
        check = (((osr_code * 2 + 8) << 4) | 0x05) << 24
        check_mask = 0xFF000000

        # figure out which is data and which is metadata
        data_0 = data[0::2]
        data_1 = data[1::2]
        data = data_0
        meta = data_1
        for d0, d1 in zip(data_0, data_1):
            if (d0 & check_mask) != check:
                # data_0 is the data 
                break
            elif (d1 & check_mask) != check:
                data = data_1
                meta = data_0
                break;
        
        # check metadata
        for m in meta:
            if (m & check_mask) != check:
                raise errs.HardwareError("Invalid metadata")
                
        return funcs.uint32_to_int32(data)
    
    def _get_data_and_common_mode(self, raw_data):
        cm_data = funcs.fix_data(raw_data, 8, True)
        data = funcs.fix_data([d >> 18 for d in raw_data], 8, True)
        return data, cm_data
        
    def fix_data(self, raw_data, is_randomized, is_alternate_bit):
        del is_randomized, is_alternate_bit
        cm_data = None
        if self.verify:
            data = self._get_data_and_check_osr(raw_data)
        elif self.is_filtered_data:
            funcs.uint32_to_int32(raw_data) 
            data = raw_data
        else:
            data, cm_data = self._get_data_and_common_mode(raw_data)
        return data, cm_data
    
if __name__ == '__main__':
    NUM_SAMPLES = 32 * 1024
    OSR = 256
    # to use this function in your own code you would typically do
    # data = ltc2508_24_dc2222a_b(num_samples, osr, verify, is_disributed_rd)
    ltc2508_24_dc2222a_b(NUM_SAMPLES, OSR, verify=False, is_disributed_rd=False, 
                         is_filtered_data=True, verbose=True, do_plot=True, 
                         do_write_to_file=True)

