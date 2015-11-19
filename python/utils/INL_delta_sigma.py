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
        The purpose of this module is to perform a INL sweep for LTC Mixed
        Signal design team. Specifically, a Delat Sigma 
"""

###############################################################################
# Libraries
###############################################################################

import connect_to_linduino as duino
import LTC2758_20_bit_dac as LTC2758
import time
import visa
import Cherry_pick_20bit_dac as ltc2758_comm
###############################################################################
# Constants
###############################################################################
ADC_FS = 2.048
ADC_BIT_RES = 2**16 - 1
AVERAGE = 10

def set_dac_voltage(linduino, ltc2758, voltage):
    code = ltc2758.volts_2_code(voltage)
    # Set outputs to zero volts     
    ltc2758_comm.LTC2758_set_code(linduino, 0, code[1])
    ltc2758_comm.LTC2758_set_code(linduino, 1, code[0])

def init_LTC4284(linduino):
    linduino.port.write("MI")
    linduino.port.write("sS2AS85S08p")

def read_LTC4284(linduino):
    # Initiate a snap shot
    timeout = 1000
    count = 0
    linduino.port.write("sS2AS85S08p")
    time.sleep(.1)
    # Poll reg 01 for EOC
    reg_01 = 0x00    
    while (reg_01 & 0x08) != 0x08:    
        linduino.port.write("sS2AS01sS2BRp")
        reg_01 = int(linduino.port.read(10),16)
        time.sleep(.1)
        count += 1
        if(count > timeout):
            return (-1)
    linduino.port.write("sS2AS4AsS2BQRp")
    return int(linduino.port.read(10), 16)
    
    
if __name__ == "__main__":
    # Connect to test equipment
    # ---------------------------------------------------------------------
    
    # Connect to visa resource manager
    rm = visa.ResourceManager()
        
   
    try:
        # Connect to the HP multimeter
        hp3458a = rm.open_resource("GPIB0::22::INSTR", 
                                   read_termination = "\r\n", 
                                   timeout = 5000)
                                       
        ltc2758_comm.hp3458a_init(hp3458a)
        
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
            trim_lsb = (pos_fs_trim - neg_fs_trim)/((2**18)-1)
            
            ltc2758 = LTC2758.LTC2758_plus(offset = offset,
                                           main_lsb = main_lsb, 
                                           trim_lsb = trim_lsb, 
                                           meas_bin_weight = cal_const)
                                           
            linduino2 = duino.Linduino()
            linduino = duino.Linduino()
            
            # Set DAC SPAN range
            # ---------------------------------------------------------------------
            ltc2758_comm.LTC2758_set_span(linduino, 
                                          0, 
                                          ltc2758_comm.LTC2758_SPAN_NVREF_2_PVREV_2)
            ltc2758_comm.LTC2758_set_span(linduino, 
                                          1, 
                                          ltc2758_comm.LTC2758_SPAN_0_VREF)
            
            time.sleep(1)
            
            ltc2758_comm.hp3458a_lcd_disp(hp3458a,"Test in Progress")
            
            init_LTC4284(linduino2)
            
            adc_data = 0
            dac_voltage = 0.0015
            adc_transition = []
            adc_code = []
            while adc_data == 0:
                set_dac_voltage(linduino, ltc2758, dac_voltage)
                adc_data = read_LTC4284(linduino2)
                print "ADC data = " + hex(adc_data)
                dac_voltage += ADC_FS/(ADC_BIT_RES * 10)
            
            flag = 0
            temp = 0.0
            for x in range(0,AVERAGE):
                temp += ltc2758_comm.hp3458a_read_voltage(hp3458a)
            adc_transition.append(temp/AVERAGE)
            adc_code.append(adc_data)
            pre_adc_data = adc_data
            
            while adc_data < ADC_BIT_RES:
#                dac_voltage += ADC_FS/(ADC_BIT_RES)*.25
                dac_voltage += ADC_FS/(ADC_BIT_RES * 20)
            
                set_dac_voltage(linduino, ltc2758, dac_voltage)
                adc_data = read_LTC4284(linduino2)
                print "ADC data = " + hex(adc_data)
                
                temp = 0.0
                for x in range(0,AVERAGE):
                    temp += ltc2758_comm.hp3458a_read_voltage(hp3458a)
                adc_transition.append(temp/AVERAGE)
                adc_code.append(adc_data)
                
            f = open("ltc4284_transition_test.csv", "w") # Create the file
            f.write("ADC code,voltage(hp3458A)\n")
            for x in range(0,len(adc_transition)):
                f.write(str(adc_code[x]) + ',' + str(adc_transition[x]))
            f.close() # Close the file
            
        finally:
            hp3458a.close()
            linduino.close() 
            linduino2.close()
#    except Exception:
#        print Exception.message
    finally:
        pass


