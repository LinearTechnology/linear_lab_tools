from numpy import min, max, convolve, log, ones, zeros
from scipy import linspace, fft
from scipy import signal
from scipy.signal import lti, step
from scipy.misc import imread

# Choices for LTC parts: 2048 for NON-LTC2440 family, 64 to 32768 for LTC2440
osr = 1024 
sinc1=ones(osr/4)
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

w, h = signal.freqz(sinc4_w_rev, 1, 16385)
fresp = log(abs(h))
plt.plot(fresp, zorder=1)
plt.title('sinc4 frequency domain response')
plt.xlabel('freq.')
plt.ylabel('log Amplitude')
plt.axis([0, 2000, 0, 23])
print plt.axis()
img = imread("LinearLogo.tiff")
plt.imshow(img, origin='upper',aspect='auto', extent=[750, 2000, 8, 23])
plt.show()