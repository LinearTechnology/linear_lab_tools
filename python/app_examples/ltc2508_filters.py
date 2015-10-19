# -*- coding: utf-8 -*-
'''
LTC2508_filters.py

This script imports the LTC2508 digital filter coefficents and plots the
impulse responses and frequency responses.

It also shows how to combine the responses of an analog anti-aliasing filter and the digital filter
in order to validate that the overall rejection is adequate at the first image frequency (fs) 

Tested with Python 2.7, Anaconda distribution available from Continuum Analytics,
http://www.continuum.io/

REVISION HISTORY
$Revision$
$Date$

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
sys.path.append("../utils")
from linear_lab_tools_functions import *

start_time = time.time();

# Which method to use to calculate frequency response from filter coefficients. The freqz method is
# the "traditional" way, but the FFT method is considerably faster.
use_fft_method = True
ppc = 8 # Points per coefficient, affects fft method
num_freqencies = 65536 # Number of frequencies to evaluate, affects freqz method

# Initialize arrays to hold filter coefficients. We know the number of elements ahead of time.
ssinc_256 = np.ndarray(2175, dtype=float)
ssinc_1024 = np.ndarray(8703, dtype=float)
ssinc_4096 = np.ndarray(34815, dtype=float)
ssinc_16384 = np.ndarray(139263, dtype=float)

# Read in coefficients from files
with open('../../common/ltc25xx_filters/ssinc_256.txt', 'r') as infile:
    for i in range(0, 2175):
        instring = infile.readline()
        ssinc_256[i] = float(instring)
print('done reading DF 256!')

with open('../../common/ltc25xx_filters/ssinc_1024.txt', 'r') as infile:
    for i in range(0, 8703):
        instring = infile.readline()
        ssinc_1024[i] = float(instring)
print('done reading DF 1024!')

with open('../../common/ltc25xx_filters/ssinc_4096.txt', 'r') as infile:
    for i in range(0, 34815):
        instring = infile.readline()
        ssinc_4096[i] = float(instring)
print('done reading DF 4096!')

with open('../../common/ltc25xx_filters/ssinc_16384.txt', 'r') as infile:
    for i in range(0, 139263):
        instring = infile.readline()
        ssinc_16384[i] = float(instring) # Frequency Density
print('done reading DF 16384!')

ssinc_256 /= sum(ssinc_256) #Normalize to unity gain
ssinc_1024 /= sum(ssinc_1024) #Normalize to unity gain
ssinc_4096 /= sum(ssinc_4096) #Normalize to unity gain
ssinc_16384 /= sum(ssinc_16384) #Normalize to unity gain
print("Done normalizing!")

# Plot the impulse responses
plt.figure(1)
plt.title('LTC2508 SSinc filter impulse responses (DF 256, 1024, 4096, 16384)')
#plt.subplot(4, 1, 1)
#plt.title("DF256")
plt.plot(ssinc_256 / max(ssinc_256))
#plt.axis([0, len(ssinc_16384), 0, max(ssinc_256)])
#plt.subplot(4, 1, 2)
#plt.title("DF1024")
plt.plot(ssinc_1024 / max(ssinc_1024))
#plt.axis([0, len(ssinc_16384), 0, max(ssinc_1024)])
#plt.subplot(4, 1, 3)
#plt.title("DF4096")
plt.plot(ssinc_4096 / max(ssinc_4096))
#plt.axis([0, len(ssinc_16384), 0, max(ssinc_4096)])
#plt.subplot(4, 1, 4)
#plt.title("DF16384")
plt.plot(ssinc_16384 / max(ssinc_16384))
#plt.axis([0, len(ssinc_16384), 0, max(ssinc_16384)])
plt.xlabel('tap number')
plt.show()

# Function to calculate frequency response of a filter from its coefficients. The points_per_coeff parameter tells how many points
# in between unit circle zeros to calculate.
#def freqz_by_fft(filter_coeffs, points_per_coeff):
#    num_coeffs = len(filter_coeffs)
#    fftlength = num_coeffs * points_per_coeff
#    resp = abs(np.fft.fft(np.concatenate((filter_coeffs, np.zeros(fftlength - num_coeffs))))) # filter and a bunch more zeros
#    return resp

if(use_fft_method == True):
    print("Calculating frequency response using zero-padded FFT method")
    ssinc_256_mag = freqz_by_fft(ssinc_256, 64*ppc)
    ssinc_1024_mag = freqz_by_fft(ssinc_1024, 16*ppc)
    ssinc_4096_mag = freqz_by_fft(ssinc_4096, 4*ppc)
    ssinc_16384_mag = freqz_by_fft(ssinc_16384, ppc)
else:
    print("Calculating frequency response using numpy's freqz function")
    w1, ssinc_256_mag = signal.freqz(ssinc_256, 1, num_freqencies)
    w2, ssinc_1024_mag = signal.freqz(ssinc_1024, 1, num_freqencies)
    w3, ssinc_4096_mag = signal.freqz(ssinc_4096, 1, num_freqencies)
    w4, ssinc_16384_mag = signal.freqz(ssinc_16384, 1, num_freqencies)

# Calculate response in dB, for later use...
fresp1 = 20*np.log10(abs(ssinc_256_mag))
fresp2 = 20*np.log10(abs(ssinc_1024_mag))
fresp3 = 20*np.log10(abs(ssinc_4096_mag))
fresp4 = 20*np.log10(abs(ssinc_16384_mag))

# Plot frequency response, linear frequency axis
plt.figure(2)
plt.semilogy(ssinc_256_mag, zorder=1)
plt.semilogy(ssinc_1024_mag, zorder=1)
plt.semilogy(ssinc_4096_mag, zorder=1)
plt.semilogy(ssinc_16384_mag, zorder=1)


plt.title('LTC2508 SSinc filter responses (DF 256, 1024, 4096, 16384)')
plt.xlabel('freq.')
plt.ylabel('log Amplitude')
plt.axis([0, 16400, 10.0**(-150/20), 1])
plt.show()

# Now let's show the first 2 images of the DF 256 filter, then create an
# analog filter with the intent of suppressing the first image by at least 80dB

sample_rate = 1000000.0
bin_width = sample_rate / len(ssinc_256_mag)
print ("bin width: " + str(bin_width))
print ("1kHz bin: " + str(1000.0 / bin_width))
print ("1kHz bin: " + str(2000.0 / bin_width))

wide_ssinc_256_mag = np.concatenate((ssinc_256_mag, ssinc_256_mag))
first_order_response = np.ndarray(len(wide_ssinc_256_mag), dtype=float)
second_order_response = np.ndarray(len(wide_ssinc_256_mag), dtype=float)
cutoff_1st = 1000.0 / bin_width# 1000.0 # Bin number
cutoff_2nd = 1000.0 / bin_width# 2000.0
for i in range(0, len(wide_ssinc_256_mag)): # Generate first order response for each frequency in wide response
    first_order_response[i] = 1.0 / (1.0 + (i/cutoff_1st)**2.0)**0.5 # Magnitude = 1/SQRT(1 + (f/fc)^2)
    second_order_response[i] = 1.0 / (1.0 + (i/cutoff_2nd)**4.0)**0.5 # Magnitude = 1/SQRT(1 + (f/fc)^2)



x = np.linspace(0, len(wide_ssinc_256_mag) - 1, num=len(wide_ssinc_256_mag))
plt.figure(3)
plt.title("First image of DF256 filter, along with analog AAF filter response")
plt.axis([200, 0.75*len(wide_ssinc_256_mag), -150, 0])
plt.ylabel("Rejection (dB)")
plt.xlabel("Frequency (Hz)")
#plt.loglog(wide_ssinc_256_mag)
#plt.loglog(first_order_response)
#plt.loglog(second_order_response)
plt.semilogx(x, 20*np.log10(wide_ssinc_256_mag))
plt.semilogx(x, 20*np.log10(first_order_response))
plt.semilogx(x, 20*np.log10(second_order_response))
#plt.loglog(np.multiply(wide_ssinc_256_mag, second_order_response))
plt.tight_layout()

sscinc_shifted = ssinc_256

plt.figure(4)
plt.plot(sscinc_shifted)
sscinc_shifted = np.concatenate((np.zeros(256), sscinc_shifted ))
plt.plot(sscinc_shifted)
sscinc_shifted = np.concatenate((np.zeros(256), sscinc_shifted ))
plt.plot(sscinc_shifted)
sscinc_shifted = np.concatenate((np.zeros(256), sscinc_shifted ))
plt.plot(sscinc_shifted)
sscinc_shifted = np.concatenate((np.zeros(256), sscinc_shifted ))
plt.plot(sscinc_shifted)
sscinc_shifted = np.concatenate((np.zeros(256), sscinc_shifted ))
plt.plot(sscinc_shifted)
sscinc_shifted = np.concatenate((np.zeros(256), sscinc_shifted ))
plt.plot(sscinc_shifted)
sscinc_shifted = np.concatenate((np.zeros(256), sscinc_shifted ))
plt.plot(sscinc_shifted)
sscinc_shifted = np.concatenate((np.zeros(256), sscinc_shifted ))
plt.plot(sscinc_shifted)
plt.show()



print "My program took", (time.time() - start_time), " seconds to run"