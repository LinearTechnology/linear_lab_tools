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
        The purpose of this module is to connect to the DC1371 controller
"""


# Import communication library

import llt.common.ltc_controller_comm as comm
import llt.common.functions as funcs
from llt.common.constants import TYPE_DC1371
from llt.common.constants import DC1371_EEPROM_SIZE
import llt.common.exceptions as errs

class Demoboard():
    def __init__(self, dc_number, fpga_load, num_channels, num_bits, alignment, is_bipolar, 
                 demo_config, spi_reg_values = [], verbose = False):
        self.vprint = funcs.make_vprint(verbose)
        self.num_bits = num_bits
        self.alignment = alignment
        self.is_bipolar = is_bipolar
        self.num_channels = num_channels
        self.fpga_load = fpga_load

        controller_info = funcs.get_controller_info_by_eeprom(TYPE_DC1371,
            dc_number, DC1371_EEPROM_SIZE, self.vprint)
        self.controller = comm.Controller(controller_info)
        self._init_controller(demo_config, spi_reg_values)

    # support "with" semantics
    def __enter__(self):
        return self

    # support "with" semantics
    def __exit__(self, vtype, value, traceback):
        del vtype
        del value
        del traceback
        self.controller.cleanup()
        
    def collect(self, num_samples, trigger, timeout = 5, is_randomized = False, 
                is_alternate_bit = False,):
        num_samples = num_samples * self.num_channels
        funcs.start_collect(self, num_samples, trigger, timeout)
        self.vprint('Data collect done.')
        self.vprint('Reading data')
        
        num_bytes, raw_data = self.controller.data_receive_uint16_values(end=num_samples)
        if num_bytes != num_samples * 2:
            raise errs.HardwareError("Didn't get all bytes")
        self.vprint('Data read done')

        data = funcs.fix_data(raw_data,self.num_bits, self.alignment, 
                              self.is_bipolar, is_randomized, is_alternate_bit)
        return funcs.scatter_data(data, self.num_channels)

    def _init_controller(self, demo_config, register_values):
        self.controller.data_set_high_byte_first()
        self.set_spi_registers(register_values)
        # demo-board specific information needed by the DC1371
        self.controller.dc1371_set_demo_config(demo_config)

    def set_spi_registers(self, register_values):
        if register_values != []:
            self.vprint('Updating SPI registers')
            for x in range(0,len(register_values), 2):
                self.controller.spi_send_byte_at_address(register_values[x], register_values[x+1])
        # The DC1371 needs to check for FPGA load after a change in the SPI registers
        if not self.controller.fpga_get_is_loaded(self.fpga_load):
            self.vprint('Loading FPGA')
            self.controller.fpga_load_file(self.fpga_load)
        else:
            self.vprint('FPGA already loaded')

    def get_num_bits(self):
        return self.num_bits
 
class Demoboard2ChipSelects(Demoboard):
    """
        A DC90XX demo board with 2 chip selects
    """

    def set_spi_registers(self, register_values):
        if register_values != []:
            self.vprint('Updating SPI registers')
            self.controller.dc1371_spi_choose_chip_select(1) # First bank of 4 channels
            for x in range(0,len(register_values), 2):
                self.controller.spi_send_byte_at_address(register_values[x], register_values[x+1])
            self.controller.dc1371_spi_choose_chip_select(2) # Second bank of 4 channels
            for x in range(0,len(register_values), 2):
                self.controller.spi_send_byte_at_address(register_values[x], register_values[x+1])
        # The DC1371 needs to check for FPGA load after a change in the SPI registers
        if not self.controller.fpga_get_is_loaded(self.fpga_load):
            self.vprint('Loading FPGA')
            self.controller.fpga_load_file(self.fpga_load)
        else:
            self.vprint('FPGA already loaded')

                