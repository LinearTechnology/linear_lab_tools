# -*- coding: utf-8 -*-
"""
Created on Fri Sep 30 09:40:32 2016

@author: jeremy_s
"""

##############################################################################
##### HAO'S STUFF ##### HAO'S STUFF ##### HAO'S STUFF ##### HAO'S STUFF ######
##############################################################################
import math
import numpy as np

class sin_params():
    def __init__(self, data, num_bits, mask, window_string="NONE", num_harmonics=8, thd_harmonics=5):
        self.num_samps = len(data)
        self.num_bits = num_bits
        self.num_harmonics = num_harmonics
        self.thd_harmonics = thd_harmonics
        self.mask_indices = self._mask_to_indices(mask)
        
        windows = {'HAMMING':(1.586303,0.54,0.46,0.0,0.0),'HANN':(1.632993,0.50,0.50,0.0,0.0),'BLACKMAN':(1.811903,0.42,0.50,0.08,0.0),
        'BLKEXACT':(1.801235,0.42659071,0.42659071,0.07684867),'BLKHARRIS_70':(1.807637, 0.42323,0.49755,0.07922,0.0),
        'FLATTOP':(2.066037, 0.2810639,0.5208972,0.1980399,0.0),'BLKHARRIS_92':(1.968888,0.35875,0.48829,0.14128,0.01168)}
        self.window_string = window_string        
        self.window_type = None
        if not (window_string is None or window_string == "NONE"):
            self.window_type = windows[window_string]
        
        self.fft_data = self._windowed_fft_mag(data)
        
        self.BANDWIDTH = 3
        
        self.noise_power = None
        self.harmonic_bins = None
        self.harmonics = None
        self.fundamental = None
        self.harmonic_sum = None
        self.auto_mask = None
           
    def get_noise(self):
        if self.noise_power == None:
            self.noise_power = self._calculate_noise()
        return self.noise_power
        
    def get_harmonic_bins(self):
        if self.harmonic_bins == None:
            self.harmonic_bins = self._calculate_harmonic_bins()
        return self.harmonic_bins       
    
    def get_harmonics(self):
        if self.harmonics == None:
            self.harmonics = self._calculate_harmonics()
        return self.harmonics
        
    def get_fundamental(self):
        if self.fundamental == None:
            self.fundamental = self.get_harmonics()[1]
        return self.fundamental
        
    def get_fundamental_dbfs(self):
        return 10*math.log10(self.get_fundamental()) - 20*math.log10(1 << (self.num_bits - 1))
    
    def get_harmonics_db(self):
        h_powers = self.get_harmonics()
        fundamental = self.to_db(h_powers[1])
        h_powers_db = {}
        count = 0
        for h in h_powers:
            if h != 1 and count != 0:
                try:
                    h_powers_db[h] = self.to_db(h_powers[h]) - fundamental
                except:
                    pass
            else:
                count += 1
        return h_powers_db
    
    def get_snr(self):      
        return self.get_fundamental() / self.get_noise()
    
    def get_snr_db(self):
        return self.to_db(self.get_snr())
          
    def get_harmonic_sum(self):
        if self.harmonic_sum is None:
             self.harmonic_sum = self._calculate_harmonic_sum()
        return self.harmonic_sum
          
    def get_thd(self):            
        return self.get_harmonic_sum() / self.get_fundamental()
        
    def get_thd_db(self):
        return self.to_db(self.get_thd())
    
    def get_sinad(self):
        f = self.get_fundamental()
        n = self.get_noise()
        thd = self.get_harmonic_sum()
        return f / (n + thd)
        
    def get_sinad_db(self):
        return self.to_db(self.get_sinad())
    
    def get_enob(self):
        return ((self.get_sinad_db())-1.76)/6.02
        
    def get_spur(self):
        spur_index = 0
        spur_sum = 0
        fundamental_index = self._get_index_of_max(self.fft_data)
        dc_mask = self._get_dc_mask()

        for i, item in enumerate(self.fft_data):
            if (i < dc_mask + self.BANDWIDTH or i > len(self.fft_data)-4) or (i >= fundamental_index-6 and i <= fundamental_index+6):
                continue
            bins = range(i-self.BANDWIDTH,i+self.BANDWIDTH+1)
            bins_sum = sum(self._index_subset(self.fft_data, bins))
            
            if bins_sum > spur_sum:
                spur_index = i
                spur_sum = bins_sum
                
        return spur_index
    
    def get_spur_power(self):
        spur_index = self.get_spur()
        spur_bins = range(spur_index-self.BANDWIDTH,spur_index+self.BANDWIDTH+1)
        spur_power = self._get_power(spur_bins)
        return spur_power
        
    def get_auto_mask(self, max_harms):
        if self.auto_mask is None:
             self.auto_mask = self._calculate_auto_mask(max_harms)
        return self.auto_mask
         
    # Extra conversation functions
    def to_db(self, val):
        return 10*math.log10(val)
        
    def from_db(self, val):
        return 10**(val/10)
    
    def from_db20(self, val):
        return 20*math.log10(val)
    
    def to_db20(self, val):
        return 10**(val/20)
        
    #####################################################################################
    # CALCULATE FUNCTIONS #
    #####################################################################################
    
    # Calculates the noise using the indices of the mask, which indicate where the signals occur
    def _calculate_noise(self):
        data_len = len(self.fft_data)
        noise_len = len(self.mask_indices)
        
        unmasked_data = self._index_subset(self.fft_data, self.mask_indices)
        
        noise_power = self._sum_of_squares(unmasked_data)   
        
        noise_power /= noise_len
        noise_power *= data_len  
        
        return noise_power 
    
    # Calculates the indices of where the harmonics are, starting off with the fundamental
    def _calculate_harmonic_bins(self):
        harmonic_bins = [0 for i in range(self.num_harmonics)]
        fundamental_bin = self._get_index_of_max(self.fft_data)
        harmonic_bins[0] = fundamental_bin
        for h in range(2,self.num_harmonics+1):
            nominal_bin = h * fundamental_bin
            bins = range(nominal_bin-h/2,nominal_bin+h/2+1)
            bins = map(self._map_index,bins,[len(self.fft_data) for x in range(len(bins))])
            
            harmonic_bins[h-1] = bins[self._get_index_of_max(self._index_subset(self.fft_data, bins))]     
        
        return harmonic_bins
    
    # Calculates the power of each harmonic by adding the bins' sum of squares and subtracting the harmonic noise
    def _calculate_harmonics(self):           
        #harmonic_powers = [0 for x in range(len(self.get_harmonic_bins()))]    
        harmonics = {}
        prev_harmonic_bins = []
        avg_noise = self.get_noise() / len(self.fft_data)
        
        for i, item in enumerate(self.get_harmonic_bins()):
            bins = range(item-self.BANDWIDTH,item+self.BANDWIDTH+1)
            bins = map(self._map_index,bins,[len(self.fft_data) for x in range(len(bins))])
            bins = self._make_unique(bins)

            bins = self._set_diff(bins,prev_harmonic_bins)
            
            bin_power = self._index_subset(self.fft_data, bins)
            raw_power = self._sum_of_squares(bin_power)
            harmonic_noise = avg_noise * len(bins)
            if raw_power > harmonic_noise:
                harmonics[i+1] = raw_power - harmonic_noise
                
            prev_harmonic_bins.append(bins)
        
        return harmonics

    # Calculates the thd power by summing up the harmonics
    def _calculate_harmonic_sum(self):
        harm_sum = 0
        for i in range(self.thd_harmonics-1):
            h = i+2
            try:
                harm_sum += self.get_harmonics()[h]
            except:
                pass
        return harm_sum
        
    # Calculates an approximation of the noise floor
    def _calculate_est_noise_floor(self, N):
        data_length = len(self.fft_data)
        BW = data_length/(N*20)
 
        mask = [1 for x in range(data_length)]
        mask[0] = 0
        for i in range(N+1):
            mask[self.get_harmonic_bins()[i]-BW:self.get_harmonic_bins()[i]+BW+1] = np.zeros(2*BW+1)
            
        indices = self._mask_to_indices(mask)
        
        for i,index in enumerate(indices):
            indices[i] = self._map_index(index,data_length)

        noise_indices = self._make_unique(indices)
        
        data_points = self._index_subset(self.fft_data,noise_indices)

        noise_estimate = sum(data_points)
        const = data_length - (N+1)*(2*BW+1) - 1
        noise_estimate /= const
        
        return noise_estimate
        
    # Calculates an auto mask for the signal
    def _calculate_auto_mask(self, max_harms):
         mask = [0 for x in range(len(self.fft_data))]
         dc_mask = self._get_dc_mask()
         mask[0:dc_mask+1] = np.ones(dc_mask+1)
         
         harmonic_bins = self.get_harmonic_bins()
         noise_est = self._calculate_est_noise_floor(4)
         print "the noise is" , noise_est

         for i in range(max_harms):
            k = harmonic_bins[i]
            low = harmonic_bins[i]
            high = harmonic_bins[i]
            
            if mask[k] == 1:
                continue
            
            for j in range(1,k):
                average = (self.fft_data[k-j]+self.fft_data[k-j+1]+self.fft_data[k-j+2])/3
                if mask[k-j] == 1:
                    break
                if average <= noise_est:
                    low = k - j + 1
                    break

            for j in range(1,len(self.fft_data)-k):
                average = (self.fft_data[k+j]+self.fft_data[k+j-1]+self.fft_data[k+j-2])/3
                if mask[k+j] == 1:
                    break
                if  average <= noise_est:
                    high = k + j - 1
                    break
            
            mask[low:high+1] = np.ones(high-low+1)
         return mask
    
    #####################################################################################
    # HELPER FUNCTIONS #
    #####################################################################################
    
    # Maps the the index according to the nyquist 
    def _map_index(self, index, num_samples):
        length = num_samples/2 -1
        nyquist_bin = length/2
        index = (index + length) % length
        if index <= nyquist_bin:
            return index
        else:
            return length-index
    
    # Windowing function that follows PScope constants for blackman harris 92dB
    def _window_func(self, size):
        normalization = self.window_type[0];        
        a0 = self.window_type[1]
        a1 = self.window_type[2]
        a2 = self.window_type[3]
        a3 = self.window_type[4]
        
        wind = [0 for x in range(size)]
        for i in range(size):
            
            t1 = i / (float(size) - 1.0)
            t2 = 2 * t1
            t3 = 3 * t1
            t1 -= int(t1)
            t2 -= int(t2)
            t3 -= int(t3)
            
            wind[i] = a0 - \
                      a1*math.cos(2*math.pi*t1) + \
                      a2*math.cos(2*math.pi*t2) - \
                      a3*math.cos(2*math.pi*t3)
            
            wind[i] *= normalization;
        
        return wind
    
    # Properly windows and scales the data
    def _windowed_fft_mag(self, data):
        n = len(data)
        
        window = self._window_func(n)

        avg = np.mean(data)

        data = np.subtract(data, avg)
        
        if self.window_type is not None:
            window = self._window_func(n)
            data = np.multiply(data, window);
        
        fft_data = np.fft.fft(data)
        fft_data = fft_data[0:n/2+1]
        fft_norm = map(lambda x: 2*math.sqrt(np.real(x)**2 + np.imag(x)**2) / n, fft_data)
        fft_norm[0] /= 2;
        fft_norm[n/2] /=2
                
        return fft_norm
        
    def _get_dc_mask(self):
        if self.window_string is None:
            return 1
        elif self.window_string == 'HAMMING' or  self.window_string == 'HANN':
            return 2
        elif self.window_string == 'BLKHARRIS_92':
            return 4
        else:
            return 3
    
    # Returns the index of the maximum value in the data set
    def _get_index_of_max(self,data):
        index = 0
        max_value = data[index]
        for i, v in enumerate(data):
            if v > max_value:
                max_value = v
                index = i
        return index
    
    # creates subset of data according to indices
    def _index_subset(self, data, indices):
        return [data[i] for i in indices]
        
    def _get_power(self,bins):
        fundamental_index = self._get_index_of_max(self.fft_data)
        fundamemtal_bins = range(fundamental_index-self.BANDWIDTH, fundamental_index+self.BANDWIDTH+1)
        dc_bins = range(self._get_dc_mask()-self.BANDWIDTH+1,self._get_dc_mask()+self.BANDWIDTH+1)
        avg_noise = self.get_noise() / len(self.fft_data)
        
        peak_index = bins[self._get_index_of_max(self._index_subset(self.fft_data, bins))]
        peak_bins = range(peak_index-self.BANDWIDTH,peak_index+self.BANDWIDTH+1)
        peak_bins = self._set_diff(peak_bins,fundamemtal_bins)
        peak_bins = self._set_diff(peak_bins,dc_bins)
        
        raw_power = self._sum_of_squares(self._index_subset(self.fft_data, peak_bins))
        harmonic_noise = avg_noise * len(peak_bins)
        if raw_power > harmonic_noise:
            return raw_power - harmonic_noise
        else:
            return None
    
    def _make_unique(self,data):
        return list(set(data))
        
    def _set_diff(self, indices_a, indices_b):
        for b in indices_b:
            try:
                indices_a.remove(b)
            except:
                pass
        return indices_a
    
    def _mask_to_indices(self, mask):
        indices = []
        for i, m in enumerate(mask):
            if m == 1:
                indices.append(i)
        return indices
    
    def _sum_of_squares(self, data):
        total = 0
        for d in data:
            total += d * d
        return total
    
