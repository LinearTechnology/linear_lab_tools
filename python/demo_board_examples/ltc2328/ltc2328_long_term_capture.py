# -*- coding: utf-8 -*-
'''



REVISION HISTORY
$Revision: 4276 $
$Date: 2015-10-20 10:38:41 -0700 (Tue, 20 Oct 2015) $

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

from time import sleep
import time
import numpy as np

from ltc2328_dc1908 import ltc2328_dc1908

# Print extra information to console

num_points = 1024
delay = 1.0

averages = [0] * num_points
stdevs = [0] * num_points
times = [time.time()] * num_points
starttime = time.time()

for i in range (0, num_points):
    print("Capturing point " + str(i) + " of " + str(num_points))
    times[i] = time.time() - starttime
    capturedata = ltc2328_dc1908(32*1024, verbose=False, do_demo=False)
    averages[i] = np.average(capturedata)
    stdevs[i] = np.std(capturedata)
    sleep(delay)


print('Writing data to file')
with open('longterm_data.txt', 'w') as f:
    for i in range (0, num_points):
        f.write(str(times[i]) + "," + str(averages[i]) + "," + str(stdevs[i]) + '\n')