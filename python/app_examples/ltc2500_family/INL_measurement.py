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
        The purpose of this module is to measure INL for the 2500
"""
###############################################################################
# Libraries
###############################################################################

import visa
import time
import sys # os, socket, ctypes, struct
import numpy as np
from time import sleep
from matplotlib import pyplot as plt
import DC2390_functions as DC2390
import LTC2758
sys.path.append('../../') 
from mem_func_client import MemClient

###############################################################################
# Global Constants
###############################################################################

MASTER_CLOCK = 50000000 
SYSTEM_CLOCK_DIVIDER = 199 # 50MHz / 200 = 250 Ksps
NUM_SAMPLES = 2**17
DAC_VREF = 5.0 # DAC Reference voltage
NUMBER_OF_POINTS = 200


###############################################################################
# Functions
###############################################################################

def hp34401a_lcd_disp(hp_meter, message):
    """
        Displays up to 12 charaters on the hp33401a
    """
    hp34401a.write("DISP:TEXT:CLE")
    hp34401a.write("DISP:TEXT '" + str(message) + "'")

def hp34401a_voltage_read(hp_meter):
    """
        Measures voltage in auto range and auto resolution
    """
    hp_meter.write("MEAS:VOLT:DC? DEF,DEF")    
    return float(hp_meter.read())

def hp34401a_voltage_read_rng_res(hp_meter , v_range, v_resolution):
    """
        Measures voltage with specified range and resolution
    """
    hp_meter.write("MEAS:VOLT:DC? " + str(v_range) + " , " + str(v_resolution))
    return float(hp_meter.read())

def inl_test(client, hp_meter, num_pts, daca_start, daca_end, dacb_start,
             dacb_end, file_name):

    # Variables
    # -------------------------------------------------------------------------    
    hp_data = []
    adc_data = []
    daca_voltage_step = (daca_end - daca_start) / num_pts
    dacb_voltage_step = (dacb_end - dacb_start) / num_pts
    
    # Set the DACs to the start voltages
    code = LTC2758.LTC2758_voltage_to_code(daca_start, DAC_VREF,
                                           LTC2758.LTC2748_UNIPOLAR_0_P5)
    LTC2758.LTC2758_write(client, LTC2758.LTC2748_DAC_A | 
                          LTC2758.LTC2758_WRITE_CODE_UPDATE_ALL, code)
    
    code = LTC2758.LTC2758_voltage_to_code(dacb_start, DAC_VREF, 
                                           LTC2758.LTC2748_UNIPOLAR_0_P5)
    LTC2758.LTC2758_write(client, LTC2758.LTC2748_DAC_B | 
                          LTC2758.LTC2758_WRITE_CODE_UPDATE_ALL, code)
        
    # Run INL Test
    # -------------------------------------------------------------------------
    hp34401a_lcd_disp(hp_meter, "Running Test")
    
    for i in reversed(range(0,num_pts)):
        
        # Set DACs
        dac_a = daca_start + daca_voltage_step * i
        code = LTC2758.LTC2758_voltage_to_code(dac_a, DAC_VREF,
                                               LTC2758.LTC2748_UNIPOLAR_0_P5)
        LTC2758.LTC2758_write(client, LTC2758.LTC2748_DAC_A | 
                              LTC2758.LTC2758_WRITE_CODE_UPDATE_ALL, code)
        
        dac_b = dacb_start + dacb_voltage_step * i
        code = LTC2758.LTC2758_voltage_to_code(dac_b, DAC_VREF,
                                               LTC2758.LTC2748_UNIPOLAR_0_P5)
        LTC2758.LTC2758_write(client, LTC2758.LTC2748_DAC_B | 
                              LTC2758.LTC2758_WRITE_CODE_UPDATE_ALL, code)
        
        time.sleep(0.1)
        
        # Read the Voltage of DACs from HP meter max resloutin 10v range
        v_hp = hp34401a_voltage_read(hp_meter)

        time.sleep(0.1)
        
        # Capture the data
        data = DC2390.capture(client, NUM_SAMPLES, trigger = 0, timeout = 1.0)
        
        hp_data.append(v_hp)
        adc_data.append(np.average(data))
    
    # Save data to file
    # -------------------------------------------------------------------------
    
    hp34401a_lcd_disp(hp_meter, "save 2 file")
    f = open(file_name, "w") # Create the file
    f.write('HP (V),ADC (32-bit code)\n')
    for x in range(len(hp_data)):
        f.write(str(hp_data[x]))
        f.write(",")
        f.write(str(adc_data[x]))
        f.write("\n")
    f.close() # Close the file
    
    hp34401a_lcd_disp(hp_meter, "INL Done")
        
def sampling_rate_sweep(client, hp_meter, dac_vref ,v_min, v_max, file_name):
    """
        Sweeps the sampling rate
    """
    # Variables
    # -------------------------------------------------------------------------
    sample_rate = []
    data1 =[]
    data2 = []
    hp_data1 = []
    hp_data2 = []
    sweep_rate = [10000,50000,100000,200000,300000,400000,500000]
    
    # Run sweep test
    # -------------------------------------------------------------------------
    
    # Display message to the hp34401a
    hp34401a_lcd_disp(hp_meter, "Running Test")
    
    for i in range(len(sweep_rate)):
        clk_div = MASTER_CLOCK/(sweep_rate[i])
        sample_rate.append(sweep_rate[i])
        # Set the clock divider
        client.reg_write(DC2390.SYSTEM_CLOCK_BASE, 0xF5000000 | clk_div)
        time.sleep(.1)
        
         # Set DACs
        code = LTC2758.LTC2758_voltage_to_code(v_min, dac_vref, 
                                               LTC2758.LTC2748_UNIPOLAR_0_P5)
        LTC2758.LTC2758_write(client, LTC2758.LTC2748_DAC_A | 
                              LTC2758.LTC2758_WRITE_CODE_UPDATE_ALL, code)
        
        code = LTC2758.LTC2758_voltage_to_code(v_max, dac_vref, 
                                               LTC2758.LTC2748_UNIPOLAR_0_P5)
        LTC2758.LTC2758_write(client, LTC2758.LTC2748_DAC_B | 
                              LTC2758.LTC2758_WRITE_CODE_UPDATE_ALL, code)
        
        time.sleep(0.1)
        
        # Read the Voltage of DACs from HP meter
        v_hp = hp34401a_voltage_read_rng_res(hp_meter, 10, 1**(-6))
        
        time.sleep(0.1)
        
        # Capture the data
        data = DC2390.capture(client, NUM_SAMPLES, trigger = 0, timeout = 1.0)
        
        hp_data1.append(v_hp)
        data1.append(np.average(data))
        
        # Set DACs
        code = LTC2758.LTC2758_voltage_to_code(v_max, dac_vref, 
                                               LTC2758.LTC2748_UNIPOLAR_0_P5)
        LTC2758.LTC2758_write(client, LTC2758.LTC2748_DAC_A | 
                              LTC2758.LTC2758_WRITE_CODE_UPDATE_ALL, code)
        
        code = LTC2758.LTC2758_voltage_to_code(v_min, dac_vref, 
                                               LTC2758.LTC2748_UNIPOLAR_0_P5)
        LTC2758.LTC2758_write(client, LTC2758.LTC2748_DAC_B | 
                              LTC2758.LTC2758_WRITE_CODE_UPDATE_ALL, code)        
        
        time.sleep(0.1)
        
        # Read the Voltage of DACs from HP meter
        v_hp = hp34401a_voltage_read(hp_meter)
        
        time.sleep(0.1)
        
        # Capture the data
        data = DC2390.capture(client, 2**17, trigger = 0, timeout = 1.0)
        
        hp_data2.append(v_hp)
        data2.append(np.average(data))
    
    # Store the data to a file
    # -------------------------------------------------------------------------
    hp34401a_lcd_disp(hp_meter, "save 2 file")
    
    f = open(file_name, "w") # Create the file
    f.write("Sampling Rate Sweep \n")
    f.write("Sampling rate (Hz),Meter [+],ADC [+],Meter [-],ADC [-]\n")
    for x in range(len(hp_data1)):
        f.write(str(sample_rate[x]))
        f.write(",")
        f.write(str(hp_data1[x]))
        f.write(",")
        f.write(str(data1[x]))
        f.write(",")
        f.write(str(hp_data2[x]))
        f.write(",")
        f.write(str(data2[x]))
        f.write("\n")
    f.close() # Close the file
    
    hp34401a_lcd_disp(hp_meter, "Sweep Done")
    

if __name__ == "__main__": 

    # Keep track of start time
    start_time = time.time()
    
    try:   
        
        # FPGA initialization
        # ---------------------------------------------------------------------
        
        # Get the host from the command line argument. 
        # Can be numeric or hostname.
        HOST = sys.argv[1] if len(sys.argv) == 2 else '127.0.0.1'
    
        # Connect to the SoC 
        client = MemClient(host=HOST)
        
        # Verify the FPGA bistream
        # Read FPGA type and revision
        rev_id = client.reg_read(DC2390.REV_ID_BASE)
        type_id = rev_id & 0x0000FFFF
        rev = (rev_id >> 16) & 0x0000FFFF
        
        if (type_id != 0xABCD) or (rev != 0x1238):
            print "Wrong FPGA bitstream on the FPGA"
            print 'FPGA load type ID: %04X' % type_id
            print 'FPGA load revision: %04X' % rev
        else:
            print "Correct bitstream file found !!"
    
        # Set the LTC695 to 50 MHz
        DC2390.LTC6954_configure(client, 0x04)
        
        # Set the clock divider
        client.reg_write(DC2390.SYSTEM_CLOCK_BASE, 0xF5000000 | 
                         SYSTEM_CLOCK_DIVIDER)
        
        # Set the sample depth
        client.reg_write(DC2390.NUM_SAMPLES_BASE, NUM_SAMPLES)
        
        # Set Mux for raw Nyquist data
        # Set Dac A for SIN and Dac B for LUT
        client.reg_write(DC2390.DATAPATH_CONTROL_BASE, 
                         DC2390.DC2390_FIFO_ADCB_NYQ |
                         DC2390.DC2390_DAC_B_NCO_COS | 
                         DC2390.DC2390_DAC_A_NCO_SIN | 
                         DC2390.DC2390_LUT_ADDR_COUNT | 
                         DC2390.DC2390_LUT_RUN_CONT)
        
        # Configure the LTC2500
        # ---------------------------------------------------------------------
        ltc2500_cfg_led_on  = (((DC2390.LTC2500_DF_64 | 
                                 DC2390.LTC2500_SSINC_FILT)<<6) | 0x03 | 
                                (DC2390.LTC2500_N_FACTOR << 16))
        ltc2500_cfg_led_off = (((DC2390.LTC2500_DF_64 | 
                                 DC2390.LTC2500_SSINC_FILT)<<6) | 
                                (DC2390.LTC2500_N_FACTOR << 16))
        
        client.reg_write(DC2390.LED_BASE, ltc2500_cfg_led_on)
        sleep(0.1)
        client.reg_write(DC2390.LED_BASE, ltc2500_cfg_led_off)
        sleep(0.1)
        
        # Connect to test equipment
        # ---------------------------------------------------------------------
        
        # Connect to visa resource manager
        rm = visa.ResourceManager()
    
        # Connect to the HP multimeter
        hp34401a = rm.open_resource("GPIB0::22::INSTR")
    
        hp34401a.timeout = 5000
    
        hp34401a.write("*CLS")  # Clear the LCD screen
        hp34401a.write("*IDN?") # Read the ID name command for the meter
        print hp34401a.read()   # Display the ID name
        hp34401a_lcd_disp(hp34401a, "Starting Test")
        
        time.sleep(1)
        
        # Start the tests
        # ---------------------------------------------------------------------
        
        #inl_test(client, hp34401a, 100, 2.5, 5.0, "raw_data.csv")
        inl_test(client, hp34401a, NUMBER_OF_POINTS, 5.0, 0, 0, 5.0,
                 "raw_data.csv")
        
        time.sleep(1)
        
        sampling_rate_sweep(client, hp34401a, DAC_VREF ,0.0, 5.0,
                            "sample_sweep.csv")        
        
        hp34401a.close() # Disconnect the meter        
        
    finally:
        
        print "The program took", (time.time() - start_time)/60, "min to run"