##############################################################################
###### END HAO'S STUFF ###### END HAO'S STUFF ###### END HAO'S STUFF #########
##############################################################################

#import os
#import serial
#import llt.common.dc890 as dc890
#import llt.common.constants as consts
import time

#from llt.demo_board_examples.ltc23xx.ltc2387.ltc2387_dc2290a_a import ltc2387_dc2290a_a
#from llt.demo_board_examples.ltc23xx.ltc2315.ltc2315_dc1563a_a import ltc2315_dc1563a_a
#from llt.demo_board_examples.ltc22xx.ltc2261.ltc2261_dc1369a_a import ltc2261_dc1369a_a
#from llt.demo_board_examples.ltc23xx.ltc2378.ltc2378_20_dc1925a_a import ltc2378_20_dc1925a_a
#from llt.demo_board_examples.ltc22xx.ltc2268.ltc2268_dc1532a   import ltc2268_dc1532a
#from llt.demo_board_examples.ltc2000.ltc2000_dc2085a_a import ltc2000_dc2085a_a

def read_file(filename):
    with open(filename) as f:
        return [float(line) for line in f]
        
def set_clocks():
    DC590_ID_STRING = "USBSPI,PIC,02,01,DC,DC590,----------------------\n\x00"
    DC1954_ID_STRING = "LTC6954-4,Cls,D6954,01,01,DC,DC1954A-D,---------\n\x00"
    for i in range(1,256):
        port = 'COM{}'.format(i)
        try:
            with serial.Serial(port, baudrate=115200, timeout=1) as ser:
                time.sleep(2)
                ser.readline() # hello
                ser.write("i\n")
                id_string = ser.read(50)
                if id_string == DC590_ID_STRING:
                    ser.write("I\n")
                    id_string = ser.read(50)
                    if id_string[:49] == DC1954_ID_STRING[:49]:
                        print "found linduino"
                        ser.write("MSGxS04S07S08S02S10S01XgS04S07S08S01S10S01G");
                    return True
        except:
            pass # move on to an open serial port
    return False
        
