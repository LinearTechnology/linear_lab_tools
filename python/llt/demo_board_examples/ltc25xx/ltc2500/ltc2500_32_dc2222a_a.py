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
        the LTC500-32 demo board through python with the DC890.
"""

import llt.common.dc890 as dc890
import llt.common.functions as funcs
import llt.common.constants as consts
import llt.common.exceptions as errs

from matplotlib import pyplot as plt

SINC_1_FILTER     = 0x01
SINC_2_FILTER     = 0x02
SINC_3_FILTER     = 0x03
SINC_4_FILTER     = 0x04
SSINC_FILTER      = 0x05
SSINC_FLAT_FILTER = 0x06
AVERAGING_FILTER  = 0x07

def ltc2500_32_dc2222a_a(num_samples, df, filter_type, enable_dge, enable_dgc, 
                         verify, is_distributed_rd, is_filtered_data, 
                         verbose = False, do_plot = False, do_write_to_file = False):
    with Dc2222aA(df, filter_type, enable_dge, enable_dgc, 
                  verify, is_distributed_rd, is_filtered_data, 
                  verbose) as controller:
        # You can call this multiple times with the same controller if you need tos
        data, cm_data, of_data = controller.collect(num_samples, consts.TRIGGER_NONE)

        # To change the df, verify, and/or distributed read, call the following
        # function before a collect.
        # config_cpld(df, verify, is_distributed_rd)

        if do_plot:
            funcs.plot(controller.get_num_bits(), 
                       data,
                       verbose=verbose)
            
            if cm_data is not None:
                
                plt.figure(2)
                plt.plot(cm_data)
                plt.title('Common Mode Time Domain Samples')
                plt.show()
            if of_data is not None:
                plt.figure(3)
                plt.plot(of_data)
                plt.title('Overflow Bit Time Domain Samples')
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
class Dc2222aA(dc890.Demoboard):
    """
        A DC890 demo board with settings for the DC2289A-A
    """
    def __init__(self, df, filter_type, enable_dge, enable_dgc, 
                 verify, is_distributed_rd, is_filtered_data, 
                 verbose = False):
        self.df_map = {4:2, 8:3, 16:4, 32:5, 64:6, 128:7, 256:8, 512:9, 1024:10,
                        2*1024:11, 4*1024:12, 8*1024:13, 16*1024:14}
        if filter_type != AVERAGING_FILTER:
            if df not in self.df_map :
                raise ValueError("with this filter type, df must be 2^n with 2 <= n <= 14")
        elif df < 1 or df > 16*1024 - 1:
            raise ValueError("with this filter type, df must be between 1 and 16383")
        dc890.Demoboard.__init__(self, 
                                 dc_number             = 'DC2222A-A', 
                                 fpga_load             = 'CMOS',
                                 num_channels          = 1,
                                 is_positive_clock     = False, 
                                 num_bits              = 32,
                                 alignment             = 32,
                                 is_bipolar            = True,
                                 spi_reg_values        = [], # No SPI registers
                                 verbose               = verbose)
        self.config_cpld(df, filter_type, enable_dge, enable_dgc,
                         verify, is_distributed_rd, is_filtered_data)
        
    def collect(self, num_samples, trigger, timeout = 10, is_randomized = False, 
                is_alternate_bit = False):
        if self.verify:
            num_samples *= 2
        data = dc890.Demoboard.collect(self, num_samples, trigger, timeout, 
                                       is_randomized, is_alternate_bit)
        return data

    def config_cpld(self, df, filter_type, enable_dge, enable_dgc, 
                    verify, is_distributed_rd, is_filtered_data):
        if not is_filtered_data and (verify or is_distributed_rd):
            raise errs.NotSupportedError(
                "Verify and distributed read do not work with unfiltered data")
        self.verify = verify
        self.df = df
        self.is_filtered_data = is_filtered_data
        self.filter_type = filter_type
        self.enable_dge = enable_dge
        self.enable_dgc = enable_dgc
        # order of events:
        # 1. Bring down WRTIN_I2C and both chip selects (and verify if needed).
        # 2. Send main config info with SDI1/SCK1.
        # 3. Send variable df if needed with SDI2/SCK2.
        # 4. Bring up CS2.
        # 5. Bring up CS1 and WRTIN_I2C
        # steps two and three can be done in either order.
        
        # Dist. Read: bit 11
        # df code (0-> df 256, 1-> df 1024, 2-> df 4096, 3-> 16384) bits 8:5
        # A/B (0->nyquist data, 1->filtered data) bit 0
        
        # IO expander bit numbers        
        CS1_BIT      = 7
        SDI1_BIT     = 6
        SCK1_BIT     = 5
        N_VERIFY_BIT = 4
        WRITE_IN_BIT = 3
        CS2_BIT      = 2
        SDI2_BIT     = 1
        SCK2_BIT     = 0
        
        # IO expander byte values
        CS1      = 1 << CS1_BIT
        N_VERIFY = 1 << N_VERIFY_BIT
        WRITE_IN = 1 << WRITE_IN_BIT
        CS2      = 1 << CS2_BIT

        DIST_READ = 0x08
        FILTERED  = 0x01
        DGE       = 0x02
        DGC       = 0x04
        df_code = self.df_map[df];        
        if is_filtered_data:
            msb = DIST_READ if is_distributed_rd else 0x00
            if enable_dge:
                msb |= DGE
            if enable_dgc:
                msb |= DGC
            lsb = FILTERED | (df_code << 5) | (filter_type << 1)
        else:
            msb = 0
            lsb = 0
                
        base = 0x00 # bring everything down
        if not verify:
            base |= N_VERIFY
        
        self.controller.dc890_gpio_spi_set_bits(0, SCK1_BIT, SDI1_BIT)
        self.controller.dc890_gpio_set_byte(base)
        
        self.controller.spi_send_no_chip_select([msb, lsb])

        if self.filter_type == AVERAGING_FILTER:
            msb = (self.df >> 8) & 0xFF
            lsb = self.df & 0xFF
            self.controller.dc890_gpio_spi_set_bits(0, SCK2_BIT, SDI2_BIT)
            self.controller.dc890_gpio_set_byte(base)
            
            self.controller.spi_send_no_chip_select([msb, lsb])
        
        base |= CS2        
        self.controller.dc890_gpio_set_byte(base)
        base = base | CS1 | WRITE_IN
        self.controller.dc890_gpio_set_byte(base)

    def _get_data_and_check_df(self, data):
        
        # figure out the expected metadata
        if self.filter_type == AVERAGING_FILTER:
            check = AVERAGING_FILTER << 24
            check |= (self.df - 1) << 10
            check_mask = 0xFFFFC00
        else:
            df_code = self.df_map[self.df]
            check = (df_code << 28) | (self.filter_type << 24)
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
    
    def _get_all_data(self, raw_data):
        cm_data = funcs.fix_data(raw_data[:], 7, 7, True)
        cm_data = funcs.uint32_to_int32(cm_data)
        data = funcs.fix_data([int(d >> 7) for d in raw_data], 24, 24, True)
        overflow = [(d & 0x80000000) != 0 for d in raw_data]        
        return data, cm_data, overflow
        
    def fix_data(self, raw_data, is_randomized, is_alternate_bit):
        del is_randomized, is_alternate_bit
        cm_data = None
        of_data = None
        if self.verify:
            data = self._get_data_and_check_df(raw_data)
        elif self.is_filtered_data:
            data = funcs.uint32_to_int32(raw_data) 
        else:
            data, cm_data, of_data = self._get_all_data(raw_data)
        return data, cm_data, of_data
    def get_num_bits(self):
            if self.is_filtered_data:
                return self.num_bits
            else:
                return 24
    
if __name__ == '__main__':
    NUM_SAMPLES = 8 * 1024
    df = 4
    filter_type = SINC_1_FILTER
    
    # to use this function in your own code you would typically do
    # data = ltc2500_32_dc2222a_a(num_samples, df, verify, is_distributed_rd)
    ltc2500_32_dc2222a_a(NUM_SAMPLES, df, filter_type, enable_dge = False, enable_dgc = False, 
                         verify=True, is_distributed_rd=True, is_filtered_data=True, 
                         verbose=True, do_plot=True, do_write_to_file=True)

