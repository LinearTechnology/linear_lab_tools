# -*- coding: utf-8 -*-
"""
Created on Sat Jun 06 07:45:06 2015

@author: markthoren
"""

"""
Useful functions for various LinearLabTools projects
"""
import numpy as np
from matplotlib import pyplot as plt

def fold_spectrum(unfolded_spectrum, points_per_zone, num_zones):
    verbose = 0
    zonesign = 1
    folded_spectrum = [[0 for i in range(num_zones)] for j in range(points_per_zone)] #initialize array
    # This section slices up the unfolded spectrum, flipping for even Nyquist zones.
    for i in range(0, num_zones):
        if(zonesign == 1):
            folded_spectrum[i] = unfolded_spectrum[points_per_zone*(i):points_per_zone*(i+1) -1:1]
            zonesign = -1
            if(verbose == 1):
                print str(i) + " " +str(points_per_zone*(i)) + " " + str(points_per_zone*(i+1)-1)
        else:
            folded_spectrum[i] = unfolded_spectrum[points_per_zone*(i+1)-1 : points_per_zone*(i) : -1]
            zonesign = 1
            if(verbose == 1):
                print str(i) + " " +str(points_per_zone*(i+1)-1) + " " + str(points_per_zone*(i))
    # Now RMS sum corresponding points from each zone
    rms_sum = [0 for i in range(points_per_zone)]
    for i in range(0, num_zones): # First, square noise densities of each zone, then add
        for j in range(0, points_per_zone-1):
            rms_sum[j] += folded_spectrum[i][j] ** 2
    
    for j in range(0, points_per_zone): # Then take the square root of each element
        rms_sum[j] = rms_sum[j] ** 0.5
    return folded_spectrum, rms_sum


# Function to integrate a power-spectral-density
def integrate_psd(psd, bw):
    integral_of_psd_squared = np.zeros(len(psd))
    integrated_psd = np.zeros(len(psd))
    integral_of_psd_squared[0] = psd[0]**2.0

    for i in range(1, len(psd)):
        integral_of_psd_squared[i] += integral_of_psd_squared[i-1] + psd[i-1] ** 2
        integrated_psd[i] += integral_of_psd_squared[i]**0.5
    integrated_psd *= bw**0.5
    return integrated_psd
    

def freqz_by_fft(filter_coeffs, points_per_coeff):
    num_coeffs = len(filter_coeffs)
    fftlength = num_coeffs * points_per_coeff
    resp = abs(np.fft.fft(np.concatenate((filter_coeffs, np.zeros(fftlength - num_coeffs))))) # filter and a bunch more zeros
    return resp




if __name__ == "__main__":
    print("First, let's validate the integrate_psd function...")
    numpoints = 65536
    cutoff = 1024.0
    bw_per_point = 1/cutoff
    fmax = numpoints * bw_per_point
    first_order_response = np.ndarray(numpoints, dtype = float)
    for i in range(numpoints):
        first_order_response[i] = 1.0 / (1.0 + (i/cutoff)**2.0)**0.5 # Magnitude = 1/SQRT(1 + (f/fc)^2)
    psd = integrate_psd(first_order_response, 1.0/cutoff)

    print("Test parameters:")
    print("Cutoff frequency: " + str(cutoff) + "Hz")
    print("Integrate DC to : " + str(numpoints) + "Hz")
    print("Predicted total noise is sqrt(pi/2): " + str((np.pi/2) ** 0.5))
    print("And it actually is: " + str(psd[numpoints-1]))

    f = np.arange(2, 65538, 1)

    plt.figure(1)
    plt.subplot(2, 1, 1)
    plt.title("First order LPF response, fc=" + str(cutoff))
    plt.semilogx(f, 20*np.log(first_order_response))
    plt.subplot(2, 1, 2)
    plt.title("Total integ. noise from DC to x, should be (pi/2)^0.5")
    plt.semilogx(f, psd)
    plt.show()
    
    sinc1resp = abs(np.fft.fft(np.concatenate(((np.ones(1024)/1024.0), np.zeros(65536-1024))))) # Make a 1024 tap filter, then find freq response
    psdsinc = integrate_psd(sinc1resp, 1.0/64.0)

    plt.figure(2)
    plt.subplot(2, 1, 1)
    plt.title("SINC1 filter response, N=" + str(1024))
    plt.plot(sinc1resp)
    plt.axis([0, 500, 0, max(sinc1resp)])
    plt.subplot(2, 1, 2)
    plt.title("Total integ. noise from DC to x, should be 2^0.5")
    plt.plot(psdsinc)
    plt.axis([0, 500, 0, max(psdsinc)])
    plt.show()
    
    print("And finally, here's your LTSpice noise simulation directive:")
    print(".noise V(Vout) Vin_source lin " + str(numpoints-1) + " " + str(bw_per_point) + " " + str(fmax))
# Arguments are output node, input node, linear spacing, # of points, bin 1 frequency, end frequency)
    
    ltspice_psd = np.zeros(numpoints) # bin zero(DC) already set to zero ;)
    print('reading noise PSD data from file')
    infile = open('../../common/LTSpice/validate_integrate_psd.txt', 'r')
    print("First line (header): " + infile.readline())
    for i in range(1, numpoints-1):
        instring = infile.readline()
        indata = instring.split()         # Each line has two entries separated by a space
        ltspice_psd[i] = float(indata[1]) # Frequency Density
    infile.close()
    print('done reading!')
    
    ltspice_totalnoise = integrate_psd(ltspice_psd, bw_per_point)
    print("total noise of LTSpice sim: " + str(ltspice_totalnoise[numpoints-1]))

