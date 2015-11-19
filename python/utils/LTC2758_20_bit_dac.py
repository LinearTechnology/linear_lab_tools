# -*- coding: utf-8 -*-
"""
    Created by: Noe Quintero
    E-mail: nquintero@linear.com

    Copyright (c) 2015, Linear Technology Corp.(LTC)
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
        The purpose of this module is to use calibration points for to make a
        20-bit DAC.
"""

import time 
import connect_to_linduino as duino
import Cherry_pick_20bit_dac as ltc2758_comm

class LTC2758_plus:
    """
        An enhanced LTC2758 class used to calculate the needed codes with cal
        constants
    """
    def __init__(self, 
                 offset = 0.0, 
                 main_lsb = 2.65122471323e-05,
                 trim_lsb = -2.07126930721e-07, 
                 meas_bin_weight = [0.0] * 18):
        self.offset = offset
        self.main_lsb = main_lsb
        self.trim_lsb = trim_lsb
        self.meas_bin_weight = meas_bin_weight
    
    def volts_2_code(self, desired_voltage):
        '''
            Returns [Code MAIN DAC, Code Trim DAC]
        '''
        code = (desired_voltage + self.offset) / self.main_lsb 
        
        code = int(round(code)) # Round and convert to integer

        # Limit the range to 18-bits        
        if code > 0x3FFFF:
            code = 0x3FFFF
        elif code < 0:
            code = 0
        

        # Find actual voltage 
        actual_voltage = 0.0
        for x in range(0,18):
            if(code & (1<<x)):
                actual_voltage += self.meas_bin_weight[x]

        residual = desired_voltage - actual_voltage

        # Calculate sub range code
        trim_code = 0x20000 - residual/self.trim_lsb
        trim_code = int(round(trim_code)) # Round and convert to integer
        
        # Limit the range to 18-bits
        if trim_code > 0x3FFFF:
            trim_code = 0x3FFFF
        elif trim_code < 0:
            trim_code = 0
        
        return [code, trim_code]

if __name__ == "__main__":    
    try:
        # Open calibration files
        with open("cal_const.csv") as f:
            data = f.readline().split(',')
            dac_ref = float(data[1])
            data = f.readline().split(',')
            offset = float(data[1])
            data = f.readline().split(',')
            pos_fs_trim = float(data[1])
            data = f.readline().split(',')
            neg_fs_trim = float(data[1])
            f.readline()
            cal_const = []
            for line in f:
                data = line.split(',')
                cal_const.append(float(data[1]))
        
        main_lsb = abs(dac_ref / ((2**18)-1))
        trim_lsb = (pos_fs_trim - neg_fs_trim)*4/((2**18)-1)
        
        ltc2758 = LTC2758_plus(offset = offset, 
                               main_lsb = main_lsb, 
                               trim_lsb = trim_lsb, 
                               meas_bin_weight = cal_const)
        
        linduino = duino.Linduino() # Connect to Linduino
        
        # Set DAC SPAN range
        # ---------------------------------------------------------------------
        ltc2758_comm.LTC2758_set_span(linduino, 
                                      0, 
                                      ltc2758_comm.LTC2758_SPAN_NVREF_2_PVREV_2)
        ltc2758_comm.LTC2758_set_span(linduino, 
                                      1, 
                                      ltc2758_comm.LTC2758_SPAN_0_VREF)
        
        time.sleep(1)
        
        code = ltc2758.volts_2_code(1.234567)
        print hex(code[0])
        print hex(code[1])
        # Set outputs to zero volts     
        ltc2758_comm.LTC2758_set_code(linduino, 0, code[1])#)#0x1FED7)
        ltc2758_comm.LTC2758_set_code(linduino, 1, code[0])
        
        
    finally:
        linduino.close()