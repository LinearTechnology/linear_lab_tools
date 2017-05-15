# -*- coding: utf-8 -*-
"""
    Plot data saved from DC2390_noise_meas.py program.


    Created by: Mark Thoren
    E-mail: mthoren@linear.com

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
        The purpose of this module is to excersice the LTC25xx for Seismeic 
        Applications
"""



###############################################################################
# Libraries
###############################################################################
import sys
import time
import numpy as np
from time import sleep
from matplotlib import pyplot as plt
import llt.utils.DC2390_functions as DC2390
from llt.common.mem_func_client_2 import MemClient


###############################################################################
# Parameters for running different tests
###############################################################################

SYSTEM_CLOCK_DIVIDER = 99 # 50MHz / 100 = 500 Ksps
NUM_SAMPLES = 2**20
SINC_LEN = 2048
FILTER_TYPE = 1

FIRSTRUN = 1



###############################################################################
# Functions
###############################################################################



if __name__ == "__main__":
    PATH = 'DC2390_noise_meas/'
#    PREFIX = "Filt_gain_31_df_"
    PREFIX = "Filt_gain_18_df_"
    filter_type = 1
    filt_dat_len = 2**12
    nyq_dat_len = 2**20
    vfs = 10.0 # Full-scale voltage, VREF * 2 for LTC25xx family
    samplerate = 500000.0
    bin_width = 2.0 * samplerate / float(nyq_dat_len)
    print("Bin width: " + str(float(bin_width)))
    
    df8_filt = np.concatenate(((np.ones(8)), np.zeros(nyq_dat_len-8)))
    df4k_filt = np.concatenate(((np.ones(4096)), np.zeros(nyq_dat_len-4096)))
    df8_filt_mag = abs(np.fft.fft(df8_filt))
    df8_filt_mag /= df8_filt_mag[0] # Normalize to unity gain at DC
    df4k_filt_mag = abs(np.fft.fft(df4k_filt))
    df4k_filt_mag /= df4k_filt_mag[0] # Normalize to unity gain at DC

    # Keep track of start time
    start_time = time.time();
    

    filt_data_4_in = np.zeros(filt_dat_len, dtype=float)

    ltc2500_noise_fft = np.zeros(nyq_dat_len, dtype=float)
    
    if FIRSTRUN == 1:
        nyq_data_gain_18 = np.zeros(nyq_dat_len, dtype=float) # Read in Nyquist data
        nyq_data_gain_31 = np.zeros(nyq_dat_len, dtype=float)
        nyq_fft_gain_18 = np.zeros(nyq_dat_len, dtype=float) # Read in Nyquist data
        nyq_fft_gain_31 = np.zeros(nyq_dat_len, dtype=float)
        for run in range(0, 16):
            print('Reading Nyquist data, run ' + str(run) + ' from file')
            with open(PATH + 'Nyq_gain_18_run_' + str(run) + '.csv', 'r') as f:
                for i in range(nyq_dat_len):
                    nyq_data_gain_18[i] = float(f.readline())
            nyq_data_gain_18 = nyq_data_gain_18 * (vfs / 2.0**32.0) # Convert to voltage        
            nyq_fft_gain_18 += np.abs(np.fft.fft(nyq_data_gain_18))
        
            with open(PATH + 'Nyq_gain_31_run_' + str(run) + '.csv', 'r') as f:
                for i in range(nyq_dat_len):
                    nyq_data_gain_31[i] = float(f.readline())
            nyq_data_gain_31 = nyq_data_gain_31 * (vfs / 2.0**32.0) # Convert to voltage
            nyq_fft_gain_31 += np.abs(np.fft.fft(nyq_data_gain_31))
            
            #Now make some dummy LTC2500 noise to double-check our noise density math...
            ltc2500_noise = np.random.normal(loc = 0.0, scale = 23e-6, size = nyq_dat_len) #23uVRMS
            ltc2500_noise_fft += np.abs(np.fft.fft(ltc2500_noise))
            
            
        nyq_fft_gain_18 /= (16.0 * float(nyq_dat_len)) # Normalize for fft length, number of runs
        nyq_fft_gain_31 /= (16.0 * float(nyq_dat_len))
        ltc2500_noise_fft /= (16.0 * float(nyq_dat_len))
    
    
        ltc2500_psd = ltc2500_noise_fft / (bin_width**0.5) # First, scale everything properly for
        nyq_psd_gain_18 = nyq_fft_gain_18 / (bin_width**0.5) # two-sided spectrum
        nyq_psd_gain_31 = nyq_fft_gain_31 / (bin_width**0.5)
    
        ltc2500_psd = ltc2500_psd[0:nyq_dat_len/2] * 2.0 # Next, extract first half of spectrum,
        nyq_psd_gain_18 = nyq_psd_gain_18[0:nyq_dat_len/2] * 2.0 # Multiply by 2. Reminder: This
        nyq_psd_gain_31 = nyq_psd_gain_31[0:nyq_dat_len/2] * 2.0 # is only allowable for REAL FFT inputs
    
        psd_filt = np.ones(16) / 16.0 # Make a smoothing filter for PSD plots
        #ltc2500_psd = np.convolve(psd_filt, ltc2500_psd, mode="valid")
        nyq_psd_gain_18 = np.convolve(psd_filt, nyq_psd_gain_18, mode="valid")
        nyq_psd_gain_31 = np.convolve(psd_filt, nyq_psd_gain_31, mode="valid")
    
        rmsnoise = np.std(nyq_data_gain_18)
        print("RMS noise for Nyquist, Gain 18: " + str(rmsnoise))

    DF_TXT = ["4", "8", "16", "32", "64", "128", "256", "512", "1024", "2048", "4096", "8192", "16384"]
    DF_VALS = [4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384]

    filt_data_18 = [[0] * filt_dat_len for i in range(13)] # Array to hold filtered data
    filt_data_31 = [[0] * filt_dat_len for i in range(13)] # Array to hold filtered data

    rms_noise_18 = [0] * 13 #Calculated RMS noise for each DF
    rms_noise_31 = [0] * 13

    # Read filtered data into arrays...
    print('Reading filtered data from files (DF4 to DF16k)')
    for df in range(0, 13):
        with open(PATH + "Filt_gain_18_df_" + DF_TXT[df] + '.csv', 'r') as f:
            for i in range(filt_dat_len):
                point = float(f.readline()) * 10.0 / 2.0**32 # Convert to voltage
                filt_data_18[df][i] = point
        with open(PATH + "Filt_gain_31_df_" + DF_TXT[df] + '.csv', 'r') as f:
            for i in range(filt_dat_len):
                point = float(f.readline()) * 10.0 / 2.0**32 # Convert to voltage
                filt_data_31[df][i] = point
        rms_noise_18[df] = np.std(filt_data_18[df])
        rms_noise_31[df] = np.std(filt_data_31[df])





