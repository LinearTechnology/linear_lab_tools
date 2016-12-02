# -*- coding: utf-8 -*-
"""
    E-mail: quikeval@linear.com

    Copyright (c) ?year?, Linear Technology Corp.(LTC)
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
        the LTC2000 demo board through python with the Altera Stratix IV GX 
        FPGA Development Kit.
"""
import llt.common.ltc_controller_comm as comm
import llt.common.constants as consts
import llt.common.functions as funcs
import llt.common.exceptions as errs
import math
import time

def ltc2000_dc2085(data, spi_regs, verbose=False):
    with Ltc2000(False, spi_regs, verbose) as controller:
        controller.send_data(data)

class Ltc2000():
    _SIZE_DICTIONARY = {16*1024: 0x00, 32*1024: 0x10, 64*1024: 0x20, 128*1024: 0x30,
                        256*1024: 0x40, 512*1024: 0x50, 1024*1024: 0x60, 2*1024*1024: 0x70,
                        4*1024*1024: 0x80, 8*1024*1024: 0x90, 16*1024*1024: 0xA0,
                        32*1024*1024: 0xB0, 64*1024*1024: 0xC0, 128*1024*1024: 0xD0,
                        256*1024*1024: 0xE0, 512*1024*1024: 0xF0}
    _FPGA_ID_REG = 0x00
    _FPGA_CONTROL_REG = 0x01
    _FPGA_STATUS_REG = 0x02
    _FPGA_DAC_PD = 0x03
    
    def __init__(self, is_xilinx, spi_reg_values, verbose = False):
        if is_xilinx:
            self.expected_description = "LTC Communication Interface"
            self.expected_id = 0x20
            self.expected_pll_status = 0x06
            self.expected_max_val = 2 * 1024 * 1024
            self.range_string = "16K to 2M"
            self.is_little_endian = True;
        else:
            self.expected_description = "LTC2000"
            self.expected_id = 0x1A
            self.expected_pll_status = 0x47
            self.expected_max_val = 512 * 1024 * 1024
            self.range_string = "16K to 512M"
            self.is_little_endian = False;
        self.vprint = funcs.make_vprint(verbose)
        self._connect()
        self._init_controller(spi_reg_values)

    # support "with" semantics
    def __enter__(self):
        return self

    # support "with" semantics
    def __exit__(self, vtype, value, traceback):
        del vtype
        del value
        del traceback
        self.controller.close()
        self.controller.cleanup()

    def _connect(self):
        # Open communication to the demo board
        self.vprint("Looking for Controller")
        for info in comm.list_controllers(consts.TYPE_HIGH_SPEED):
            description = info.get_description()
            if self.expected_description in description:
                self.vprint("Found a possible setup")
                self.controller = comm.Controller(info)
                return
        raise(errs.HardwareError('Could not find a compatible device'))
    
    def _init_controller(self, spi_reg_values):
        self.controller.hs_set_bit_mode(consts.HS_BIT_MODE_MPSSE)
        self.controller.hs_fpga_toggle_reset()
        # Read FPGA ID register
        id = self.controller.hs_fpga_read_data_at_address(Ltc2000._FPGA_ID_REG)
        self.vprint("FPGA Load ID: 0x{:04X}".format(id))
        if self.expected_id != id:
            raise(errs.HardwareError('Wrong FPGA Load'))
        self.controller.hs_fpga_write_data_at_address(Ltc2000._FPGA_DAC_PD, 0x01)
        self.set_spi_registers(spi_reg_values)

    def set_spi_registers(self, register_values):
        self.vprint("Configuring ADC over SPI")
        if register_values != []:
            for x in range(0,len(register_values), 2):
                self.controller.spi_send_byte_at_address(register_values[x], register_values[x+1])

    def send_data(self, data):
        num_samples = len(data)                  
        num_samples_reg_value = Ltc2000._SIZE_DICTIONARY.get(num_samples)
        if num_samples > self.expected_max_val or num_samples_reg_value is None:
            raise(errs.NotSupportedError(
                "Data Length Not Supported (Must be a power of 2 between " + self.range_string))
        
        self.vprint("Reading PLL status")
        pll_status = self.controller.hs_fpga_read_data_at_address(Ltc2000._FPGA_STATUS_REG)        
        if self.expected_pll_status != pll_status:
            raise(errs.HardwareError('FPGA PLL status was bad'))
        self.vprint("PLL status is okay")
        time.sleep(0.1)
        self.controller.hs_fpga_write_data_at_address(Ltc2000._FPGA_CONTROL_REG, num_samples_reg_value)
        if self.is_little_endian:
            self.controller.data_set_low_byte_first()
        else:
            self.controller.data_set_high_byte_first()
        
        self.controller.hs_set_bit_mode(consts.HS_BIT_MODE_FIFO)
        self.vprint("Sending data")
        num_bytes_sent = self.controller.data_send_uint16_values(data)
        self.controller.hs_set_bit_mode(consts.HS_BIT_MODE_MPSSE)
        if num_bytes_sent != num_samples * 2:
            raise(errs.HardwareError("Not all data was sent."))
        self.vprint("All data was sent (" + str(num_bytes_sent) + " bytes)")

if __name__ == '__main__':
    num_cycles = 800  # Number of sine wave cycles over the entire data record
    total_samples = 64 * 1024 
    data = total_samples * [0] 

    for i in range(0, total_samples):
        data[i] = int(32000 * math.sin((num_cycles*2*math.pi*i)/total_samples))

    spi_regs = [ # addr, value
                   0x01, 0x00, 
                   0x02, 0x02, 
                   0x03, 0x07, 
                   0x04, 0x0B, 
                   0x05, 0x00, 
                   0x07, 0x00,
                   0x08, 0x08, 
                   0x09, 0x20, 
                   0x18, 0x00, 
                   0x19, 0x00,
                   0x1E, 0x00
               ]
    # to use this function in your own code you would typically do
    # ltc2000_dc2085(data, spi_reg)
    ltc2000_dc2085(data, spi_regs, verbose=True)
