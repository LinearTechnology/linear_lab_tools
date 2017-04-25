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

# Select downsample factor - DF4 to DF16384 (powers of 2)
# 4, 8, 16, 32 correspond to the LTC2512 (Flat passband filter type)
# 256, 1024, 4096, 16384 correspond to the LTC2508 (SSinc filter type)

DF_info = DF256

# List of filter type information
FT_list = [FTSINC1, FTSINC2, FTSINC3, FTSINC4, FTSSINC, FT_FLAT]

# UN-comment one to Select filter type.
#FT_info = Filt_Type_information.FTSINC1
#FT_info = Filt_Type_information.FTSINC2
#FT_info = Filt_Type_information.FTSINC3
#FT_info = Filt_Type_information.FTSINC4
FT_info = FTSSINC
#FT_info = Filt_Type_information.FT_FLAT

FS = 1000000 # Sample rate, for scaling horizontal axis

start_time = time.time();

# Sort of messy to read one by one, but each filter has a different length...

filename = "../../../common/ltc25xx_filters/" + FTSINC1.FT_txt + "_" + DF_info.DF_txt + ".txt"
filelength = lltf.linecount(filename)
filt_sinc1 = np.ndarray(filelength, dtype=float)
print ("reading " + str(filelength) + " coefficients from file " + filename)
# Read in coefficients from files
with open(filename, 'r') as infile:
    for i in range(0, filelength):
        instring = infile.readline()
        filt_sinc1[i] = float(instring)
print("done reading filter coefficients for " + FTSINC1.FT_txt + "!")

filename = "../../../common/ltc25xx_filters/" + FTSINC2.FT_txt + "_" + DF_info.DF_txt + ".txt"
filelength = lltf.linecount(filename)
filt_sinc2 = np.ndarray(filelength, dtype=float)
print ("reading " + str(filelength) + " coefficients from file " + filename)
# Read in coefficients from files
with open(filename, 'r') as infile:
    for i in range(0, filelength):
        instring = infile.readline()
        filt_sinc2[i] = float(instring)
print("done reading filter coefficients for " + FTSINC2.FT_txt + "!")

filename = "../../../common/ltc25xx_filters/" + FTSINC3.FT_txt + "_" + DF_info.DF_txt + ".txt"
filelength = lltf.linecount(filename)
filt_sinc3 = np.ndarray(filelength, dtype=float)
print ("reading " + str(filelength) + " coefficients from file " + filename)
# Read in coefficients from files
with open(filename, 'r') as infile:
    for i in range(0, filelength):
        instring = infile.readline()
        filt_sinc3[i] = float(instring)
print("done reading filter coefficients for " + FTSINC3.FT_txt + "!")

filename = "../../../common/ltc25xx_filters/" + FTSINC4.FT_txt + "_" + DF_info.DF_txt + ".txt"
filelength = lltf.linecount(filename)
filt_sinc4 = np.ndarray(filelength, dtype=float)
print ("reading " + str(filelength) + " coefficients from file " + filename)
# Read in coefficients from files
with open(filename, 'r') as infile:
    for i in range(0, filelength):
        instring = infile.readline()
        filt_sinc4[i] = float(instring)
print("done reading filter coefficients for " + FTSINC4.FT_txt + "!")

filename = "../../../common/ltc25xx_filters/" + FTSSINC.FT_txt + "_" + DF_info.DF_txt + ".txt"
filelength = lltf.linecount(filename)
filt_ssinc = np.ndarray(filelength, dtype=float)
print ("reading " + str(filelength) + " coefficients from file " + filename)
# Read in coefficients from files
with open(filename, 'r') as infile:
    for i in range(0, filelength):
        instring = infile.readline()
        filt_ssinc[i] = float(instring)
print("done reading filter coefficients for " + FTSSINC.FT_txt + "!")

filename = "../../../common/ltc25xx_filters/" + FT_FLAT.FT_txt + "_" + DF_info.DF_txt + ".txt"
filelength = lltf.linecount(filename)
filt_flat = np.ndarray(filelength, dtype=float)
print ("reading " + str(filelength) + " coefficients from file " + filename)
# Read in coefficients from files
with open(filename, 'r') as infile:
    for i in range(0, filelength):
        instring = infile.readline()
        filt_flat[i] = float(instring)
