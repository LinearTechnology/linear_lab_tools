# -*- coding: utf-8 -*-
"""
Created on Sat Aug 15 07:49:26 2015

@author: markthoren
"""
import ltc_controller_comm as comm

from time import sleep
sleep_time = 0.1

# FPGA register addresses
ID_REG = 0x00
CAPTURE_CONFIG_REG = 0x01
CAPTURE_CONTROL_REG = 0x02
CAPTURE_RESET_REG = 0x03
CAPTURE_STATUS_REG = 0x04
SPI_CONFIG_REG = 0x05
CLOCK_STATUS_REG = 0x06
JESD204B_WB0_REG = 0x07
JESD204B_WB1_REG = 0x08
JESD204B_WB2_REG = 0x09
JESD204B_WB3_REG = 0x0A
JESD204B_CONFIG_REG = 0x0B
JESD204B_RB0_REG = 0x0C
JESD204B_RB1_REG = 0x0D
JESD204B_RB2_REG = 0x0E
JESD204B_RB3_REG = 0x0F
JESD204B_CHECK_REG = 0x10

JESD204B_W2INDEX_REG = 0x12
JESD204B_R2INDEX_REG = 0x13

# LTC6951 register definitions
REG_LOCK_STAT = 0x00
REG_STAT_MASK = 0x01
REG_PD_SS_CAL = 0x02
REG_ALC_REF   = 0x03
REG_BD_LK     = 0x04
REG_RD_ND_HI  = 0x05
REG_ND_LOW    = 0x06
REG_CP_CTRL   = 0x07
REG_PD_MUTE   = 0x08
REG_OUT0_DIV  = 0x09
REG_OUT0_DLY  = 0x0A
REG_OUT1_DIV  = 0x0B
REG_OUT1_DLY  = 0x0C
REG_OUT2_DIV  = 0x0D
REG_OUT2_DLY  = 0x0E
REG_OUT3_DIV  = 0x0F
REG_OUT3_DLY  = 0x10
REG_OUT4_DIV  = 0x11
REG_OUT4_DLY  = 0x12
REG_REV_PART  = 0x13

def read_LTC6951_reg_dump(filename, verbose = True):
    infile = open(filename, 'r')
    infile.readline() # Read out four header lines
    infile.readline()
    infile.readline()
    infile.readline()
    instring = infile.readline()
    infile.close()
    insplitdata = instring.split(',') # Fifth line has all register values separated by a comma and space...
    reg_vals = [0] * len(insplitdata)
    for i in range(0, len(insplitdata)-1): # Parse out registers into list of ints
        reg_vals[i] = int(insplitdata[i],16)
    if(verbose == True):
        print('Instring:')
        print instring
        print('Indata (split string):')
        print insplitdata  
        print('register values:')
        print reg_vals
    return reg_vals

def initialize_DC2226_version2_clocks_250(device, verbose):
    if(verbose != 0):
        print "Configuring clock generators over SPI:"
    device.hs_set_bit_mode(comm.HS_BIT_MODE_MPSSE)

    #LTC6954 config
    print "Configuring LTC6954 (REF distribution)"
    device.hs_fpga_write_data_at_address(SPI_CONFIG_REG, 0x04)

    device.spi_send_byte_at_address(0x00 << 1, 0x00)
    device.spi_send_byte_at_address(0x01 << 1, 0x80) # 6951-1 delay
    device.spi_send_byte_at_address(0x02 << 1, 0x01) # 6951-1 divider
    device.spi_send_byte_at_address(0x03 << 1, 0x80) # 6951-2 delay
    device.spi_send_byte_at_address(0x04 << 1, 0x01) # 6951-2 divider
    device.spi_send_byte_at_address(0x05 << 1, 0xC0) # sync delay & CMSINV
    device.spi_send_byte_at_address(0x06 << 1, 0x01) # sync divider
    device.spi_send_byte_at_address(0x07 << 1, 0x21) #
    print "Configuring U10 (LTC6951) cp"
#LTC6951config
    device.hs_fpga_write_data_at_address(SPI_CONFIG_REG, 0x02)
    device.spi_send_byte_at_address(0x00 << 1, 0x05) #
    device.spi_send_byte_at_address(0x01 << 1, 0xBA) #
    device.spi_send_byte_at_address(0x02 << 1, 0x00) #
    device.spi_send_byte_at_address(0x03 << 1, 0x7C) #
    device.spi_send_byte_at_address(0x04 << 1, 0xA3) #
    device.spi_send_byte_at_address(0x05 << 1, 0x08) #
    device.spi_send_byte_at_address(0x06 << 1, 0x05) # 5 for 200, 6 for 300. VCO=2GHz.
    device.spi_send_byte_at_address(0x07 << 1, 0x07) #
    device.spi_send_byte_at_address(0x08 << 1, 0x01) #
    device.spi_send_byte_at_address(0x09 << 1, 0x13) #
    device.spi_send_byte_at_address(0x0A << 1, 0xC0) #
    device.spi_send_byte_at_address(0x0B << 1, 0x9B) # ADC SYSREF 2 div, 
    device.spi_send_byte_at_address(0x0C << 1, 0x16) # ADC SYSREF 2 delay, - 16 for 250, 1E f0r 300
