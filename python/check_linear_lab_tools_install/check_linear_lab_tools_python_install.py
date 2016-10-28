# -*- coding: utf-8 -*-
'''
Simple program to validate that Python was installed properly and that NumPy, SciPy,
and Matplotlib are installed. 

Tested with Python 2.7, Anaconda distribution available from Continuum Analytics,
http://www.continuum.io/


REVISION HISTORY
$Revision: 4285 $
$Date: 2015-10-20 15:21:11 -0700 (Tue, 20 Oct 2015) $

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

import numpy as np
from scipy import linspace, fft
from scipy import signal
from scipy.signal import lti, step
from scipy.misc import imread

# Choices for LTC parts: 2048 for NON-LTC2440 family, 64 to 32768 for LTC2440
osr = 1024 
sinc1=np.ones(osr/4)
#print sinc1
sinc2 = np.convolve(sinc1, sinc1)
#print sinc2
sinc4 = np.convolve(sinc2, sinc2)
#print sinc4
reverser = np.zeros(osr*2)
reverser[0] = 1
reverser[osr] = 1
sinc4_w_rev = np.convolve(sinc4, reverser)
sinc4_w_rev = sinc4_w_rev/sum(sinc4_w_rev)


from matplotlib import pyplot as plt

w, h = signal.freqz(sinc4_w_rev, 1, 16385)
fresp = 20*np.log10(abs(h))
plt.plot(fresp, zorder=1)
plt.title('Congratulations! Python is installed properly!')
plt.xlabel('Frequency')
plt.ylabel('Rejection')
plt.axis([0, 1000, -150, 0])
print plt.axis()
img = imread("LinearLogo.PNG")
plt.imshow(img, origin='upper',aspect='auto', extent=[350, 1000, -40, 0])
plt.show()