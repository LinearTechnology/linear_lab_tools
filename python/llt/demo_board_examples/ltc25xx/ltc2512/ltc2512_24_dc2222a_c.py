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
        the LTC512-24 demo board through python with the DC890.
"""

import llt.common.dc890 as dc890
import llt.common.functions as funcs
import llt.common.constants as consts
import llt.common.exceptions as errs

def ltc2512_24_dc2222a_c(num_samples, df, verify, is_distributed_rd,
                         is_filtered_data, verbose = False, do_plot = False, 
                         do_write_to_file = False):
    with Dc2222aC(df, verify, is_distributed_rd, is_filtered_data, verbose) as controller:
        # You can call this multiple times with the same controller if you need tos
        data, cm_data = controller.collect(num_samples, consts.TRIGGER_NONE)

        # To change the df, verify, and/or distributed read, call the following
        # function before a collect.
        # config_cpld(df, verify, is_distributed_rd)

        if do_plot:
            funcs.plot(controller.get_num_bits(), 
                       data,
                       verbose=verbose)
            
            if cm_data is not None:
                from matplotlib import pyplot as plt
                plt.figure(2)
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
class Dc2222aC(dc890.Demoboard):
    """
        A DC890 demo board with settings for the DC2289A-A
    """
    def __init__(self, df, verify, is_distributed_rd, is_filtered_data, 
                 verbose = False):
        self.df_map = {4: 0, 8: 1, 16: 2, 32: 3}
        if df not in self.df_map:
            raise ValueError("DF must be one of 4, 8, 16, 32")
        dc890.Demoboard.__init__(self, 
                                 dc_number             = 'DC2222A-C', 
                                 fpga_load             = 'CMOS',
                                 num_channels          = 1,
                                 is_positive_clock     = False, 
                                 num_bits              = 24,
                                 alignment             = 32,
                                 is_bipolar            = True,
                                 spi_reg_values        = [], # No SPI registers
                                 verbose               = verbose)
        self.config_cpld(df, verify, is_distributed_rd, is_filtered_data)
        
    def config_cpld(self, df, verify, is_distributed_rd, is_filtered_data):
        if not is_filtered_data and (verify or is_distributed_rd):
            raise errs.NotSupportedError(
                "Verify and distributed read do not work with unfiltered data")
        self.verify = verify
        self.df = df
        self.is_filtered_data = is_filtered_data
        # order of events:
        # 1. Bring down WRTIN_I2C and both chip selects (and verify if needed).
        # 2. Send main config info with SDI1/SCK1.
        # 3. Send variable df if needed with SDI2/SCK2.
        # 4. Bring up CS2.
        # 5. Bring up CS1 and WRTIN_I2C
        # steps two and three can be done in either order.
        
        # Dist. Read: bit 11
        # df code (0-> df 4, 1-> df 8, 2-> df 16, 3-> 32) bits 8:5
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
        df_code = self.df_map[df];        
        if is_filtered_data:
            msb = DIST_READ if is_distributed_rd else 0x00
            lsb = FILTERED | (df_code << 5)
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

    def _get_data_and_check_df(self, data):
        
        # figure out the expected metadata
        df_code = self.df_map[self.df]
        check = ((df_code + 2) << 4) | 0x06
        check_mask = 0x000000FF
        
        # check metadata
        for d in data:
            if (d & check_mask) != check:
                raise errs.HardwareError("Invalid metadata")
                
        return funcs.fix_data([d >> 8 for d in data], 24, 24, True) 
    
    def _get_data_and_common_mode(self, raw_data):
        cm_data = funcs.fix_data(raw_data[:], 8, 8, True)
        cm_data = funcs.uint32_to_int32(cm_data)
        data = funcs.fix_data([int(d >> 18) for d in raw_data], 14, 14, True)
        return data, cm_data
        
    def fix_data(self, raw_data, is_randomized, is_alternate_bit):
        del is_randomized, is_alternate_bit
        cm_data = None
        if self.verify:
            data = self._get_data_and_check_df(raw_data)
        elif self.is_filtered_data:
            data = funcs.fix_data([d >> 8 for d in raw_data], 24, 24, True) 
        else:
            data, cm_data = self._get_data_and_common_mode(raw_data)
        return data, cm_data
    def get_num_bits(self):
            if self.is_filtered_data:
                return self.num_bits
            else:
                return 14
    
if __name__ == '__main__':
    NUM_SAMPLES = 8 * 1024
    df = 4
    # to use this function in your own code you would typically do
    # data = ltc2512_24_dc2222a_c(num_samples, df, verify, is_distributed_rd)
    ltc2512_24_dc2222a_c(NUM_SAMPLES, df, verify=False, is_distributed_rd=False, 
                         is_filtered_data=False, verbose=True, do_plot=True, 
                         do_write_to_file=True)