def test_sin(data, fundamental_bin, fundamental_db, snr_db, thd_db, big_min, small_max):
    
    print "min " , min(data)
    print "max " + str(max(data))    
    assert max(data) >= small_max, "max value too small"
    assert min(data) <= big_min, "min value too big"
    
    sp = sin_params(data, 18, [], window_string="BLKHARRIS_92", num_harmonics=8, thd_harmonics=5)
    mask = sp.get_auto_mask(8)
    mask = np.ones(len(mask)) - mask;
    sp = sin_params(data, 18, mask, window_string="BLKHARRIS_92", num_harmonics=8, thd_harmonics=5)
    
    print "fundimental bin" , sp.get_harmonic_bins()[0]
    assert sp.get_harmonic_bins()[0] == fundamental_bin, "bad fundamental bin"
    
    test_fun_db = sp.get_fundamental_dbfs()
    print "Fundimental dBfs ", test_fun_db
    #assert test_fun_db > fundamental_db - 1 and test_fun_db < fundamental_db + 1, "bad fundamental dbfs"

    test_snr_db = sp.get_snr_db()
    print "SNR " , test_snr_db
#    assert test_snr_db > snr_db - 1 and test_snr_db < snr_db + 5, "bad snr db"

    test_thd_db = sp.get_thd_db()
    print "THD " , test_thd_db
    assert test_thd_db < thd_db + 1 and test_thd_db > thd_db - 5, "bad thd db"
    
