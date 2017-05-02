# -*- coding: utf-8 -*-
'''
LTC2500_filters.py

This script imports the LTC2500-32 digital filter coefficents and plots the
impulse responses and frequency responses.
It then calculates the "effective noise bandwidth" in two ways, by measuring
the filter's effect on a set of random data, and by direct integration of the
frequency response.

Tested with Python 2.7, Anaconda distribution available from Continuum Analytics,
http://www.continuum.io/

REVISION HISTORY
$Revision: 4255 $
$Date: 2015-10-19 13:09:55 -0700 (Mon, 19 Oct 2015) $

Copyright (c) 2015, Linear Technology Corp.(LTC)
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

The views and conclusions contained in the software and documentation are those
of the authors and should not be interpreted as representing official policies,
either expressed or implied, of Linear Technology Corp.
'''

# Import standard libraries
import numpy as np
from scipy import signal
from matplotlib import pyplot as plt
import time

# Import Linear Lab Tools utility funcitons
import sys
from llt.utils.DC2390_functions import * # Has filter DF, type information
import llt.utils.linear_lab_tools_functions as lltf

start_time = time.time();

# List of DF information
DF_list = [DF4, DF8, DF16, DF32, DF64, DF128, DF256, DF512, DF1k, DF2k, DF4k, DF8k, DF16k]
# List of filter type information
FT_list = [FTSINC1, FTSINC2, FTSINC3, FTSINC4, FTSSINC, FT_FLAT]

FS = 1000000 # Sample rate, for scaling horizontal frequency axis


# Read all filter coefficients into a big 2-d list, calculate corresponding
# magnitude responses, responses in dB. For each of these, the first index
# is the filter type (SINC2, SINC2, SSINC, Flat, etc.),
# the second index represents the DF. For example:
# filters[filter type][downsample factor][tap value]

# Reading files and doing these calculations takes a while. Only need to do once
# if you leave the console open.
read_files = False
#read_files = True

if read_files == True:
    filters          = [[[] for j in xrange(len(DF_list))] for i in xrange(len(FT_list))]
    filt_resp_mag    = [[[] for j in xrange(len(DF_list))] for i in xrange(len(FT_list))]
    filt_resp_mag_db = [[[] for j in xrange(len(DF_list))] for i in xrange(len(FT_list))]
    ftnum = 0 # Handy numerical index
    for ft in FT_list:
        dfnum = 0 # Handy numerical index
        for df in DF_list:
            filename = "../../../common/ltc25xx_filters/" + ft.FT_txt + "_" + df.DF_txt + ".txt" # Construct filename
            filelength = lltf.linecount(filename) # Find out how long it is
            filters[ftnum][dfnum] = np.ndarray(filelength, dtype=float) # Add entry to list
            print ("reading " + str(filelength) + " coefficients from file " + filename)
            with open(filename, 'r') as infile: # Read in coefficients from files
                for i in range(0, filelength):
                    instring = infile.readline()
                    filters[ftnum][dfnum][i] = float(instring)
            filters[ftnum][dfnum] /= sum(filters[ftnum][dfnum]) # Normalize to unity gain
            filt_resp_mag[ftnum][dfnum] = lltf.freqz_by_fft_numpoints(filters[ftnum][dfnum], 2 ** 20) # Calculate magnitude response
            filt_resp_mag_db[ftnum][dfnum] = 20*np.log10(abs(filt_resp_mag[ftnum][dfnum])) # Calculate response in dB
            dfnum += 1
        ftnum += 1
    print ("Done reading in all coefficient files and calculating responses!!")

# Create filter response of Variable-SINC filter, N=2, to represent the simplest
# possible filter. (This mode is distinct from the other filters, no coefficient file.)
vsinc2 = np.ones(2) # Yup, that's it... just a couple of 1s!
vsinc2 /= sum(vsinc2) #Normalize to unity gain
vsinc_resp_mag = lltf.freqz_by_fft_numpoints(vsinc2, 2 ** 20) # Calculate magnitude response
vsinc_resp_mag_db = 20*np.log10(abs(vsinc_resp_mag)) # Calculate response in dB

