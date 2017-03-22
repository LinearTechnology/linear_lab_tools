# -*- coding: utf-8 -*-
'''
Welcome to the LinearLabTools simulation of a basic cross-correlation noise
measurement. This technique is used in phase noise measurements, where the 
instrument noise is greater than the noise of the device under test. The
way around this is to make TWO instrument paths, whose noise will be uncorrelated.
The instrument path outputs will have a correlated component due to the common DUT
noise at the input.

This program shows how to extract the correlated component


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



import numpy as np
from numpy import array, vdot, zeros
from scipy import fft, real
#from numpy.random import normal, uniform

def dot_product(a,b):
    dp=np.real(a)*np.real(b) + np.imag(a) * np.imag(b)
    return dp

def alt_dot_product(a, b):
    dp = np.abs(a)*np.abs(b)*np.cos(np.angle(a) - np.angle(b))
    return dp


a = array([1+2j,3+4j])
b = array([5+6j,7+8j])

c = 2+2j
d = 2+2j

#print vdot(a, b)
#(70-8j)
#print vdot(b, a)
#(70+8j)
print np.dot(c, d)
print np.vdot(c, d)
print dot_product(c, d)
print alt_dot_product(c, d)


zero_vector = np.ndarray(shape=(1024), dtype=complex) # Make a complex vector
#for i in range(0, 1024):
#    zero_vector[i] = 0 + 0j
    
xcorr = zero_vector

'''############################'''
'''Set up simulation parameters'''
'''############################'''

dut_noise_fft_avg = zeros(1024)
path_a_noise_fft_avg = zeros(1024)
path_b_noise_fft_avg = zeros(1024)
xcorr_avg = zeros(1024)

naverages = 100

for j in range(0, naverages):
    random_phase = np.random.uniform(0.0, 2*3.1415926, 1)
    dut_noise = np.random.normal(0.0, .00025, 1024)
    for i in range(0, 1024):
        dut_noise[i] += .0001 * np.sin(random_phase + (2.0*3.1415926 * 100 * i/1024))
    
    path_a_noise = np.random.normal(0.0, .001, 1024)
    path_b_noise = np.random.normal(0.0, .001, 1024)
    
    dut_noise_fft = fft(dut_noise)
    path_a_noise_fft = fft(path_a_noise + dut_noise)
    path_b_noise_fft = fft(path_b_noise + dut_noise)
    
    
    for i in range(0, 1024):
        xcorr[i] = (dot_product(path_a_noise_fft[i], path_b_noise_fft[i]))

    dut_noise_fft_avg = dut_noise_fft_avg + abs(dut_noise_fft)
    path_a_noise_fft_avg = path_a_noise_fft_avg + abs(path_a_noise_fft)
    path_b_noise_fft_avg = path_b_noise_fft_avg + abs(path_b_noise_fft)
    xcorr_avg = xcorr_avg + xcorr


dut_noise_fft_avg = dut_noise_fft_avg / naverages
path_a_noise_fft_avg = path_a_noise_fft_avg / naverages
path_b_noise_fft_avg = path_b_noise_fft_avg / naverages
xcorr_avg = xcorr_avg / naverages
for i in range(0, 1024):
    xcorr_avg[i] = pow(xcorr_avg[i], 0.5)


#print path_a_noise_fft[0]

#xcorr[0] = vdot(path_a_noise_fft[0], path_b_noise_fft[0])

#print real(xcorr)

from matplotlib import pyplot as plt


#plt.plot(t, s, t, i)
plt.figure(1)

plt.subplot(411)
plt.title('Path A noise')
plt.plot(abs(path_a_noise_fft_avg))

plt.subplot(412)
plt.title('Path B noise')
plt.plot(abs(path_b_noise_fft_avg))

plt.subplot(413)
plt.title('DUT noise')
plt.plot(abs(dut_noise_fft_avg))

plt.subplot(414)
plt.title('Cross correlation avg')
plt.plot(abs(xcorr_avg))
plt.show()

#plt.figure(2)
#
#plt.subplot(411)
#plt.plot(abs(path_a_noise_fft))
#plt.title('Last data')
#plt.subplot(412)
#plt.plot(abs(path_b_noise_fft))
#plt.subplot(413)
#plt.plot(abs(dut_noise_fft))
#plt.subplot(414)
#plt.plot(abs(xcorr))
#plt.show()

#print dut_noise