#    device.spi_send_byte_at_address(0x0D << 1, 0x93) # FPGA CLK div, 
    device.spi_send_byte_at_address(0x0D << 1, 0x95) # FPGA CLK div, 0x95 for half of 250
#    device.spi_send_byte_at_address(0x0D << 1, 0x97) # FPGA CLK div,  0x97 for 1/4 of 250...
    device.spi_send_byte_at_address(0x0E << 1, 0x16) # FPGA CLK delay, 16 for 250, 1E for 300
    device.spi_send_byte_at_address(0x0F << 1, 0x93) #  ADC CLK 2 div,
    device.spi_send_byte_at_address(0x10 << 1, 0x16) #  ADC CLK 2 delay ,16 for 250, 1E for 300
    device.spi_send_byte_at_address(0x11 << 1, 0x30) #
    device.spi_send_byte_at_address(0x12 << 1, 0x00) #
    device.spi_send_byte_at_address(0x13 << 1, 0x11) #
    device.spi_send_byte_at_address(0x02 << 1, 0x01) # calibrate after writing all registers
	
    print "Configuring U13 (LTC6951) cp"
#LTC6951config
    device.hs_fpga_write_data_at_address(SPI_CONFIG_REG, 0x03)
    device.spi_send_byte_at_address(0x00 << 1, 0x05) #
    device.spi_send_byte_at_address(0x01 << 1, 0xBA) #
    device.spi_send_byte_at_address(0x02 << 1, 0x00) #
    device.spi_send_byte_at_address(0x03 << 1, 0x7C) #
    device.spi_send_byte_at_address(0x04 << 1, 0xA3) #
    device.spi_send_byte_at_address(0x05 << 1, 0x08) #
    device.spi_send_byte_at_address(0x06 << 1, 0x05) # 5 for 250, 6 for 300
    device.spi_send_byte_at_address(0x07 << 1, 0x07) #
    device.spi_send_byte_at_address(0x08 << 1, 0x01) #
    device.spi_send_byte_at_address(0x09 << 1, 0x13) #
    device.spi_send_byte_at_address(0x0A << 1, 0xC0) #
    device.spi_send_byte_at_address(0x0B << 1, 0x9B) # FPGA SYSREF div, 
    device.spi_send_byte_at_address(0x0C << 1, 0x16) # FPGA SYSREF delay, 16 for 250, 1E f0r 300
    device.spi_send_byte_at_address(0x0D << 1, 0x93) # ADC CLK 1 div,
    device.spi_send_byte_at_address(0x0E << 1, 0x16) # ADC CLK 1 delay, 16 for 250, 1E for 300
    device.spi_send_byte_at_address(0x0F << 1, 0x9B) # ADC SYSREF 1 div,
    device.spi_send_byte_at_address(0x10 << 1, 0x16) # ADC SYSREF 1 delay, 16 for 250, 1E for 300
    device.spi_send_byte_at_address(0x11 << 1, 0x30) #
    device.spi_send_byte_at_address(0x12 << 1, 0x00) #
    device.spi_send_byte_at_address(0x13 << 1, 0x11) #
    device.spi_send_byte_at_address(0x02 << 1, 0x01) # calibrate after writing all registers

    print "toggle SYNC cp"
    # only toggle LTC6951 sync (LTC6954 does not need a sync with DIV=1)
    sleep(sleep_time)
    device.hs_fpga_write_data_at_address(SPI_CONFIG_REG, 0x08)
    print "sync high"
    sleep(sleep_time)
    print "sync low"
    device.hs_fpga_write_data(0x00)
    sleep(sleep_time)

def initialize_DC2226_version2_clocks_300(device, verbose):
    if(verbose != 0):
        print "Configuring clock generators over SPI:"
    device.hs_set_bit_mode(comm.HS_BIT_MODE_MPSSE)

    #LTC6954 config
    print "Configuring LTC6954 (REF distribution)"
    device.hs_fpga_write_data_at_address(SPI_CONFIG_REG, 0x04)

    device.spi_send_byte_at_address(0x00 << 1, 0x00)
    device.spi_send_byte_at_address(0x01 << 1, 0x80) # 6951-1 delay
    device.spi_send_byte_at_address(0x02 << 1, 0x01) # 6951-1 divider
    device.spi_send_byte_at_address(0x03 << 1, 0x80) # 6951-2 delay
    device.spi_send_byte_at_address(0x04 << 1, 0x01) # 6951-2 divider
    device.spi_send_byte_at_address(0x05 << 1, 0xC0) # sync delay & CMSINV
    device.spi_send_byte_at_address(0x06 << 1, 0x01) # sync divider
    device.spi_send_byte_at_address(0x07 << 1, 0x21) #
    print "Configuring U10 (LTC6951) cp"