def test_dc2290a_a():
    """Tests DC718 > 16bits and write_to_file32_bits"""
    ltc2387_dc2290a_a()
    new_filename = "test_dc2290a_a_data.txt"
    os.rename("data.txt", new_filename)
    data = read_file(new_filename)
    test_sin(data, 100, -5, 80, -80, 100, 10000)
    
def test_dc1563a_a():
    """Tests DC718 <= 16 bits and write_to_file32_bits"""
    ltc2315_dc1563a_a()
    new_filename = "test_dc1563a_a_data.txt"
    os.rename("data.txt", new_filename)
    data = read_file(new_filename)
    test_sin(data, 100, -5, 80, -80, 100, 10000)
    
def test_dc1369a_a():
    """Tests DC890 <= 16 bits, write_to_file32_bits, fix_data bipolar, 
    fix_data unipolar(offset binary), fix_data random, and fix_data alt bit"""
    
    # basic, write_data    
    ltc2261_dc1369a_a()
    new_filename = "test_dc1563a_a_data.txt"
    os.rename("data.txt", new_filename)
    data = read_file(new_filename)
    test_sin(data, 100, -5, 80, -80, 100, 1000)    
    
    # bipolar
    NUM_SAMPLES = 32 * 1024
    spi_reg = [ # addr, value
                  0x00, 0x80,
                  0x01, 0x00,
                  0x02, 0x00,
                  0x03, 0x71,
                  0x04, 0x01 # 2's complement
              ]
    with dc890.Demoboard(dc_number         = 'DC1369A-A', 
                         fpga_load         = 'DLVDS',
                         num_channels      = 2,
                         is_positive_clock = True, 
                         num_bits          = 14,
                         alignment         = 14,
                         is_bipolar        = True,
                         spi_reg_values    = spi_reg,
                         verbose           = False) as controller:
        data = controller.collect(NUM_SAMPLES, consts.TRIGGER_NONE)
        data = data[0] # Keep only one channel
        test_sin(data, 100, -5, 80, -80, 100, 10000) 
        
    # random
    NUM_SAMPLES = 32 * 1024
    spi_reg = [ # addr, value
                  0x00, 0x80,
                  0x01, 0x00,
                  0x02, 0x00,
                  0x03, 0x71,
                  0x04, 0x02 # randomizer
              ]
    with dc890.Demoboard(dc_number         = 'DC1369A-A', 
                         fpga_load         = 'DLVDS',
                         num_channels      = 2,
                         is_positive_clock = True, 
                         num_bits          = 14,
                         alignment         = 14,
                         is_bipolar        = False,
                         spi_reg_values    = spi_reg,
                         verbose           = False) as controller:
        data = controller.collect(NUM_SAMPLES, consts.TRIGGER_NONE, 5, True)
        data = data[0] # Keep only one channel
        test_sin(data, 100, -5, 80, -80, 100, 10000)
        
    # alt bit
    NUM_SAMPLES = 32 * 1024
    spi_reg = [ # addr, value
                  0x00, 0x80,
                  0x01, 0x00,
                  0x02, 0x00,
                  0x03, 0x71,
                  0x04, 0x04 # alt bit
              ]
    with dc890.Demoboard(dc_number = 'DC1369A-A', 
                         fpga_load             = 'DLVDS',
                         num_channels          = 2,
                         is_positive_clock     = True, 
                         num_bits              = 14,
                         alignment             = 14,
                         is_bipolar            = True,
                         spi_reg_values        = spi_reg,
                         verbose               = False) as controller:
        data = controller.collect(NUM_SAMPLES, consts.TRIGGER_NONE, 5, False, True)
        data = data[0] # Keep only one channel
        test_sin(data, 100, -5, 80, 80, 100, 10000) 
    
