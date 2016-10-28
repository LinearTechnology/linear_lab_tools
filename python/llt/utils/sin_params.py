import math as m
import numpy as np

from matplotlib import pyplot as plt

NONE               = 0x10
HAMMING            = 0x20
HANN               = 0x21
BLACKMAN           = 0x30
BLACKMAN_EXACT     = 0x31
BLACKMAN_HARRIS_70 = 0x32
FLAT_TOP           = 0x33
BLACKMAN_HARRIS_92 = 0x40

DEF_WINDOW_TYPE = BLACKMAN_HARRIS_92

BW = 3

def sin_params(data, window_type=DEF_WINDOW_TYPE, mask=None, num_harms=8, spur_in_harms = True):
    fft_data = windowed_fft_mag(data)
    harm_bins, harms, harm_bws = find_harmonics(fft_data, num_harms)
    spur, spur_bw = find_spur(spur_in_harms, harm_bins, harms, fft_data, window_type)

    if mask is None:
        mask = calculate_auto_mask(fft_data, harm_bins, window_type)
    plt.plot([10*m.log10(f) for f in fft_data])
    plt.plot(mask*10*m.log10(max(fft_data)))
    noise, noise_bins = masked_sum_of_sq(fft_data, mask)
    average_noise = noise / max(1, noise_bins)
    noise = average_noise * len(fft_data)

    # create a dictionary where key is harmonic number and value is tuple of harm and bin
    harmonics = {}
    for i, (h, (b, bw)) in enumerate(zip(harms, zip(harm_bins, harm_bws))):
        h -= average_noise * bw
        if h > 0:
            harmonics[i+1] = (h, b)
       
    spur -= average_noise * spur_bw

    signal = harmonics[1][0]
    snr = 10*m.log10(signal / noise)
    harm_dist = ( harmonics.get(2, (0, 0))[0] + 
                  harmonics.get(3, (0, 0))[0] + 
                  harmonics.get(4, (0, 0))[0] + 
                  harmonics.get(5, (0, 0))[0] )
    thd = 10*m.log10(harm_dist / signal) if harm_dist > 0 else 0
    sinad = 10*m.log10(signal / (harm_dist + noise))
    enob = (sinad -1.76) / 6.02
    sfdr = 10*m.log10(signal / spur) if spur > 0 else 0

    return (harmonics, snr, thd, sinad, enob, sfdr)

def window(size, window_type=DEF_WINDOW_TYPE):
    if window_type == NONE:
        return None

    window_coeffs_dict = {
        HAMMING:            (1.586303, 0.54,       0.46),
        HANN:               (1.632993, 0.50,       0.50),
        BLACKMAN:           (1.811903, 0.42,       0.50,       0.08),
        BLACKMAN_EXACT:     (1.801235, 0.42659071, 0.42659071, 0.07684867),
        BLACKMAN_HARRIS_70: (1.807637, 0.42323,    0.49755,    0.07922),
        FLAT_TOP:           (2.066037, 0.2810639,  0.5208972,  0.1980399),
        BLACKMAN_HARRIS_92: (1.968888, 0.35875,    0.48829,    0.14128,     0.01168)
    }

    window_coeffs = window_coeffs_dict[window_type]
    num_coeffs = len(window_coeffs)

    normalization = window_coeffs[0]      
    a0 = window_coeffs[1]
    a1 = window_coeffs[2]

    tau = 2*m.pi
    t = np.linspace(0, 1, size, False)
    if num_coeffs == 3:
        wind = a0 - a1*np.cos(tau*t)
    elif num_coeffs == 4:
        a2 = window_coeffs[3]
        wind = a0 - a1*np.cos(tau*t) + a2*np.cos(2*tau*t)
    else:
        a2 = window_coeffs[3]
        a3 = window_coeffs[4]
        wind = a0 - a1*np.cos(tau*t) + a2*np.cos(2*tau*t) - a3*np.cos(3*tau*t)
     
    return wind * normalization       

def windowed_fft_mag(data, window_type=BLACKMAN_HARRIS_92):
    n = len(data)      
    data = np.array(data, dtype=np.float64)
    data -= np.mean(data)
    data = data * window(n, window_type)
    fft_data = np.fft.fft(data)[0:n/2+1]
    fft_data = abs(fft_data) / n
    fft_data[1:n/2] *= 2     
    return fft_data

def find_harmonics(fft_data, max_harms):
    harmonic_bins = [0 for i in range(max_harms)]
    fundamental_bin = np.argmax(fft_data)
    harmonic_bins[0] = fundamental_bin
    harmonics = [0 for i in range(max_harms)]
    harmonic_bandwidths = [0 for i in range(max_harms)]

    for h in range(1, max_harms+1):
        # first find the location by searching for the max inside an area of uncertainty
        mask = init_mask(len(fft_data), 0)
        nominal_bin = h * fundamental_bin
        if h > 1:    
            set_mask(mask, nominal_bin-h/2,nominal_bin+h/2)
            for i in range(h-1):
                clear_mask(mask, h, h)
            _, harmonic_bins[h-1] = masked_max(fft_data, mask)

        # now find the power in the harmonic
        clear_mask(mask, nominal_bin-h/2,nominal_bin+h/2)
        set_mask(mask, nominal_bin - BW, nominal_bin + BW)
        for i in range(h-1):
            clear_mask(mask, harmonic_bins[i]-BW, harmonic_bins[i]+BW)
        harmonics[h-1], harmonic_bandwidths[h-1] = masked_sum_of_sq(fft_data, mask)
    return (harmonic_bins, harmonics, harmonic_bandwidths)
        
