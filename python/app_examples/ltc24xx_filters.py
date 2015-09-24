# -*- coding: utf-8 -*-
'''
Simulation of LTC2440 filters.
We'll derive the filter used in the LTC2400 family of ADCs,
Then demonstrate that averaging is just the same thing as bin 0 of an FFT.
This is a useful mental tool for relating the AC spec of SNR to the DC spec
of RMS noise.



Tested with Python 2.7, Anaconda distribution available from Continuum Analytics,
http://www.continuum.io/

Demo board documentation:
http://www.linear.com/demo/2085
http://www.linear.com/product/LTC2000#demoboards

LTC2508 product page
http://www.linear.com/product/LTC2508


REVISION HISTORY
$Revision: 3018 $
$Date: 2014-12-01 15:53:20 -0800 (Mon, 01 Dec 2014) $

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

Mark Thoren
Linear Technology Corporation
November, 2014
'''


from numpy import min, max, convolve, random, average, ones, zeros, amax, log
import numpy as np
from scipy import linspace, fft
from scipy import signal
from scipy.signal import lti, step
from scipy.misc import imread

plot_sinc4 = True

# Choices for LTC parts: 2048 for NON-LTC2440 family, 64 to 32768 for LTC2440
osr = 256
sinc1=ones(osr/4) # Dividing by 4 such that the OSR is the number of taps
                  # in the SINC4 filter.
#print sinc1
sinc2 = convolve(sinc1, sinc1)
#print sinc2
sinc4 = convolve(sinc2, sinc2)
#print sinc4
reverser = zeros(osr*2)
reverser[0] = 1
reverser[osr] = 1
sinc4_w_rev = convolve(sinc4, reverser)


from matplotlib import pyplot as plt


#plt.plot(t, s, t, i)
plt.figure(1)

plt.subplot(311)
plt.plot(sinc1)
plt.title('sinc4 time domain response')
plt.subplot(312)
plt.plot(sinc2)
plt.subplot(313)
plt.plot(sinc4_w_rev)
plt.plot(reverser * amax(sinc4))
plt.xlabel('tap number')
plt.ylabel('Amplitude')
#plt.hlines(1, min(sinc4), max(sinc4), colors='r')
#plt.hlines(0, min(sinc4), max(sinc4))
plt.xlim(xmin=-100, xmax=2*osr)
#plt.legend(('Unit-Step Response',), loc=0)
plt.grid()
plt.show()

if plot_sinc4 == True :
    #fresp = log(abs(fft(sinc4)))
    #fresp = signal.welch(sinc4)
    w, h = signal.freqz(sinc4_w_rev, 1, 16385)
    hmax = max(h) #Normalize to unity
    fresp = log(abs(h)/hmax)
    
    plt.figure(2)
    plt.plot(fresp, zorder=1)
    
    plt.title('sinc4 frequency domain response')
    plt.xlabel('freq.')
    plt.ylabel('log Amplitude')
    plt.axis([0, 2000, -20, 1])
    plt.show()

#Okay, now let's play around with some filtering, and try to show the
#equivalence of averaging (A SINC1 filter) to bin 1 of an FFT!

num_points = 1024
value = 100
rms_noise = 25

data = np.ndarray(shape=num_points, dtype=float)#zeros(num_bins)
avg = 0.0
for i in range(num_points):
    data[i] = np.random.normal(value, rms_noise)
    avg += data[i]    
    
avg = avg / num_points
print "Average, calculated using standard method: " + str(avg)
fftdata = fft(data)
print "Average, taken as bin 1 of FFT: " + str(fftdata[0] / num_points)



