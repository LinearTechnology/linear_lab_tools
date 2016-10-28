# -*- coding: utf-8 -*-
'''
Simulation of LTC2440 filters.
This program QUALITATIVELY derive a filter of a type similar to that
used in the LTC2400 family of ADCs.

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
from matplotlib import pyplot as plt

plot_sinc4 = True

# Choices for LTC parts: 2048 for NON-LTC2440 family, 64 to 32768 for LTC2440
osr = 256
sinc1=ones(osr/4) # Dividing by 4 such that the OSR is the number of taps
                  # in the SINC4 filter.

sinc2 = convolve(sinc1, sinc1)
sinc4 = convolve(sinc2, sinc2)
reverser = zeros(osr*2)
reverser[0] = 1
reverser[osr] = 1
sinc4_w_rev = convolve(sinc4, reverser)

# Now normalize filters
sinc1 = sinc1 / sum(sinc1)
sinc2 = sinc2 / sum(sinc2)
sinc4 = sinc4 / sum(sinc4)
sinc4_w_rev = sinc4_w_rev / sum(sinc4_w_rev)

plt.figure(1)

plt.subplot(211)
plt.title('sinc1, 2, 4 time domain responses')
plt.ylabel('tap val.')
plt.plot(sinc1)
plt.plot(sinc2)
plt.plot(sinc4)
plt.subplot(212)
plt.title('sinc4 w/reverser time domain responses')
plt.ylabel('tap val.')
plt.plot(sinc4_w_rev)
plt.plot(reverser * amax(sinc4))
plt.xlabel('tap number')
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
    fresp = 20.0 * np.log10(abs(h)/hmax)
    
    plt.figure(2)
    plt.plot(fresp, zorder=1)
    
    plt.title('sinc4 frequency domain response')
    plt.xlabel('freq.')
    plt.ylabel('log Amplitude')
    plt.axis([0, 2000, -100, 1])
    plt.show()


# Now let's show another reason the LTC244x family is not particularly well suited
# for AC measurements...

numperiods = 4
intersample_delay = 32
several_sinc4s = sinc4_w_rev
for i in range(numperiods):
    several_sinc4s = np.concatenate((several_sinc4s, np.zeros(intersample_delay)))
    several_sinc4s = np.concatenate((several_sinc4s, sinc4_w_rev))

plt.figure(3)
plt.plot(several_sinc4s)
plt.show()





