# -*- coding: utf-8 -*-
'''
Generate SINC data to send to the LTC2000 demo board, for something a bit
more interesting than a plain old sine wave.

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

from matplotlib import pyplot as plt
import numpy as np

def generate_sinc_data(total_samples):
    #Generate funky SINC data
    data = total_samples * [0] 
    for i in range(0, total_samples):
        x = ((i - 32768) / (512.0)) + 0.0001 # Add a tiny offset to avoid divide by zero
        data[i] = int(32000 * (np.sin(x) / x))
    
    plt.figure(1)
    plt.plot(data)
    plt.show()
    
    # Testing file I/O
    
    print('writing data out to file')
    outfile = open('dacdata_sinc.csv', 'w')
    for i in range(0, total_samples):
        outfile.write(str(data[i]) + "\n")
    outfile.close()
    print('done writing!')
    return