def test_dc1925a_a():
    """Tests write_to_file_32_bit, fix_data bipolar, DC890 > 16 bits"""
    #ltc2378_20_dc1925a_a(8*1024,[],False,True,True)
    new_filename = "test_dc1925a_a_data.txt"
    #os.rename("data.txt", new_filename)
    data = read_file(new_filename)
    #os.remove(new_filename)
    test_sin(data, 207, -9, 90, -87, -182400, 182400)
    
def test_dc1532a_a():
    """Tests write_to_file_32_bit, write_channels_to_file_32_bit, DC1371"""
    ltc2268_dc1532a()
    new_filename = "test_dc1532a_a_data.txt"
    os.rename("data.txt", new_filename)
    data = read_file(new_filename)
    os.remove(new_filename)
    test_sin(data, 100, -5, 80, -80, 100, 10000)
    
def test_dc2085a_a():
    """Tests write_to_file, UFO"""
    ltc2000_dc2085a_a()
    new_filename = "test_dc2085a_a_data.txt"
    os.rename("data.txt", new_filename)
    data = read_file(new_filename)
    test_sin(data, 100, -5, 80, -80, 100, 10000)
    
if __name__ == '__main__':
    #print "set Clocks"
    #set_clocks()

    
    test_dc1925a_a()
    print "done"