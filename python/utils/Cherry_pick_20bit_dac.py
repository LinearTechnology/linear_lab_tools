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
        The purpose of this module is to measure calibration points for a
        20-bit DAC.
"""
###############################################################################
# Libraries
###############################################################################

import visa
import time 
import connect_to_linduino as duino


LTC2758_SPAN_0_VREF = 0x00
LTC2758_SPAN_NVREF_PVREV = 0x02
LTC2758_SPAN_NVREF_2_PVREV_2 = 0x04
vref_dac = 0.0
AVERAGING = 100 

def LTC2758_set_code(linduino, channel, code):
    linduino.port.write('MS')   # Set Linduino to SPI mode
    linduino.port.write('x')    # CS low
    if(channel == 1):
        linduino.port.write('S72')
    else:
        linduino.port.write('S70')
    # Send DAC code
    temp = (code >> 10) & 0xFF
    linduino.port.write('S' + format(temp,'02x'))
    temp = (code >> 2) & 0xFF
    linduino.port.write('S' + format(temp,'02x'))
    temp = (code << 6) & 0xFF
    linduino.port.write('S' + format(temp,'02x'))
    linduino.port.write('X')    # CS high

def LTC2758_set_span(linduino, channel, span):
    linduino.port.write('MS')   # Set Linduino to SPI mode
    linduino.port.write('x')    # CS low
    if(channel == 1):
        linduino.port.write('S62')
    else:
        linduino.port.write('S60')
    linduino.port.write('S00')
    linduino.port.write('S' + format(span,'02x'))
    linduino.port.write('S00')
    linduino.port.write('X')    # CS high
    
def hp34401a_lcd_disp(hp_meter, message):
    """
        Displays up to 12 charaters on the hp33401a
    """
    hp_meter.write("DISP:TEXT:CLE")
    hp_meter.write("DISP:TEXT '" + str(message) + "'")

def hp34401a_voltage_read(hp_meter):
    """
        Measures voltage in auto range and auto resolution
    """
    hp_meter.write("MEAS:VOLT:DC? DEF,DEF")    
    return float(hp_meter.read())

def set_dac_read_voltage(hp_meter, linduino, channel, code):
    LTC2758_set_code(linduino, channel, code)
    time.sleep(.1)
    return hp34401a_voltage_read(hp_meter)
          
def hp3458a_lcd_disp(hp_meter, message):
    """
        Displays up to 16 charaters on the hp2458a
    """
    hp_meter.write("DISP 3")
    hp_meter.write("DISP 2 '" + str(message) + "'")
    
def hp3458a_self_test(hp_meter):
    hp_meter.write("TEST")
    
def hp3458a_init(hp_meter):
    hp_meter.write("RESET")
    hp_meter.write("TARM HOLD")
    hp_meter.write("FUNC DCV") # Set to DC voltage measurment 
    hp_meter.write("RANGE 10, 1E-6") # Set to 10V range
    hp_meter.write("LFREQ LINE") # Measure line freq and set rejection filter
    hp_meter.write("NPLC 100")
    hp_meter.write("AZERO ON")
    hp_meter.write("FIXEDZ ON") # Fixed input impedance 
    
def hp3458a_read_voltage(hp_meter):
    hp_meter.write("TARM SGL")
    return float(hp_meter.read())
    
    
if __name__ == "__main__":
    
    
    # Connect to test equipment
    # ---------------------------------------------------------------------
    
    # Connect to visa resource manager
    rm = visa.ResourceManager()
    
    # Connect to the HP multimeter
    hp3458a = rm.open_resource("GPIB0::22::INSTR", 
                               read_termination = "\r\n", 
                               timeout = 5000)

    try:

        # Initialize the HP3458A
        hp3458a_init(hp3458a)
   
        hp3458a_lcd_disp(hp3458a, '20-Bit DAC Test')
        
        hp3458a.write("TEMP?")
        print "Internal Temp: " + hp3458a.read()
        
        time.sleep(1)
        
        # Connect to Linduino
        # ---------------------------------------------------------------------
        hp3458a_lcd_disp(hp3458a, "Find Linduino")
        # Connect to Linduino
        linduino = duino.Linduino() # find Linduino
        time.sleep(2)
        hp3458a_lcd_disp(hp3458a, "Found Linduino")
        time.sleep(2)
        
        hp3458a_lcd_disp(hp3458a, "Setting Up DACs")
        # Set DAC SPAN range
        # ---------------------------------------------------------------------
        LTC2758_set_span(linduino, 0, LTC2758_SPAN_NVREF_2_PVREV_2)
        LTC2758_set_span(linduino, 1, LTC2758_SPAN_0_VREF)
        
        hp3458a_lcd_disp(hp3458a, "Set DACs to Zero")
        # Set outputs to zero volts     
        LTC2758_set_code(linduino, 0, 0x20000)
        LTC2758_set_code(linduino, 1, 0x00000)
        
        
        hp3458a_lcd_disp(hp3458a, "Connect to ref")
        raw_input("Connect meter to ref, then hit enter")
        
        # Measure the referance
        for x in range(0,AVERAGING):
            temp = hp3458a_read_voltage(hp3458a)
            vref_dac += temp
            print temp
        vref_dac /= AVERAGING
        print vref_dac
        
        hp3458a_lcd_disp(hp3458a, "Connect to DAC")
        raw_input("Connect meter to Main DAC, then hit enter")
        hp3458a_lcd_disp(hp3458a, "Test in Progress")
        
        zero_dac_trim = 0.0        
        for x in range(0,AVERAGING):
            temp = hp3458a_read_voltage(hp3458a)
            zero_dac_trim += temp
            print temp
        zero_dac_trim /= AVERAGING
        
        
        LTC2758_set_code(linduino, 0, 0x00000)
        time.sleep(.5)
        fs_daca_trim = 0.0        
        for x in range(0,AVERAGING):
            temp = hp3458a_read_voltage(hp3458a)
            fs_daca_trim += temp
            print temp
        fs_daca_trim /= AVERAGING
        
        
        LTC2758_set_code(linduino, 0, 0x3FFFF)
        time.sleep(.5)
        nfs_dac_trim = 0.0        
        for x in range(0,AVERAGING):
            temp = hp3458a_read_voltage(hp3458a)
            nfs_dac_trim += temp
            print temp
        nfs_dac_trim /= AVERAGING
        
        
        
        
#        lsb_trim_dac = (fs_daca_trim - nfs_dac_trim)/(2**18-1)
#        print lsb_trim_dac
        
        LTC2758_set_code(linduino, 0, 0x20000)
        time.sleep(.5)
        main_dac_cal_voltage = []
        for y in range(0,18):
            print y
            main_dac_cal_temp = 0.0
            LTC2758_set_code(linduino, 1, 2**y)
            LTC2758_set_code(linduino, 1, 2**y)
            time.sleep(.5)
            for x in range(0,AVERAGING):
                temp = hp3458a_read_voltage(hp3458a)
                main_dac_cal_temp += temp
                print temp
            main_dac_cal_temp /= AVERAGING
            main_dac_cal_voltage.append(main_dac_cal_temp)
        
        f = open("cal_const.csv", "w") # Create the file
        f.write("DAC Ref (V)," + str(vref_dac) + '\n')
        f.write("zero_trim  (0x20000)," + str(zero_dac_trim) + '\n')
        f.write("FS_trim (0x00000)," + str(fs_daca_trim) + '\n')
        f.write("NFS_trim (0x3FFFF)," + str(nfs_dac_trim) + '\n')
        f.write("Code,Voltage \n")
        for x in range(0,len(main_dac_cal_voltage)):        
            f.write(str(2**x) + "," + str(main_dac_cal_voltage[x]) + '\n' )  
        f.close() # Close the file
        
        hp3458a_lcd_disp(hp3458a, "Test Done")
#        print hp3458a_read_voltage(hp3458a)
#        hp34401a_lcd_disp(hp34401a, "Look at PC")
#        raw_input("Connect meter to DAC A, then hit enter")
#        hp34401a_lcd_disp(hp34401a, "Testing DAC")
#        time.sleep(1)
#        
#        hp_voltage_a = []
#        dac_code_a = []
#        
#        for x in range (0,18):
#            LTC2758_set_code(linduino, 0x00, x)
#            time.sleep(1)
#            hp_voltage_a.append(hp34401a_voltage_read(hp34401a))
#            dac_code_a.append(x)
#
#        f = open("dac_a.csv", "w") # Create the file
#        f.write("DAC A \nDAC code, meter voltage")
#        for x in range(len(hp_voltage_a)):
#            f.write(str(hp_voltage_a[x]))
#        f.close() # Close the file 
#        
#        hp34401a_lcd_disp(hp34401a, "Look at PC")
#        raw_input("Connect meter to DAC B, then hit enter")
#        hp34401a_lcd_disp(hp34401a, "Testing DAC")
#        
#        hp_voltage_b = []
#        dac_code_b = []
#        
#        for x in range (0,18):
#            LTC2758_set_code(linduino, 0x00, x)
#            time.sleep(1)
#            hp_voltage_b.append(hp34401a_voltage_read(hp34401a))
#            dac_code_b.append(x)
#
#        f = open("dac_a.csv", "w") # Create the file
#        f.write("DAC A \nDAC code, meter voltage")
#        for x in range(len(hp_voltage_b)):
#            f.write(str(hp_voltage_b[x]))
#        f.close() # Close the file 
#        
#        hp34401a_lcd_disp(hp34401a, "Test done")
#        raw_input("Hit eneter to end")
#               
    finally:
        linduino.close()
#        hp3458a.close() # Disconnect the meter
    
    

