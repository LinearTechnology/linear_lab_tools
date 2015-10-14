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
img = imread("LinearLogo.png")
plt.imshow(img, origin='upper',aspect='auto', extent=[350, 1000, -40, 0])
plt.show()