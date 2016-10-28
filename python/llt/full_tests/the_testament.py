# -*- coding: utf-8 -*-
"""
Created on Fri Sep 30 09:40:32 2016

@author: jeremy_s
"""

from llt.utils.sin_params import sin_params

import os
import llt.common.dc890 as dc890
import llt.common.constants as consts
import time
import llt.common.functions as funcs
import llt.utils.connect_to_linduino as duino
import math as m

from llt.demo_board_examples.ltc23xx.ltc2387.ltc2387_dc2290a_a import ltc2387_dc2290a_a
from llt.demo_board_examples.ltc23xx.ltc2315.ltc2315_dc1563a_a import ltc2315_dc1563a_a
from llt.demo_board_examples.ltc22xx.ltc2261.ltc2261_dc1369a_a import ltc2261_dc1369a_a
from llt.demo_board_examples.ltc23xx.ltc2378.ltc2378_20_dc1925a_a import ltc2378_20_dc1925a_a
from llt.demo_board_examples.ltc22xx.ltc2268.ltc2268_dc1532a import ltc2268_dc1532a

def read_file(filename):
    with open(filename) as f:
        return [float(line) for line in f]
       
def test_sin(data, num_bits, ex_fund_bin, ex_fund, ex_snr, ex_thd, ex_min, ex_max):    
    min_val = min(data)
    max_val = max(data)
    harmonics, snr, thd, _, _, _ = sin_params(data)
    fund, fund_bin = harmonics[1]
    fund = 10*m.log10(fund) - 20*m.log10(2**(num_bits - 1))

    print "min ", min_val
    print "max ", max_val    
    print "fundimental bin" , fund_bin
    print "Fundimental dBfs ", fund
    print "SNR " , snr
    print "THD " , thd

    assert min_val <= ex_min, "min value too big"
    assert max_val >= ex_max, "max value too small"
    assert fund_bin == ex_fund_bin, "bad fundamental bin"
    assert fund > ex_fund - 1 and fund < ex_fund + 1, "bad fundamental dbfs"    
    #assert snr > ex_snr - 1 and snr < ex_snr + 5, "bad snr db"
    assert thd < ex_thd + 20 and thd > ex_thd - 10, "bad thd db"

def test_dc2290a_a(linduino):
    """Tests DC718 > 16bits and write_to_file32_bits"""
    print "########################"
    print "#### TEST DC2290A-A ####"
    print "########################"
    linduino.transfer_packets("K01K02K10\n")
    time.sleep(5)
    ltc2387_dc2290a_a(64*1024, True, True, True)
    new_filename = "test_dc2290a_a_data.txt"
    os.rename("data.txt", new_filename)
    data = read_file(new_filename)
    os.remove(new_filename)
    test_sin(data, 18, 18, -7, 66, -70, -55500, 55500)
    print
    
def test_dc1563a_a(linduino):
    """Tests DC718 <= 16 bits and write_to_file32_bits"""
    print "########################"
    print "#### TEST DC1563A-A ####"
    print "########################"
    linduino.transfer_packets("K00K02K11\n")
    time.sleep(5)
    ltc2315_dc1563a_a(32*1024, False, True, True)
    new_filename = "test_dc1563a_a_data.txt"
    os.rename("data.txt", new_filename)
    data = read_file(new_filename)
    os.remove(new_filename)
    test_sin(data, 12, 23, -1, 64, -63, 300, 3500)
    print
    
