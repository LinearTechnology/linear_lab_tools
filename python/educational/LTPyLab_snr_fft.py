'''
Welcome to the LTPyLab simulation of basic FFT operation, SNR calculation
Basically, we're making a vector of num_bins time domain
samples, then corrupting the signal in several "real world" ways:

1) Thermal noise is added to the signal, which is just a random
number with a gaussian distribution. This is often referred to as the
"transition noise" of an ADC, and it can never be smaller than K*T/C where
K is Boltzmann's constant, T is absolute temperature, and C is the size of the
ADC's sample capacitor.

2) Quantization noise is added by simply starting with a signal of amplitude
2^(number of bits), then truncating the decimal portion with the int function

3) Random jitter is added to the sample clock. This is an accurate model of
wideband clock jitter that is spread across seveal Nyquist bands

3) Deterministic jitter is added to the sample clock, representing phase noise
at a particular frequency. This gives an intuitive understanding of the effect
of phase noise as a signal's frequency and amplitude change.


Mark Thoren
Linear Technology Corporation
November, 2014
'''

'''############################'''
'''Set up simulation parameters'''
'''############################'''
bits = 16 # ADC resolution (Theoretical!!)
num_bins = 4096 #This is also the number of points in the time record
bin_number = 500 #Bin number of the signal itself. If bin_number is greater
                #than num_bins/2, then the signal will be aliased accordingly

thermal_noise = 0.5 #0.00010 # LSB of thermal noise
jitter = 0.0000000000001 #0.000025 # clock jitter, expressed as RMS fraction of a sampling interval

# Now for some phase noise... To illustrate the concept, we're going to introduce
# a single tone of phase noise, rather than a distribution (as is the case in
# "real life".) This IS an accurate representation of a sinusoidal disturbance
# on the clock.
phase_noise_offset = 25 # Offset from carrier in bins
phase_noise_amplitude = 0.0 #.000001 #Amplitude, in fraction of a sample period
# third_harm = 0.0 Next revision will include harmonics...
'''##############################'''
'''END setupsimulation parameters'''
'''##############################'''

# Pull in the good stuff from various libraries...
import numpy as np
from scipy import fft
from matplotlib import pyplot as plt

# declare variables to make code easier to read below
data = np.zeros(num_bins)
freq_domain_signal = np.zeros(num_bins)
freq_domain_noise = np.zeros(num_bins)

signal_level = 2.0**bits # Calculated amplitude in LSB.

#Generate some input data, along with noise
for t in range(num_bins):
    phase_jitter = phase_noise_amplitude * np.cos(2.0 * np.pi * phase_noise_offset* t / num_bins)
    samp_jitter = np.random.normal(0.0, jitter)
    data[t] = signal_level * np.cos(2.0*np.pi*bin_number*(t + samp_jitter + phase_jitter)/num_bins)/2.0 #First the signal :)
    #data[t] += third_harm * np.cos(3.0*2.0*np.pi*bin_number*(t)/num_bins)/2.0
    data[t] += np.random.normal(0.0, thermal_noise) #Then the thermal noise ;(
    data[t] = np.rint(data[t]) #Finally, round to integer value - equiavalent to quantizing
    
freq_domain = np.fft.fft(data)/num_bins
freq_domain_magnitude = np.abs(freq_domain)

#Now notch the signal out of the spectrum. We have the advantage here
#that there's only a single bin of signal, and no distortion.

np.copyto(freq_domain_noise, freq_domain_magnitude) #Make a copy

freq_domain_noise[bin_number] = 0 #Zero out signal bins. Fill in later with
freq_domain_noise[num_bins - bin_number] = 0 # Average noise floor

#Make another array that just has the signal

freq_domain_signal[bin_number] = freq_domain_magnitude[bin_number]
freq_domain_signal[num_bins - bin_number] = freq_domain_magnitude[num_bins - bin_number]

signal = 0.0 #Start with zero signal, zero noise
noise = 0.0

# Sum the power root-sum-square in each bin. Abs() function finds the power, a resistor dissipating
# power does not care what the phase is!

#for i in range(num_bins):
#    signal += (np.abs(freq_domain_signal[i])) ** 2 # D'oh... not supposed to RSS signal
#    noise += (np.abs(freq_domain_noise[i])) ** 2

signal_ss = np.sum(((freq_domain_signal)) ** 2) # D'oh... not supposed to RSS signal
noise_ss = np.sum(((freq_domain_noise)) ** 2 )
    
#signal = np.sqrt(np.abs(signal)) / num_bins
#noise = np.sqrt(np.abs(noise)) / num_bins
signal = np.sqrt(signal_ss) / num_bins
noise = np.sqrt(noise_ss) / num_bins

snr_fraction = signal / noise
snr = 20*np.log10(signal / noise)
print "Signal: " + str(signal)
print "Noise: " + str(noise)
print "Fractional signal to noise: " + str(snr_fraction)
print "SNR: " + str(snr) + "dB"

#raw_input('Enter to close and Continue: ')

max_freq_domain_magnitude = max(freq_domain_magnitude)
freq_domain_magnitude_db = 10 * np.log(freq_domain_magnitude / max_freq_domain_magnitude)

plt.figure(1)
plt.title("Time domain data, with imperfections")
plt.plot(data)
plt.show

plt.figure(2)
plt.title("Spectrum")
plt.plot(freq_domain_magnitude_db)
plt.show