#LTC6951config
#    device.FPGAWriteAddress(SPI_CONFIG_REG)
#    device.FPGAWriteData(0x02) ## VERIFIED!! ##
    device.hs_fpga_write_data_at_address(SPI_CONFIG_REG, 0x02)
    device.spi_send_byte_at_address(0x00 << 1, 0x05) #
    device.spi_send_byte_at_address(0x01 << 1, 0xBA) #
    device.spi_send_byte_at_address(0x02 << 1, 0x00) #
    device.spi_send_byte_at_address(0x03 << 1, 0x7C) #
    device.spi_send_byte_at_address(0x04 << 1, 0xA3) #
    device.spi_send_byte_at_address(0x05 << 1, 0x08) #
    device.spi_send_byte_at_address(0x06 << 1, 0x06) # 5 for 200, 6 for 300
    device.spi_send_byte_at_address(0x07 << 1, 0x07) #
    device.spi_send_byte_at_address(0x08 << 1, 0x01) #
    device.spi_send_byte_at_address(0x09 << 1, 0x13) #
    device.spi_send_byte_at_address(0x0A << 1, 0xC0) #
    device.spi_send_byte_at_address(0x0B << 1, 0x9B) #
    device.spi_send_byte_at_address(0x0C << 1, 0x1E) # 16 for 250, 1E f0r 300
    device.spi_send_byte_at_address(0x0D << 1, 0x93) #
    device.spi_send_byte_at_address(0x0E << 1, 0x1E) # 16 for 250, 1E for 300
    device.spi_send_byte_at_address(0x0F << 1, 0x93) #
    device.spi_send_byte_at_address(0x10 << 1, 0x1E) # 16 for 250, 1E for 300
    device.spi_send_byte_at_address(0x11 << 1, 0x30) #
    device.spi_send_byte_at_address(0x12 << 1, 0x00) #
    device.spi_send_byte_at_address(0x13 << 1, 0x11) #
    device.spi_send_byte_at_address(0x02 << 1, 0x01) # calibrate after writing all registers
	
    print "Configuring U13 (LTC6951) cp"
#LTC6951config
#    device.FPGAWriteAddress(SPI_CONFIG_REG)
#    device.FPGAWriteData(0x03) ## VERIFIED!! ##
    device.hs_fpga_write_data_at_address(SPI_CONFIG_REG, 0x03)

    device.spi_send_byte_at_address(0x00 << 1, 0x05) #
    device.spi_send_byte_at_address(0x01 << 1, 0xBA) #
    device.spi_send_byte_at_address(0x02 << 1, 0x00) #
    device.spi_send_byte_at_address(0x03 << 1, 0x7C) #
    device.spi_send_byte_at_address(0x04 << 1, 0xA3) #
    device.spi_send_byte_at_address(0x05 << 1, 0x08) #
    device.spi_send_byte_at_address(0x06 << 1, 0x06) # 5 for 250, 6 for 300
    device.spi_send_byte_at_address(0x07 << 1, 0x07) #
    device.spi_send_byte_at_address(0x08 << 1, 0x01) #
    device.spi_send_byte_at_address(0x09 << 1, 0x13) #
    device.spi_send_byte_at_address(0x0A << 1, 0xC0) #
    device.spi_send_byte_at_address(0x0B << 1, 0x9B) #
    device.spi_send_byte_at_address(0x0C << 1, 0x1E) # 16 for 250, 1E f0r 300
    device.spi_send_byte_at_address(0x0D << 1, 0x93) #
    device.spi_send_byte_at_address(0x0E << 1, 0x1E) # 16 for 250, 1E for 300
    device.spi_send_byte_at_address(0x0F << 1, 0x9B) #
    device.spi_send_byte_at_address(0x10 << 1, 0x1E) # 16 for 250, 1E for 300
    device.spi_send_byte_at_address(0x11 << 1, 0x30) #
    device.spi_send_byte_at_address(0x12 << 1, 0x00) #
    device.spi_send_byte_at_address(0x13 << 1, 0x11) #
    device.spi_send_byte_at_address(0x02 << 1, 0x01) # calibrate after writing all registers

    print "toggle SYNC cp"
    sleep(sleep_time)
    # only toggle LTC6951 sync (LTC6954 does not need a sync with DIV=1)
    device.hs_fpga_write_data_at_address(SPI_CONFIG_REG, 0x08)
    print "sync high"
    sleep(sleep_time)
    print "sync low"
    device.hs_fpga_write_data(0x00)
    sleep(sleep_time)

if __name__ == "__main__":
    U10_regs = read_LTC6951_reg_dump('dc2226_clock_set_files/ltc6951_dc2226a_u10.txt', verbose = False)
    U13_regs = read_LTC6951_reg_dump('dc2226_clock_set_files/ltc6951_dc2226a_u13.txt', verbose = False)
    print("U10 Registers:")
    for i in range(len(U10_regs)):
        print "{0:02X}".format(U10_regs[i])
    print("U13 Registers:")
    for i in range(len(U13_regs)):
        print "{0:02X}".format(U13_regs[i])
