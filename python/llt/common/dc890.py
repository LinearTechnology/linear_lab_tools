# -*- coding: utf-8 -*-
"""
    Created by: Noe Quintero
    E-mail: nquintero@linear.com

    REVISION HISTORY
    $Revision: 2583 $
    $Date: 2014-06-27 17:21:46 -0700 (Fri, 27 Jun 2014) $
    
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
        The purpose of this module is to connect to the DC890 controller
"""


# Import communication library

import llt.common.ltc_controller_comm as comm
import llt.common.functions as funcs
from llt.common.constants import TYPE_DC890
from llt.common.constants import DC890_EEPROM_SIZE
import llt.common.exceptions as errs

class Demoboard():
    def __init__(self, dc_number, fpga_load, num_channels, is_positive_clock, 
                 num_bits, alignment, is_bipolar, spi_reg_values = [], verbose = False):
        self.vprint = funcs.make_vprint(verbose)
        self.num_bits = num_bits
        self.alignment = alignment
        self.is_bipolar = is_bipolar
        self.num_channels = num_channels
        if alignment > 16:
            self.bytes_per_sample = 4
        else:
            self.bytes_per_sample = 2
        controller_info = funcs.get_controller_info_by_eeprom(TYPE_DC890,
            dc_number, DC890_EEPROM_SIZE, self.vprint)
        self.controller = comm.Controller(controller_info)
        is_multichannel = num_channels > 1
        self.init_controller(fpga_load, is_multichannel, is_positive_clock)
        self.set_spi_registers(spi_reg_values)

    # support "with" semantics
    def __enter__(self):
        return self

    # support "with" semantics
    def __exit__(self, vtype, value, traceback):
        del vtype
        del value
        del traceback
        self.controller.cleanup()

    def fix_data(self, raw_data, is_randomized, is_alternate_bit):
        return funcs.fix_data(raw_data, self.num_bits, self.alignment, 
                              self.is_bipolar, is_randomized, is_alternate_bit)
    
    def collect(self, num_samples, trigger, timeout = 5, is_randomized = False, 
                is_alternate_bit = False):
        self.controller.dc890_flush()
        num_samples *= self.num_channels
        funcs.start_collect(self, num_samples, trigger, timeout)
        self.vprint('Data collect done.')
        self.controller.dc890_flush()
        self.vprint('Reading data')
        if self.bytes_per_sample == 2:
            num_bytes, raw_data = self.controller.data_receive_uint16_values(end=num_samples)
            if num_bytes != num_samples * 2:
                raise errs.HardwareError("Didn't get all bytes")
        else:
            num_bytes, raw_data = self.controller.data_receive_uint32_values(end=num_samples)
            if num_bytes != num_samples * 4:
                raise errs.HardwareError("Didn't get all bytes")
        self.vprint('Data read done')

        data = funcs.fix_data(raw_data,self.num_bits, self.alignment, 
                              self.is_bipolar, is_randomized, is_alternate_bit)
        return funcs.scatter_data(data, self.num_channels)

    def init_controller(self, fpga_load, is_multichannel, is_positive_clock):
        if not self.controller.fpga_get_is_loaded(fpga_load):
            self.vprint('Loading FPGA')
            self.controller.fpga_load_file(fpga_load)
        else:
            self.vprint('FPGA already loaded')
        self.controller.data_set_high_byte_first()
        self.controller.data_set_characteristics(is_multichannel, self.bytes_per_sample, is_positive_clock)
 
    def set_spi_registers(self, register_values):
        if register_values != []:
            self.controller.dc890_gpio_set_byte(0xf0)
            self.controller.dc890_gpio_spi_set_bits(3,0,1)
            for x in range(0,len(register_values), 2):
                self.controller.spi_send_byte_at_address(register_values[x], register_values[x+1])
            self.controller.dc890_gpio_set_byte(0xff)
            
    def get_num_bits(self):
        return self.num_bits
