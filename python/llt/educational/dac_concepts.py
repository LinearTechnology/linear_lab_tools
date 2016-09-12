# -*- coding: utf-8 -*-
'''
LinearLabTools simulation of Digital to Analog Converter
operation and theory. We will simulate the output spectrum of an ideal DAC,
then add quantization noise. Quantization noise is not described in much
detail, or at least we couldn't find much on the subject. So we'll try to get
a nice picture of what "ideal noise" looks like!


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

#First, import  NumPy and SciPy...
from numpy import pi
import numpy as np #All functions available as np.xxx
from matplotlib import pyplot as plt

#Okay, now on to the DAC spectrum!
num_points = 32 #This is the number of points in the time record
bin_number = 10  # How many cycles of sinewave over the time record.
                # num_points/(bin_number * 2) is the "oversample ratio"


data = np.zeros(num_points) #First, make a vector of zeros
# Next, generate the ideal sinusoidal data points
for i in range(num_points):
    data[i]= np.sin(2*np.pi*bin_number*i/num_points)

#Plot the data!!
plt.figure(1) # This generates a new plot, defined as "1"
plt.plot(data) # This actually plots the data
plt.title('Raw, perfect data') # Put a title on the plot
plt.show # And send it to the screen so a human can actually see it!

# The ideal data is exactly as it would be inside a computer, radio, etc.
# In order to model the effects of the steps in a DAC output spectrum, 
# We need to generate several equal value points for each data point.
# More points per step gives a more accurate representation of the actual spectrum.
# The "upsample" parameter is how many points for each step.

upsample = 16 # Define the upsample ratio
upsample_data = np.zeros(upsample*len(data))
for i in range (0, len(data)):
        for j in range (0, upsample):
            upsample_data[i*upsample+j] = data[i]
print "length of upsampled data:" + str(len(upsample_data))
plt.figure(2)
plt.subplot(211) # This is pretty neat - if you want a couple of plots per window
                 # then make subplots.
plt.title('upsampled data showing steppiness')
plt.plot(upsample_data)
plt.show


dac_spectrum = (abs(np.fft.fft(upsample_data))) / len(upsample_data)
plt.subplot(212)
plt.title('spectrum, showing clock products')
plt.plot(dac_spectrum)#, '-o')
plt.show

'''
Okay, now on to quantization noise. Why is this not talked about very often?
We're thinking because most of the time the quantization noise is quite
a bit lower than noise from other sources. So let's start with an ideal
DAC output, and put some noise into the steps. Reminder: We're trying
to see stuff in the frequency domain that is BETWEEN the clock products
that we just simulated, so we need several cycles to work with.
More cycles = a closer look at the shape of the quantization noise floor.
'''
num_cycles = 16
upsample_data_w_qnoise = np.zeros(upsample*len(data)*num_cycles)
for h in range (0, num_cycles):
    for i in range (0, len(data)):
        qnoise = np.random.uniform(0, 0.1, 1)
        for j in range (0, upsample):
            upsample_data_w_qnoise[h*upsample*len(data) + i*upsample + j] = data[i] + qnoise

dac_spectrum_w_qnoise = (abs(np.fft.fft(upsample_data_w_qnoise))) / len(upsample_data_w_qnoise)

plt.figure(3)
plt.title('Spectrum, with quantization noise')
plt.semilogy(dac_spectrum_w_qnoise)
plt.show

plt.figure(4)
plt.title("Time domain signal, several cycles with q noise")
plt.plot(upsample_data_w_qnoise)
plt.show


