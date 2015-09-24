# -*- coding: utf-8 -*-
"""
Created on Thu Jun 04 15:25:29 2015

@author: FPGA_MS_lab
"""

from matplotlib import pyplot as plt
import numpy as np

#Generate funky SINC data
total_samples = 65536 # n.BuffSize
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