# Plot the impulse responses on the same horizontal axis, with normalized
# amplitude for a better visual picture...
plt.figure(1)
plt.cla()
plt.ion()
plt.title('SSINC+Flat filters')
for df in range(0, len(DF_list)):
    plt.plot(filters[5][df] / max(filters[5][df]))
plt.xlabel('tap number')
plt.show()


# Make vector of frequencies to plot / save against
haxis = np.linspace(0.0, FS, 2**20) # Horizontal axis

color_list = ["red","orange"]

# Plot frequency response, linear frequency axis
lw = 1.5
plt.figure(2)
plt.cla()
plt.ion()
#plt.cla()
plt.title("LTC2500-32 filter responses (DF " + DF256.DF_txt + ")")
plt.xlabel('Frequency (Hz)')
plt.ylabel('Rejection (dB)')
#plt.axis([0, 16400, -100, 10])
plt.axis([20, 500000, -100, 5])
# All DF256 filters, for section of video comparing all filter types
#plt.semilogx(haxis, filt_resp_mag_db[0][6], linewidth=lw, color="red", zorder=1)
#plt.semilogx(haxis, filt_resp_mag_db[1][6], linewidth=lw, color="orange",  zorder=1)
#plt.semilogx(haxis, filt_resp_mag_db[2][6], linewidth=lw, color="green",  zorder=1)
#plt.semilogx(haxis, filt_resp_mag_db[3][6], linewidth=lw, color="blue",  zorder=1)
#plt.semilogx(haxis, filt_resp_mag_db[4][6], linewidth=lw, color="purple",  zorder=1)
#plt.semilogx(haxis, filt_resp_mag_db[5][6], linewidth=lw, color="black", zorder=1)

# Selection of filters for section of video discussing versatility, compared
# with delta sigma
all_filter_plot = False
if all_filter_plot == True:
    plt.semilogx(haxis, vsinc_resp_mag_db, linewidth=lw, color="red", zorder=1) # Simple average of 2 points
    plt.semilogx(haxis, filt_resp_mag_db[5][6], linewidth=lw, color="black", zorder=1) # Example flat passband filter
    
    for dfnum in [0, 2, 4, 6, 8, 10]:# range(0, 11):# [0, 6, 11]:
        plt.semilogx(haxis[0:2**(24-dfnum)], filt_resp_mag_db[0][dfnum][0:2**(24-dfnum)], linewidth=lw, color="red", zorder=1) # Flat filter, DF4
        plt.semilogx(haxis, filt_resp_mag_db[1][dfnum], linewidth=lw, color="orange",  zorder=1)
        plt.semilogx(haxis, filt_resp_mag_db[2][dfnum], linewidth=lw, color="green",  zorder=1)
        plt.semilogx(haxis, filt_resp_mag_db[3][dfnum], linewidth=lw, color="blue",  zorder=1)
        plt.semilogx(haxis, filt_resp_mag_db[4][dfnum], linewidth=lw, color="purple",  zorder=1)
        plt.semilogx(haxis, filt_resp_mag_db[5][dfnum], linewidth=lw, color="black", zorder=1)

# Spread-sinc filters, for section of video describing increasing DF x 2 corresponding
# to a 3dB improvement in SNR
filter_bw_plot = True
if filter_bw_plot == True:
    ftnum = 4 # SSinc
    lw = 3
    plt.axis([500, 100000, -120, 5])
    plt.semilogx(haxis, filt_resp_mag_db[ftnum][2], linewidth=lw, color="red", zorder=1)
#    plt.semilogx(haxis, filt_resp_mag_db[ftnum][3], linewidth=lw, color="orange", zorder=1)
#    plt.semilogx(haxis, filt_resp_mag_db[ftnum][4], linewidth=lw, color="green", zorder=1)
#    plt.semilogx(haxis, filt_resp_mag_db[ftnum][5], linewidth=lw, color="blue", zorder=1)


print "My program took", (time.time() - start_time), " seconds to run"