#        rmsnoise = np.std(filt_data[df])
#        print("RMS noise for DF" + DF_TXT[df] + ": " + str(rmsnoise))

#    print("Calculating theoretical filtered data RMS noise from Nyquist data")
#    for df in range(0, 13):
#        calc_noise = np.std(np.convolve(nyq_data_gain_31, np.ones(DF_VALS[df])/DF_VALS[df], mode='valid'))
#        print("Theoretical noise for DF" + DF_TXT[df] + ": " + str(calc_noise))





#    plot.subplot(3, 1, 3)
#    plot.title('Filtered Data')
#    plot.ylim([-1.5*10**9,2.5*10**9])
#    plot.xlim([0,NUM_SAMPLES/length])
#    plot.plot(data)
    xmin = 0
    xmax = 2**19

    # Display the graphs
    plotnum = 1
    plt.figure(plotnum)    
#    plt.subplot(2, 1, 1)
    plt.title("Gain 19 Data, DF4 - DF16k")
    plt.ylabel('volts')
    plt.plot(filt_data_18[0], color='black')
    plt.plot(filt_data_18[2], color='red')
    plt.plot(filt_data_18[4], color='blue')
    plt.plot(filt_data_18[6], color='yellow')
    plt.plot(filt_data_18[8], color='magenta')
    plt.plot(filt_data_18[10], color='black')
    plt.plot(filt_data_18[12], color='lime')
#    plt.xlim([xmin,xmax])
#    plt.ylim([-2, 8])
#    plt.subplot(2, 1, 2)
#    plt.ylabel('microvolts')
#    plt.plot(nyq_data_120)
#    plt.xlim([xmin,xmax])
#    plt.ylim([-100, 100])
    #plt.tight_layout()
    
    sfactor = 10**9 #Convert to Nanovolts    
    
    plotnum += 1
    plt.figure(plotnum)
    plt.title("PSD, G=19, G=37, and DF8, DF4k filter responses")
    plt.ylabel('nV/rootHz')
    plt.xlabel('Bin number')

    plt.plot(nyq_psd_gain_31 * sfactor)
    plt.plot(nyq_psd_gain_18 * sfactor)
    plt.plot(ltc2500_psd * sfactor)
    plt.plot(df8_filt_mag[0:nyq_dat_len/2] * 0.0000015 * sfactor)
    plt.plot(df4k_filt_mag[0:nyq_dat_len/2] * 0.0000015 * sfactor)
    plt.xlim([0,nyq_dat_len/2])
    plt.ylim([0,1500])

    plt.show()

    
    
    print("RMS noise vs. downsample factor")
    print("DF, G=19 noise, G=37 noise")
    for df in range(0, 13):
        print(str(DF_VALS[df]) + ", " + str(rms_noise_18[df]) + ", " + str(rms_noise_31[df]) )
    
    
    print "The program took", (time.time() - start_time), "seconds  to run"