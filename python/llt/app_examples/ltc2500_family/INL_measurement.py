# -*- coding: utf-8 -*-
"""
    INL measurement program for DC2390. LTC2758 demo board must be connected
    to auzilliary QuikEval header, with outputs connected to input of signal
    chain under test.

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

'''
PyVisa is required for this script, open the Anaconda command prompt,
and run the following:

pip install -U pyvisa


'''


import time
import sys # os, socket, ctypes, struct
import numpy as np
from time import sleep
from matplotlib import pyplot as plt
import DC2390_functions as DC2390

from LTC2758 import *
from llt.common.mem_func_client_2 import MemClient

from llt.utils.endpoint_inl import *

###############################################################################
# Global Constants
###############################################################################

MASTER_CLOCK = 50000000 
SYSTEM_CLOCK_DIVIDER = 199 # 50MHz / 200 = 250 Ksps
NUM_SAMPLES = 2**10
DAC_VREF = 5.0 # DAC Reference voltage
NUMBER_OF_POINTS = 129

meter_type = None
#meter_type = 3458
#meter_type = 34401

if meter_type != None:
    import visa
    from hp_multimeters import *
###############################################################################
# Functions
###############################################################################

def vprint(s):
    """Print string only if verbose is on"""
    if verbose:
        print s

def meter_lcd_disp(meter_inst, message):
    if(meter_type == None):
        print("Meter Message: " + message)
    elif(meter_type == 3458):
        hp3458a_lcd_disp(meter_inst, "SwpDone")
    else:
        hp34401a_lcd_disp(meter_inst, "Sweep Done")

#def endpoint_inl(data):
#    inldata = []
#    xmax = len(data) -1
##    data -= np.average(data)
#    slope = (data[xmax] - data[0]) / (xmax - 0.0)# Rise over run
#    intercept = data[xmax] - (slope * xmax)
#    for i in range(0, len(data)):
#        inldata.append(data[i] - (slope * i) + intercept)
#    return inldata
    

def inl_test(client, meter_inst, num_pts, daca_start, daca_end, dacb_start,
             dacb_end, file_name):
    print("Running INL test!")
    # Variables
    # -------------------------------------------------------------------------
    hp_data = []
    adc_data = []
    voltage_data = []
    noise_data = []
    dac_a_data = []
    dac_b_data = []
    daca_voltage_step = (daca_end - daca_start) / num_pts
    dacb_voltage_step = (dacb_end - dacb_start) / num_pts
    
    # Set the DACs to the start voltages
    code = LTC2758_voltage_to_code(daca_start, DAC_VREF,
                                           LTC2748_UNIPOLAR_0_P5)
    LTC2758_write(client, LTC2748_DAC_A | 
                          LTC2758_WRITE_CODE_UPDATE_ALL, code)
    
    code = LTC2758_voltage_to_code(dacb_start, DAC_VREF, 
                                           LTC2748_UNIPOLAR_0_P5)
    LTC2758_write(client, LTC2748_DAC_B | 
                          LTC2758_WRITE_CODE_UPDATE_ALL, code)
        
    # Run INL Test
    # -------------------------------------------------------------------------
    if(meter_type == 3458):
        hp3458a_lcd_disp(meter_inst, "Run Tst")
    elif(meter_type == 34401):
        hp34401a_lcd_disp(meter_inst, "Running Test")
    else:
        print("Running Test")
    
    fig1 = plt.figure()
    plt.subplot(1, 1, 1)
    plt.title("INL Battle! LTC2508 vs. LTC2758")
    mng = plt.get_current_fig_manager()
    mng.window.showMaximized()
    plt.ion()
    
    maxtime = float(NUM_SAMPLES) * float(SYSTEM_CLOCK_DIVIDER + 1)   / float(MASTER_CLOCK)
    print ("Using timeout value of " + str(maxtime))
    
    for i in reversed(range(0,num_pts)):
        print("Point " + str(i + 1) + " of " + str(num_pts))
        # Set DACs
        dac_a = daca_start + daca_voltage_step * i
        codea = LTC2758_voltage_to_code(dac_a, DAC_VREF,
                                               LTC2748_UNIPOLAR_0_P5)
        LTC2758_write(client, LTC2748_DAC_A | 
                              LTC2758_WRITE_CODE_UPDATE_ALL, codea)
        
        dac_b = dacb_start + dacb_voltage_step * i
        codeb = LTC2758_voltage_to_code(dac_b, DAC_VREF,
                                               LTC2748_UNIPOLAR_0_P5)
        LTC2758_write(client, LTC2748_DAC_B | 
                              LTC2758_WRITE_CODE_UPDATE_ALL, codeb)
        
        time.sleep(0.01)
        
        # Read the Voltage of DACs from HP meter max resloutin 10v range
        if(meter_type == 3458):
            v_hp = hp3458a_read_voltage(meter_inst)
        elif(meter_type == 34401):
            v_hp = hp34401a_read_voltage(meter_inst)
        else:
            v_hp = 0.0

        time.sleep(0.01)
        
        # Capture the data
        data = DC2390.uns32_to_signed32(DC2390.capture(client, NUM_SAMPLES, trigger = 0, timeout = maxtime))
        
        hp_data.append(v_hp)
        adc_data.append(np.average(data))
        noise_data.append(np.std(data))
        dac_a_data.append(codea)
        dac_b_data.append(codeb)
        
        adc_voltage = np.average(data) * 10.0 / 2.0**32
        print("Absolute voltage at ADC in: " + str(adc_voltage))
        voltage_data.append(adc_voltage) #Convert to voltage
        inldata = endpoint_inl(voltage_data)
        plt.cla()
        plt.title("INL Battle! LTC2508 vs. LTC2758")
        plt.axis([0,num_pts,-0.000060, 0.000060]) # ([0,num_pts,min(inldata), max(inldata)])
        plt.plot(inldata, marker='o', linestyle='-', color="green")
        plt.show()
        plt.pause(0.0001) #Note this correction

    print("Voltage_data:")
    print(voltage_data)
    print("INL_data:")
    print(inldata)

    
    # Save data to file
    # -------------------------------------------------------------------------
    if(meter_type == 3458):
        hp3458a_lcd_disp(meter_inst, "sav2file")
    elif(meter_type == 34401):
        hp34401a_lcd_disp(meter_inst, "save 2 file")
    else:
        print("Saving to file")

    f = open(file_name, "w") # Create the file
    f.write('HP (V),ADC (32-bit code), RMS Noise (32-bit code), DAC A code, DAC B code\n')
    for x in range(len(hp_data)):
        f.write(str(hp_data[x]))
        f.write(",")
        f.write(str(adc_data[x]))
        f.write(",")
        f.write(str(noise_data[x]))
        f.write(",")
        f.write(str(dac_a_data[x]))
        f.write(",")
        f.write(str(dac_b_data[x]))
        f.write("\n")
    f.write(notes)
    f.write("\n")
    f.close() # Close the file
    
    if(meter_type == 3458):
        hp3458a_lcd_disp(meter_inst, "INLDone")
    elif(meter_type == 34401):
        hp34401a_lcd_disp(meter_inst, "INL Done")
    else:
        print("INL test done")
        
def sampling_rate_sweep(client, meter_inst, dac_vref ,v_min, v_max, file_name):
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
    if(meter_type == 3458):
        hp3458a_lcd_disp(meter_inst, "Run Tst")
    elif(meter_type == 34401):
        hp34401a_lcd_disp(meter_inst, "Running Test")
    else:
        print("Running Test")
    
    for i in range(len(sweep_rate)):
        clk_div = MASTER_CLOCK/(sweep_rate[i])
        sample_rate.append(sweep_rate[i])
        # Set the clock divider
        client.reg_write(DC2390.SYSTEM_CLOCK_BASE, 0xF5000000 | clk_div)
        time.sleep(.1)
        
         # Set DACs
        code = LTC2758_voltage_to_code(v_min, dac_vref, 
                                               LTC2748_UNIPOLAR_0_P5)
        LTC2758_write(client, LTC2748_DAC_A | 
                              LTC2758_WRITE_CODE_UPDATE_ALL, code)
        
        code = LTC2758_voltage_to_code(v_max, dac_vref, 
                                               LTC2748_UNIPOLAR_0_P5)
        LTC2758_write(client, LTC2748_DAC_B | 
                              LTC2758_WRITE_CODE_UPDATE_ALL, code)
        
        time.sleep(0.1)
        
        # Read the Voltage of DACs from HP meter
        if(meter_type == 3458):
            v_hp = hp3458a_read_voltage(meter_inst)
        elif(meter_type == 34401):
            v_hp = hp34401a_voltage_read_rng_res(meter_inst, 10, 1**(-6))
        else:
            v_hp = 0.0
        
        time.sleep(0.1)
        capture_time = 1.0 + (float(NUM_SAMPLES) / float(sweep_rate[i]))
        # Capture the data
        data = DC2390.uns32_to_signed32(DC2390.capture(client, NUM_SAMPLES, trigger = 0, timeout = capture_time))
        
        hp_data1.append(v_hp)
        data1.append(np.average(data))
        
        # Set DACs
        code = LTC2758_voltage_to_code(v_max, dac_vref, 
                                               LTC2748_UNIPOLAR_0_P5)
        LTC2758_write(client, LTC2748_DAC_A | 
                              LTC2758_WRITE_CODE_UPDATE_ALL, code)
        
        code = LTC2758_voltage_to_code(v_min, dac_vref, 
                                               LTC2748_UNIPOLAR_0_P5)
        LTC2758_write(client, LTC2748_DAC_B | 
                              LTC2758_WRITE_CODE_UPDATE_ALL, code)        
        
        time.sleep(0.1)
        
        # Read the Voltage of DACs from HP meter
        if(meter_type == 3458):
            v_hp = hp3458a_read_voltage(meter_inst)
        elif(meter_type == 34401):
            v_hp = hp34401a_read_voltage(meter_inst)
        else:
            v_hp = 0.0
            
        time.sleep(0.1)
        
        # Capture the data
        data = DC2390.uns32_to_signed32(DC2390.capture(client, NUM_SAMPLES, trigger = 0, timeout = capture_time))
        
        hp_data2.append(v_hp)
        data2.append(np.average(data))
    
    # Store the data to a file
    # -------------------------------------------------------------------------
    if(meter_type == 3458):
        hp3458a_lcd_disp(meter_inst, "sav2file")
    elif(meter_type == 34401):
        hp34401a_lcd_disp(meter_inst, "save 2 file")
    else:
        print("Saving to File")
    
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
    
    if(meter_type == 3458):
        hp3458a_lcd_disp(meter_inst, "SwpDone")
    elif(meter_type == 34401):
        hp34401a_lcd_disp(meter_inst, "Sweep Done")
    else:
        print("Sweep done")




notes = """Testing notes string. Second configuration - 10 ohm - 0.47uF output RC
0.047uF - 511 ohm feedback RC."""

    

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
        
        if (type_id != 0xABCD) or (rev < 0x1238):
            print "Wrong FPGA bitstream on the FPGA"

        else:
            print "Correct bitstream file found !!"
        print 'FPGA load type ID: %04X' % type_id
        print 'FPGA load revision: %04X' % rev
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
        
        
        
    
        # Connect to the HP multimeter
        if(meter_type == 3458):
            rm = visa.ResourceManager() # Connect to visa resource manager
            meter_inst = rm.open_resource("GPIB0::22::INSTR", 
                                   read_termination = "\r\n", 
                                   timeout = 50000)
            hp3458a_init(meter_inst)
        elif(meter_type == 34401):
            rm = visa.ResourceManager() # Connect to visa resource manager
            meter_inst = rm.open_resource("GPIB0::22::INSTR")
            meter_inst.timeout = 5000    
            meter_inst.write("*CLS")  # Clear the LCD screen
            meter_inst.write("*IDN?") # Read the ID name command for the meter
            print meter_inst.read()   # Display the ID name
            hp34401a_lcd_disp(meter_inst, "Starting Test")
        else:
            meter_inst = None
            print("Running test without meter...")
            
        time.sleep(1)
        
        # Start the tests
        # ---------------------------------------------------------------------
        
        in_n_start = 5.0
        in_n_end = 0.0
        in_p_start = 0.0
        in_p_end = 5.0
        
        inl_test(client, meter_inst, NUMBER_OF_POINTS, in_p_start, in_p_end,
                 in_n_start, in_n_end, "output_data/raw_data.csv")

        time.sleep(1)

#        sampling_rate_sweep(client, meter_inst, DAC_VREF ,0.0, 5.0,
#                            "output_data/sample_sweep.csv")    
   

        if(meter_type == 3458):
            meter_inst.close()
        elif(meter_type == 34401):
            meter_inst.close() # Disconnect the meter
        else:
            print("No meter to disconnect!")
        
    finally:
        
        print "The program took", (time.time() - start_time)/60, "min to run"