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
        The purpose of this module is consolidate usefull functions
"""
import llt.common.exceptions as err
import llt.common.ltc_controller_comm as comm
import math
import time

def make_vprint(verbose):
    if verbose:
        def vprint(string):
                print string
    else:
        def vprint(string):
                pass
    return vprint

def write_to_file_32_bit(filename, data, verbose = False, append = False):
    vprint = make_vprint(verbose)
    vprint('Writing data to file')
    with open(filename, 'a' if append else 'w') as f:
        for i in range(len(data)):
            f.write(str(data[i]) + '\n')
    vprint('File write done.')

def write_channels_to_file_32_bit(filename, *channels, **verbose_kw):
    vprint = make_vprint(verbose_kw.get("verbose", False))
    vprint('Writing data to file')
    if len(channels) < 1:
        vprint('Nothing to write')
        return
    write_to_file_32_bit(filename, channels[0])
    for channel in channels[1:]:
        write_to_file_32_bit(filename, channel, append=True)
    vprint('File write done.')

def plot(data, num_bits, channel = 0, verbose = False):
    vprint = make_vprint(verbose)
            
    from matplotlib import pyplot as plt
    import numpy as np
    
    vprint("Plotting channel " + str(channel) + " time domain.") 
    
    num_samples = len(data)
    
    plt.figure(2*channel)
    plt.plot(data)
    plt.title('Ch' + str(channel) + ': Time Domain Samples')
    plt.show()
    
    vprint("FFT'ing channel " + str(channel) + " data.") 

    adc_amplitude = 2.0**(num_bits-1)
    
    data_no_dc = data - np.average(data) # Remove DC to avoid leakage when windowing

    normalization = 1.968888        
    a0 = 0.35875
    a1 = 0.48829
    a2 = 0.14128
    a3 = 0.01168
    
    wind = [0 for x in range(num_samples)]
    for i in range(num_samples):
        
        t1 = i / (float(num_samples) - 1.0)
        t2 = 2 * t1
        t3 = 3 * t1
        t1 -= int(t1)
        t2 -= int(t2)
        t3 -= int(t3)
        
        wind[i] = a0 - \
                  a1*math.cos(2*math.pi*t1) + \
                  a2*math.cos(2*math.pi*t2) - \
                  a3*math.cos(2*math.pi*t3)
        
        wind[i] *= normalization;


    windowed_data = data_no_dc * wind# Apply Blackman window
    freq_domain = np.fft.fft(windowed_data)/(num_samples) # FFT
    freq_domain = freq_domain[0:num_samples/2+1]
    freq_domain_magnitude = np.abs(freq_domain) # Extract magnitude
    freq_domain_magnitude[1:num_samples/2] *= 2 
    freq_domain_magnitude_db = 20 * np.log10(freq_domain_magnitude/adc_amplitude)
    
    vprint("Plotting channel " + str(channel) + " frequency domain.")     
    
    plt.figure(2*channel+1)
    plt.title('Ch' + str(channel) + ': FFT')
    plt.plot(freq_domain_magnitude_db)
    plt.show()

def plot_channels(num_bits, *channels, **verbose_kw):
    verbose = verbose_kw.get("verbose", False)
    for channel_num, channel_data in enumerate(channels):
        plot(channel_data, num_bits, channel_num, verbose)
    
def fix_data(data, num_bits, alignment, is_bipolar, is_randomized = False, is_alternate_bit = False):
    if alignment < num_bits:
        raise err.LogicError("Alignment must be >= num_bits ")
    if  alignment > 30:
        raise err.NotSupportedError("Does not support alignment greater than 30 bits")
    shift = alignment - num_bits
    sign_bit = (1 << (num_bits - 1))
    offset = 1 << num_bits
    mask = offset - 1
    
    for i in xrange(len(data)):
        x = data[i]
        x = x >> shift
        if is_randomized and  (x & 1):
            x = x ^ 0x3FFFFFFE;
        if is_alternate_bit:
            x = x ^ 0x2AAAAAAA;
        x = x & mask
        if  is_bipolar and (x & sign_bit):
            x = x - offset
        data[i] = x 
    return data

def scatter_data(data, num_channels):
    if num_channels == 1:
        return data
    temp = []
    for x in range(0,num_channels):
        temp.append(data[x::num_channels])
    return tuple(temp)

def get_controller_info_by_eeprom(controller_type, dc_number, eeprom_id_size, vprint):
    # find demo board with correct ID
    controller_info = None
    vprint('Looking for a controller board')
    info_list = comm.list_controllers(controller_type)
    if info_list is None:
        raise(err.HardwareError('No controller boards found'))
    for info in comm.list_controllers(controller_type):
        with comm.Controller(info) as controller:
            eeprom_id = controller.eeprom_read_string(eeprom_id_size)
            if dc_number in eeprom_id:
                vprint('Found the ' + dc_number + ' demoboard')
                controller_info = info
                break
    if controller_info is None:
        raise(err.HardwareError('Could not find a compatible device'))
    return controller_info

def start_collect(controller_board, num_samples, trigger, timeout = 5):
        controller_board.controller.data_start_collect(num_samples, trigger)
        SLEEP_TIME = 0.2 
        for i in range(int(math.ceil(timeout/SLEEP_TIME))):
            if controller_board.controller.data_is_collect_done():
                return
            time.sleep(SLEEP_TIME)
        raise err.HardwareError('Data collect timed out (missing clock?)')