print("done reading filter coefficients for " + FT_FLAT.FT_txt + "!")




filt_sinc1 /= sum(filt_sinc1) #Normalize to unity gain
filt_sinc2 /= sum(filt_sinc2) #Normalize to unity gain
filt_sinc3 /= sum(filt_sinc3) #Normalize to unity gain
filt_sinc4 /= sum(filt_sinc4) #Normalize to unity gain
filt_ssinc /= sum(filt_ssinc) #Normalize to unity gain
filt_flat /= sum(filt_flat) #Normalize to unity gain
print("Done normalizing!")

# Plot the impulse responses on the same horizontal axis, with normalized
# amplitude for a better visual picture...
plt.figure(1)
plt.title('impulse responses')
plt.plot(filt_sinc1 / max(filt_sinc1))
plt.plot(filt_sinc2 / max(filt_sinc2))
plt.plot(filt_sinc3 / max(filt_sinc3))
plt.plot(filt_sinc4 / max(filt_sinc4))
plt.plot(filt_ssinc / max(filt_ssinc))
plt.plot(filt_flat / max(filt_flat))
plt.xlabel('tap number')
plt.show()

filt_sinc1_resp_mag = lltf.freqz_by_fft_numpoints(filt_sinc1, 2 ** 20)
filt_sinc2_resp_mag = lltf.freqz_by_fft_numpoints(filt_sinc2, 2 ** 20)
filt_sinc3_resp_mag = lltf.freqz_by_fft_numpoints(filt_sinc3, 2 ** 20)
filt_sinc4_resp_mag = lltf.freqz_by_fft_numpoints(filt_sinc4, 2 ** 20)
filt_ssinc_resp_mag = lltf.freqz_by_fft_numpoints(filt_ssinc, 2 ** 20)
filt_flat_resp_mag = lltf.freqz_by_fft_numpoints(filt_flat, 2 ** 20)



# Calculate response in dB, for later use...
filt_sinc1_resp_mag_db = 20*np.log10(abs(filt_sinc1_resp_mag))
filt_sinc2_resp_mag_db = 20*np.log10(abs(filt_sinc2_resp_mag))
filt_sinc3_resp_mag_db = 20*np.log10(abs(filt_sinc3_resp_mag))
filt_sinc4_resp_mag_db = 20*np.log10(abs(filt_sinc4_resp_mag))
filt_ssinc_resp_mag_db = 20*np.log10(abs(filt_ssinc_resp_mag))
filt_flat_resp_mag_db = 20*np.log10(abs(filt_flat_resp_mag))

# Make vector of frequencies to plot / save against
haxis = np.linspace(0.0, FS, 2**20) # Horizontal axis

with open("LTC2500_filter_responses.csv", "w") as outfile:
    for i in range(0, 16400):
        outfile.write(str(haxis[i]) + "," + str(filt_sinc1_resp_mag_db[i]) + "," + str(filt_sinc2_resp_mag_db[i]) + ","  + str(filt_sinc3_resp_mag_db[i]) + ","
                                          + str(filt_sinc4_resp_mag_db[i]) + "," + str(filt_ssinc_resp_mag_db[i]) + "," + str(filt_flat_resp_mag_db[i])  + "\n")


# Plot frequency response, linear frequency axis
lw = 3
plt.figure(2)
plt.title("LTC2500-32 filter responses (DF " + DF_info.DF_txt + ")")
plt.xlabel('Frequency (Hz)')
plt.ylabel('Rejection (dB)')
plt.axis([0, 16400, -100, 10])
plt.plot(haxis, filt_sinc1_resp_mag_db, linewidth=lw, color="red", zorder=1)
plt.plot(haxis, filt_sinc2_resp_mag_db, linewidth=lw, color="orange",  zorder=1)
plt.plot(haxis, filt_sinc3_resp_mag_db, linewidth=lw, color="green",  zorder=1)
plt.plot(haxis, filt_sinc4_resp_mag_db, linewidth=lw, color="blue",  zorder=1)
plt.plot(haxis, filt_ssinc_resp_mag_db, linewidth=lw, color="purple",  zorder=1)
plt.plot(haxis, filt_flat_resp_mag_db, linewidth=lw, color="black", zorder=1)






print "My program took", (time.time() - start_time), " seconds to run"