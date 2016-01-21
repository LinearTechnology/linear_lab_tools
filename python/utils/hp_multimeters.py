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
        The purpose of this module is to interface with hp multimeters 
"""

import visa

def hp34401a_lcd_disp(hp_meter, message):
    """Displays up to 12 charaters on the hp33401a
       hp_meter: the instance of the meter
       message: the 12 charaters to be displayed on the meter
    """
    hp_meter.write("DISP:TEXT:CLE")
    hp_meter.write("DISP:TEXT '" + str(message) + "'")

def hp34401a_read_voltage(hp_meter):
    """Measures voltage in auto range and auto resolution
       returns the voltage in float
       hp_meter: the instance of the meter
    """
    hp_meter.write("MEAS:VOLT:DC? DEF,DEF")    
    return float(hp_meter.read())

def hp34401a_read_voltage_rng_res(hp_meter , v_range, v_resolution):
    """Measures voltage with specified range and resolution
       returns the voltage in float
       hp_meter: the instance of the meter
       v_range: the desired voltage range
       v_resolution: the desired resolution
    """
    hp_meter.write("MEAS:VOLT:DC? " + str(v_range) + " , " + str(v_resolution))
    return float(hp_meter.read())


def hp3458a_lcd_disp(hp_meter, message):
    """Displays up to 16 charaters on the hp2458a
       hp_meter: the instance of the meter
       message: the 16 charaters to be displayed on the meter
    """
    hp_meter.write("DISP 3")
    hp_meter.write("DISP 2 '" + str(message) + "'")
    
def hp3458a_self_test(hp_meter):
    """Starts a self test
       hp_meter: the instance of the meter
    """
    hp_meter.write("TEST")
    
def hp3458a_init(hp_meter):
    """Initializes the meter to DC voltage measurment in the 10V range
       hp_meter: the instance of the meter
    """
    hp_meter.write("RESET")
    hp_meter.write("TARM HOLD")
    hp_meter.write("FUNC DCV") # Set to DC voltage measurment 
    hp_meter.write("RANGE 10") # Set to 10V range
    hp_meter.write("LFREQ LINE") # Measure line freq and set rejection filter
    hp_meter.write("NPLC 1")
    hp_meter.write("AZERO ONCE")
    hp_meter.write("FIXEDZ ON") # Fixed input impedance 
    
def hp3458a_read_voltage(hp_meter):
    """Measures voltage
       returns the voltage in float
       hp_meter: the instance of the meter
    """
    hp_meter.write("TARM SGL")
    return float(hp_meter.read())

def resource_manager():
    """Connect to the resource manager
       returns the visa avalable resources
    """
    return visa.ResourceManager()
    
if __name__ == "__main__":
    # Connect to test equipment
    # ---------------------------------------------------------------------
    
    # Connect to visa resource manager
    rm = resource_manager()
    
    try:
        # Connect to the HP multimeter
        hp3458a = rm.open_resource("GPIB0::22::INSTR", 
                                   read_termination = "\r\n", 
                                   timeout = 50000)
        print hp3458a
        hp3458a_init(hp3458a)
        hp3458a_lcd_disp(hp3458a, "WooHoo!")
        v = hp3458a_read_voltage(hp3458a)
        print v
        
        
    finally:
        hp3458a.close()