def calculate_auto_mask(fft_data, harm_bins, window_type):
    BANDWIDTH_DIVIDER = 80
    NUM_INITAL_NOISE_HARMS = 5
    n = len(fft_data)
    bw = n / BANDWIDTH_DIVIDER

    mask = init_mask(n)
    for i in range(NUM_INITAL_NOISE_HARMS):
        clear_mask(mask, harm_bins[i] - bw, harm_bins[i] + bw)
    mask[0] = False

    (noise_est, noise_bins) = masked_sum(fft_data, mask)
    noise_est /= noise_bins

    mask = init_mask(n)
    clear_mask_at_dc(mask, window_type)
    for h in harm_bins:
        low = h
        high = h

        if mask[h] == 0:
            continue

        j = 1
        while ( h-j > 0 and mask[h-j] == 1 and 
                sum(fft_data[(h-j):(h-j+3)]) / 3 > noise_est ):
            j += 1
        low = h - j + 1

        j = 1
        while ( h+j < n and mask[h+j] == 1 and 
                sum(fft_data[(h+j-2):(h+j+1)]) / 3 > noise_est ) :
            j += 1
        high = h + j - 1

        clear_mask(mask, low, high)
    
    return mask

def find_spur_in_harmonics(harm_bins, harms):
    index = np.argmax(harms[1:])
    return harm_bins[index]

def find_spur_bin(fft_data, mask, fund_bin, window_type):
    index = 0
    for i, ms in enumerate(mask):
        if ms == 1:
            index = i
            break

    begin = max(0, index - BW)
    end = min(len(fft_data), index + BW)
    max_value, _ = masked_sum_of_sq(fft_data, mask, begin, end)
    max_index = index

    while index < len(fft_data):
        if mask[index] == 1:
            begin = max(0, index - BW)
            end = min(len(fft_data), index + BW)
            value, _ = masked_sum_of_sq(fft_data, mask, begin, end)
            if value > max_value:
                max_value = value
                max_index = index
        index += 1
    
    begin = max(0, max_index - BW)
    end = min(len(fft_data), max_index + BW)
    spur, spur_bin = masked_max(fft_data, mask, begin, end)
    return spur_bin

def find_spur(find_in_harms, harm_bins, harms, fft_data, window_type):
    fund_bin = harm_bins[0]
    mask = init_mask(len(fft_data))
    clear_mask_at_dc(mask, window_type)
    begin = max(0, fund_bin - BW)
    end = min(len(fft_data), fund_bin + BW)
    clear_mask(mask, begin, end)
    
    if find_in_harms:
        spur_bin = find_spur_bin(fft_data, mask, fund_bin, window_type)
    else:
        spur_bin = find_spur_in_harmonics(harm_bins, harms)

    begin = max(0, spur_bin - BW)
    end = min(len(fft_data), spur_bin + BW)
    return masked_sum_of_sq(fft_data, mask, begin, end)
        
def clear_mask_at_dc(mask, window_type):
    clear_mask(mask, 0, window_type >> 4)

def init_mask(n, initial_value=1):
    if initial_value == 1:
        return np.ones(n)
    else:
        return np.zeros(n)

def set_mask(mask, start, end, set_value=1):
    nyq = len(mask)
    for i in range(start, end+1):
        mask[map_nyquist(i, nyq)] = set_value

def clear_mask(mask, start, end):
    set_mask(mask, start, end, 0)

def map_nyquist(value, nyq):
    n = 2 * (nyq - 1)
    value = (value + n) % n
    if value <= nyq:
        return value
    else:
        return n - value

def masked_reduce(fn, data, mask, begin=0, end=None, initial_value = 0):
    if end is None:
        end = len(data) - 1

    value = initial_value
    num_bins = 0
    end += 1 # we want inclusive
    for pair in zip(data[begin:end], mask[begin:end]):
        if pair[1] == 1:
             value = fn(value, pair[0])
             num_bins += 1
    return (value, num_bins)

def masked_max(data, mask, begin=0, end=None):
    (result, _) = masked_reduce(lambda a, b: b if b[1] > a[1] else a, 
        [d for d in enumerate(data)], mask, begin, end, (0, data[0]))
    return result[1], result[0]

def masked_sum(data, mask, begin=0, end=None):
    return masked_reduce(lambda a, b: a + b, data, mask, begin, end)

def masked_sum_of_sq(data, mask, begin=0, end=None):
    return masked_reduce(lambda a, b: a + b*b, data, mask, begin, end)