def test_dc1369a_a():
    """Tests DC890 <= 16 bits, write_to_file32_bits, fix_data bipolar, 
    fix_data unipolar(offset binary), fix_data random, and fix_data alt bit"""
    print "########################"
    print "#### TEST D1369A-A ####"
    print "########################"
    
    # basic, write_data
    print "\nNormal:\n-------"
    NUM_SAMPLES = 8 * 1024
    spi_reg = [ # addr, value
                  0x00, 0x80,
                  0x01, 0x00,
                  0x02, 0x00,
                  0x03, 0x71,
                  0x04, 0x00 # offset binary
              ]
    ltc2261_dc1369a_a(NUM_SAMPLES,spi_reg,False,True,True)
    new_filename = "test_dc1563a_a_data.txt"
    os.rename("data.txt", new_filename)
    data = read_file(new_filename)
    os.remove(new_filename)
    test_sin(data, 14, 2412, -1, 71, -84, 1400, 15000)    
    
    # bipolar
    print "\nBipolar:\n--------"
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
    test_sin(data, 14, 2412, -1, 71, -84, -6500, 6500) 
        
    # random
    print "\nRandomizer:\n-----------"
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
    test_sin(data, 14, 2412, -1, 71, -84, 1400, 15000)
        
    # alt bit
    print "\nAlternate Bit:\n--------------"
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
                         is_bipolar            = False,
                         spi_reg_values        = spi_reg,
                         verbose               = False) as controller:
        data = controller.collect(NUM_SAMPLES, consts.TRIGGER_NONE, 5, False, True)
        data = data[0] # Keep only one channel
    funcs.plot_channels(controller.get_num_bits(), data)    
    test_sin(data, 14, 2412, -1, 71, -84, 1400, 15000)
    print
    
def test_dc1925a_a(linduino):
    """Tests write_to_file_32_bit, fix_data bipolar, DC890 > 16 bits"""
    print "########################"
    print "#### TEST DC1925A-A ####"
    print "########################"
    linduino.transfer_packets("K00K01K12\n")
    time.sleep(5)
    ltc2378_20_dc1925a_a(8*1024,[],False,True,True)
    new_filename = "test_dc1925a_a_data.txt"
    os.rename("data.txt", new_filename)
    data = read_file(new_filename)
    os.remove(new_filename)
    test_sin(data, 20, 52, -9, 80, -75, -120000, 120000)
    print
    
def test_dc1532a_a():
    """Tests write_to_file_32_bit, write_channels_to_file_32_bit, DC1371"""
    print "########################"
    print "#### TEST DC1532A-A ####"
    print "########################"
    spi_reg = [ # addr, value
                  0x00, 0x80,
                  0x01, 0x00,
                  0x02, 0x00,
                  0x03, 0x00,
                  0x04, 0x00
              ]
    ltc2268_dc1532a(8*1024, spi_reg, False, True, True)
    new_filename = "test_dc1532a_a_data.txt"
    os.rename("data.txt", new_filename)
    data = read_file(new_filename)
    data = data[:8*1024]
    os.remove(new_filename)
    test_sin(data, 14, 2412, -16, 57, -78, 7000, 9200)
    print
    
def test_dc2085a_a():
    """Tests write_to_file, UFO"""
    print "########################"
    print "#### TEST DC2085A-A ####"
    print "########################"
    # funky way to run the script
    import llt.demo_board_examples.ltc2000.ltc2000_dc2085
    # get rid of unused import warning
    assert llt.demo_board_examples.ltc2000.ltc2000_dc2085
    spi_reg = [ # addr, value
                  0x00, 0x80,
                  0x01, 0x00,
                  0x02, 0x00,
                  0x03, 0x00,
                  0x04, 0x00
              ]
    ch0, data = ltc2268_dc1532a(8*1024, spi_reg, False, True, True)
    test_sin(data, 14, 2500, -14, 57, -80, 6800, 9400)
    
if __name__ == '__main__':

    with duino.Linduino() as linduino: # Look for the DC2026
        print "set Clocks"
        linduino.transfer_packets("MSGxS04S07S08S02S0CS01XgS04S0ES08S01S0CS01G");
        linduino.transfer_packets("K00K01K02\n")
        #linduino = None # DELETE THIS
        test_dc2290a_a(linduino)
        test_dc1925a_a(linduino)
        test_dc1369a_a()
        test_dc1563a_a(linduino)
        test_dc1532a_a()
        test_dc2085a_a()
        
        linduino.transfer_packets("K00K01K02\n")

    print "done"