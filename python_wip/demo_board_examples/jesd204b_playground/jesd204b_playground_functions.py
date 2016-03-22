'''
JESD205B playground demo system support functions

Tested with Python 2.7, Anaconda distribution available from Continuum Analytics,
http://www.continuum.io/

Demo board documentation:
http://www.linear.com/demo/xxxx
http://www.linear.com/product/xxxx#demoboards

LTCxxxx product page
http://www.linear.com/product/LTCxxxx

REVISION HISTORY
$Revision: 4255 $
$Date: 2015-10-19 13:09:55 -0700 (Mon, 19 Oct 2015) $

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

import sys
sys.path.append("../../")
import ltc_controller_comm as comm

import time

from time import sleep

sleeptime = 0.1

# Set up JESD204B parameters
M = 12		# Converters per device
N = 16 		# Converter resolution
Nt = 16		# Total bits per sample
CS = 0		# Control Bits per sample
did=0x42 # Device ID (programmed into ADC, read back from JEDEC core)
bid=0x0A # Bank      (                 "                            )
K=16     # Frames per multiframe (subclass 1 only)
LIU = 12  # Lanes in use minus 1
modes = 0x00 # Enable FAM, LAM (Frame / Lane alignment monitorning)
#modes = 0x18 #Disable FAM, LAM (for testing purposes)

# FPGA register addresses
ID_REG = 0x00

TX_PBK_CONFIG_REG = 0x01   
TX_CLOCK_STATUS_REG = 0x02
TX_DEV_CONTROL_REG = 0x03
TX_PBK_RESET_REG = 0x04 
TX_PBK_STATUS_REG = 0x05 
TX_SPI_CONFIG_REG = 0x06
     
RX_CAPTURE_CONFIG_REG = 0x01    
RX_CAPTURE_CONTROL_REG = 0x02
RX_CAPTURE_RESET_REG = 0x03
RX_CAPTURE_STATUS_REG = 0x04
RX_SPI_CONFIG_REG = 0x05
RX_CLOCK_STATUS_REG = 0x06


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
I2C_ACCESS_REG = 0x11
JESD204B_W2INDEX_REG = 0x12
JESD204B_R2INDEX_REG = 0x13

# Register names for basic configuration
JESD204B_XILINX_CONFIG_REG_NAMES = ["             Version", "               Reset", "         ILA Support", "          Scrambling",
                                    "     SYSREF Handling", "         Reserved...", "          Test Modes", "  Link err stat, 0-7",
                                    "        Octets/frame", "frames/multiframe(K)", "        Lanes in Use", "            Subclass",
                                    "        RX buf delay", "     Error reporting", "         SYNC Status", " Link err stat, 8-11"]

# Register names for per-lane information
JESD204B_XILINX_LANE_REG_NAMES = ["                  ILA config Data 0", "                  ILA config Data 1", "                  ILA config Data 2", "                  ILA config Data 3", 
                                  "                  ILA config Data 4", "                  ILA config Data 5", "                  ILA config Data 6", "                  ILA config Data 7", 
                                  "                  Test Mode Err cnt", "                       Link Err cnt", "                  Test Mode ILA cnt", "                Tst Mde multif. cnt",
                                  "                      Buffer Adjust"]


MOD_RPAT = [0xBE, 0xD7, 0x23, 0x47, 0x6B, 0x8F, 0xB3, 0x14, 0x5E, 0xFB, 0x35, 0x59]

# LTC212x register defines
ONELANE = 0x00
TWOLANES = 0x01
FOURLANES = 0x03

class NumSamp:
    def __init__(self, memSize, buffSize):
        self.MemSize = memSize
        self.BuffSize = buffSize
    
NumSamp128  = NumSamp(0x00, 128)
NumSamp256  = NumSamp(0x10, 256)
NumSamp512  = NumSamp(0x20, 512)
NumSamp1K   = NumSamp(0x30, 1024)
NumSamp2K   = NumSamp(0x40, 2 * 1024)
NumSamp4K   = NumSamp(0x50, 4 * 1024)
NumSamp8K   = NumSamp(0x60, 8 * 1024)
NumSamp16K  = NumSamp(0x70, 16 * 1024)
NumSamp32K  = NumSamp(0x80, 32 * 1024)
NumSamp64K  = NumSamp(0x90, 64 * 1024)
NumSamp128K = NumSamp(0xA0, 128 * 1024)


def reset_fpga(device):
    device.hs_set_bit_mode(comm.HS_BIT_MODE_MPSSE)
    device.hs_fpga_toggle_reset()
    time.sleep(.01)

# Adding support for V6 core, with true AXI access. Need to confirm that this doesn't break anything with V4 FPGA loads,
# as we'd be writing to undefined registers.
def write_jesd204b_reg(device, address, b3, b2, b1, b0):
    device.hs_fpga_write_data_at_address(JESD204B_WB3_REG, b3)
    device.hs_fpga_write_data_at_address(JESD204B_WB2_REG, b2)
    device.hs_fpga_write_data_at_address(JESD204B_WB1_REG, b1)
    device.hs_fpga_write_data_at_address(JESD204B_WB0_REG, b0)
    device.hs_fpga_write_data_at_address(JESD204B_W2INDEX_REG, (address & 0xFC0)>>6) # Upper 6 bits of AXI reg address
    device.hs_fpga_write_data_at_address(JESD204B_CONFIG_REG, ((address & 0x3F)<<2 | 0x02))
    if device.hs_fpga_read_data() & 0x01 == 0:
        raise RuntimeError("Got bad FPGA status in write_jedec_reg")

# Adding support for V6 core, with true AXI access. Need to confirm that this doesn't break anything with V4 FPGA loads,
# as we'd be writing to undefined registers.
def read_jesd204b_reg(device, address):
    device.hs_fpga_write_data_at_address(JESD204B_R2INDEX_REG, (address & 0xFC0)>>6) # Upper 6 bits of AXI reg address
    device.hs_fpga_write_data_at_address(JESD204B_CHECK_REG, ((address & 0x3F)<<2 | 0x02)) # Lower 6 bits address of JESD204B Check Register

    if device.hs_fpga_read_data() & 0x01 == 0:
        raise RuntimeError("Got bad FPGA status in read_jedec_reg")

    b3 = device.hs_fpga_read_data_at_address(JESD204B_RB3_REG)
    b2 = device.hs_fpga_read_data_at_address(JESD204B_RB2_REG)
    b1 = device.hs_fpga_read_data_at_address(JESD204B_RB1_REG)
    b0 = device.hs_fpga_read_data_at_address(JESD204B_RB0_REG)
    return b3, b2, b1, b0

def read_xilinx_core_config(device, verbose = True, read_link_erroe = False):
    if(verbose == True):
        print("\nJEDEC core config registers:")
    for i in range(0, 16):
        reg = i*4
        byte3, byte2, byte1, byte0 = read_jesd204b_reg(device, reg)
        if(reg == 0x1C):
            err_status1 = (byte0 | (byte1 << 8) | (byte2 << 16) | (byte3 << 24))
        if(verbose == True):                
            print JESD204B_XILINX_CONFIG_REG_NAMES[i] + ": " + ' {:02X} {:02X} {:02X} {:02X}'.format(byte3, byte2, byte1, byte0)        
    if(read_link_erroe == True):
        err_status2 = (byte0 | (byte1 << 8))
        check_link_error_status(err_status1, err_status2)

def read_xilinx_core_ilas(device, verbose = True, lane = 0, split_all = False):
    startreg = 0x800 + (lane * 0x040)
    print("\nILAS and stuff for lane " + str(lane) + ":")
    print("Starting Register: " + "{:04X}".format(startreg))
    for i in range(0, 13):
        reg = startreg + i*4
        byte3, byte2, byte1, byte0 = read_jesd204b_reg(device, reg)    
        print "\n" + JESD204B_XILINX_LANE_REG_NAMES[i] + ": " + ' {:02X} {:02X} {:02X} {:02X}'.format(byte3, byte2, byte1, byte0)
        
        if(split_all == True):
            if(i ==0):
                data = byte1 & 0x07
                if(data == 0x01):
                    print "                   JESD204B version:  " + str(data) + "\t\tPASS"
                else:
                    print "                   JESD204B version:  " + str(data) + "\t\tFAIL"
            elif(i == 1):
                data = (byte0 & 0xFF) + 1
                if(data == 2):
                    print "               F (Octets per frame):  " + str(data) + "\t\tPASS"
                else:
                    print "               F (Octets per frame):  " + str(data) + "\t\tFAIL"
            elif(i == 2):
                data = (byte0 & 0x1F) + 1
                if(data == 32):
                    print "          K (Frames per multiframe):  " + str(data) + "\t\tPASS"
                else:
                    print "          K (Frames per multiframe):  " + str(data) + "\t\tFAIL"
                
            elif(i == 3):
                data = byte0 & 0xFF
                if(data == did):
                    print "                    DID (Device ID):  0x" + '{:02X}'.format(data) + "\t\tPASS"
                else:
                    print "                    DID (Device ID):  0x" + '{:02X}'.format(data) + "\t\tFAIL"
                
                data = byte1 & 0x0F
                if(data == bid):
                    print "                      BID (Bank ID):  0x" + '{:02X}'.format(data) + "\t\tPASS"
                else:
                    print "                      BID (Bank ID):  0x" + '{:02X}'.format(data) + "\t\tFAIL"
                
                data = byte2 & 0x1F
                if(data == lane):
                    print "                      LID (Lane ID):  " + str(data) + "\t\tPASS"
                else:
                    print "                      LID (Lane ID):  " + str(data) + "\t\tFAIL"
                
                data = (byte3 & 0x1F) + 1
                if(data == LIU):
                    print "                 L (Lanes per link):  " + str(data) + "\t\tPASS"
                else:
                    print "                 L (Lanes per link):  " + str(data) + "\t\tFAIL"
                
                
            elif(i == 4):
                data = (byte0 & 0xFF) + 1
                if(data == M):
                    print "          M (Convertors per device):  " + str(data) + "\t\tPASS"
                else:
                    print "          M (Convertors per device):  " + str(data) + "\t\tFAIL"
                
                data = (byte1 & 0x1F) + 1
                if(data == N):
                    print "           N (Convertor resolution):  " + str(data) + "\t\tPASS"
                else:
                    print "           N (Convertor resolution):  " + str(data) + "\t\tFAIL"
                
                data = (byte2 & 0x1F) + 1
                if(data == Nt):
                    print "         N' (Total bits per sample):  " + str(data) + "\t\tPASS"
                else:
                    print "         N' (Total bits per sample):  " + str(data) + "\t\tFAIL"
                
                data = byte3 & 0x03
                if(data == CS):
                    print "       CS (Control bits per sample):  " + str(data) + "\t\tPASS"
                else:
                    print "       CS (Control bits per sample):  " + str(data) + "\t\tFAIL"
 
            elif(i == 5):
                data = byte0 & 0x01
                if(data == 1):
                    print "            SCR (Scrambling enable):  " + str(data) + "\t\tENABLED"
                else:
                    print "            SCR (Scrambling enable):  " + str(data) + "\t\tDISABLED"
                
                data = byte1 & 0x1F
                if(data == 0):
                    print "S (Samples per convertor per frame):  " + str(data) + "\t\tPASS"
                else:
                    print "S (Samples per convertor per frame):  " + str(data) + "\t\tFAIL"
                
                data = byte2 & 0x01
                if(data == 0):
                    print "           HD (High Density format):  " + str(data) + "\t\tPASS"
                else:
                    print "           HD (High Density format):  " + str(data) + "\t\tFAIL"
                
                data = byte3 & 0x1F
                if(data == 0):
                    print "       CF (Control Words per frame):  " + str(data) + "\t\tPASS"
                else:
                    print "       CF (Control Words per frame):  " + str(data) + "\t\tFAIL"
                    
            elif(i == 6):
                data = byte2 & 0xFF
                print "                    FCHK (Checksum):  0x" + '{:02X}'.format(data)
            elif(i == 7):
                data = byte0 & 0x03
                if(data == 0):
                    print "      ADJCNT (Phase Adjust Request):  0x" + '{:02X}'.format(byte0 & 0x03) + "\t\tPASS"
                else:
                    print "      ADJCNT (Phase Adjust Request):  0x" + '{:02X}'.format(byte0 & 0x03) + "\t\tFAIL"
                
                data = byte1 & 0x01
                if(data == 0):
                    print "      PHADJ (Phase Adjust Request) :  0x" + '{:02X}'.format(byte1 & 0x01) + "\t\tPASS"
                else:
                    print "      PHADJ (Phase Adjust Request) :  0x" + '{:02X}'.format(byte1 & 0x01) + "\t\tFAIL"
                
                data = byte2 & 0x01
                if(data == 0):
                    print "      ADJDIR (Adjust direction)    :  0x" + '{:02X}'.format(byte2 & 0x01) + "\t\tPASS"
                else:
                    print "      ADJDIR (Adjust direction)    :  0x" + '{:02X}'.format(byte2 & 0x01) + "\t\tFAIL"
                

def check_link_error_status(err_status1, err_status2): 
    print "\nCHECKING LINK ERRORS... \n"   
    error = 0;
    
    bit_position = 1;
    for lane in range(0, 8):
        print "Lane: ", lane,
        if(err_status1 & bit_position):
            print "\t- Not in Table Error received"
            error = 1;
        bit_position = bit_position << 1
        if(err_status1 & bit_position):
            print "\t- Disparity Error received"
            error = 1;
        bit_position = bit_position << 1
        if(err_status1 & bit_position):
            print "\t- Unexpected K-character received"
            error = 1;
        bit_position = bit_position << 1
        if(error == 0):
            print "\t- No Error received"
        error = 0
    
    bit_position = 1
    for lane in range(8, 12):
        print "Lane: ", lane,
        if(err_status2 & bit_position):
            print "\t- Not in Table Error received"
            error = 1;
        bit_position = bit_position << 1
        if(err_status2 & bit_position):
            print "\t- Disparity Error received"
            error = 1;
        bit_position = bit_position << 1
        if(err_status2 & bit_position):
            print "\t- Unexpected K-character received"
            error = 1;
        bit_position = bit_position << 1
        if(error == 0):
            print "\t- No Error received"
        error = 0
                            

def hexStr(data):
    return '0x' + '{:04X}'.format(data)

def next_pbrs(data):
    next_pbrs = ((data << 1) ^ (data << 2)) & 0b1111111111111100
    next_pbrs |= (((next_pbrs >> 15) ^ (next_pbrs >> 14)) & 0x0001)    # find bit 0
    next_pbrs |= (((next_pbrs >> 14) ^ (data << 1)) & 0x0002)    # find bit 1
    return next_pbrs

def dump_ADC_registers(device):
    device.hs_set_bit_mode(comm.HS_BIT_MODE_MPSSE)
    print "LTC2124 Register Dump: " 
    print "Register 1: 0x{:02X}".format(device.spi_receive_byte_at_address(0x81))
    print "Register 2: 0x{:02X}".format(device.spi_receive_byte_at_address(0x82))
    print "Register 3: 0x{:02X}".format(device.spi_receive_byte_at_address(0x83))
    print "Register 4: 0x{:02X}".format(device.spi_receive_byte_at_address(0x84))
    print "Register 5: 0x{:02X}".format(device.spi_receive_byte_at_address(0x85))
    print "Register 6: 0x{:02X}".format(device.spi_receive_byte_at_address(0x86))
    print "Register 7: 0x{:02X}".format(device.spi_receive_byte_at_address(0x87))
    print "Register 8: 0x{:02X}".format(device.spi_receive_byte_at_address(0x88))
    print "Register 9: 0x{:02X}".format(device.spi_receive_byte_at_address(0x89))
    print "Register A: 0x{:02X}".format(device.spi_receive_byte_at_address(0x8A))   

def load_ltc212x(device, cs_control=0, verbose=0, did=0xEF, bid=0x00, lanes=2, K=10, modes=0x00, subclass=1, pattern=0x00):
    if(verbose != 0):
        print "Configuring ADCs over SPI:"
    device.hs_set_bit_mode(comm.HS_BIT_MODE_MPSSE)
#ADC config, points CS line at appropriate device
    device.hs_fpga_write_data_at_address(SPI_CONFIG_REG, cs_control)
#    device.spi_send_byte_at_address(0x00, 0x01) # reset dut
    device.spi_send_byte_at_address(0x03, did) #Device ID to 0xAB
    device.spi_send_byte_at_address(0x04, bid) #Bank ID to 0x01
    device.spi_send_byte_at_address(0x05, lanes-1) #2 lane mode (default)
#    device.spi_send_byte_at_address(0x06, 0x1F) #9 frames / multiframe (0x08)
    device.spi_send_byte_at_address(0x06, K-1)
    device.spi_send_byte_at_address(0x07, modes) #Enable FAM, LAM
    #device.spi_send_byte_at_address(0x07, 0x18) #Disable FAM, LAM (only needed for prerelease silicon)
    device.spi_send_byte_at_address(0x08, subclass) #Subclass mode
    device.spi_send_byte_at_address(0x09, pattern) #PRBS test pattern
    device.spi_send_byte_at_address(0x0A, 0x03) # 0x03 = 16mA CML current
    if(verbose != 0):
        print "ADC " + str(cs_control) + " configuration:"
        dump_ADC_registers(device)

def capture2(device, n, dumpdata, dump_pscope_data, verbose):
    device.hs_set_bit_mode(comm.HS_BIT_MODE_MPSSE)
    dec = 0

    device.hs_fpga_write_data_at_address(CAPTURE_CONFIG_REG, n.MemSize | 0x08) # Both Channels active

    device.hs_fpga_write_data_at_address(CAPTURE_RESET_REG, 0x01)  #Reset
    device.hs_fpga_write_data_at_address(CAPTURE_CONTROL_REG, 0x01)  #Start!!
    sleep(1) #wait for capture

    data = device.hs_fpga_read_data_at_address(CAPTURE_STATUS_REG)
    syncErr = (data & 0x04) != 0
    if (verbose != 0):
        print "Reading capture status, should be 0x31 (CH0, CH1 valid, Capture done, data not fetched)"
        print "And it is... 0x{:04X}".format(data)

    #sleep(sleeptime)
    device.data_set_low_byte_first() #Set endian-ness
    device.hs_set_bit_mode(comm.HS_BIT_MODE_FIFO)
    sleep(0.1)
    nSampsRead, data = device.data_receive_uint16_values(end = (n.BuffSize + 100))
    device.hs_set_bit_mode(comm.HS_BIT_MODE_MPSSE)

    sleep(sleeptime)

    if(verbose != 0):
        print "Read out " + str(nSampsRead) + " samples"
#        print "And " + str(extrabytecount) + " extra bytes"

    # Initialize data arrays
    data_ch0 = [0]*(n.BuffSize/2)
    data_ch1 = [0]*(n.BuffSize/2)

    # Split CH0, CH1
    for i in range(0, (n.BuffSize)/4):
        # Split data for CH0, CH1
        data_ch0[i*2] = data[i*4]
        data_ch0[i*2+1] = data[i*4+1]
        data_ch1[i*2] = data[i*4+2]
        data_ch1[i*2+1] = data[i*4+3]

    if(dumpdata !=0):
        for i in range(0, min(dumpdata, n.BuffSize/2)):
            if(hex == 1 & dec == 1):
                print '0x' + '{:04X}'.format(data[2*i]) + ', ' + str(data[2*i]) + ', 0x' + '{:04X}'.format(data[2*i+1]) + ', ' + str(data[2*i+1])     # UN-comment for hex
                #print '0b' + '{:016b}'.format(data[i]) + ', ' + str(data[i])   # UN-comment for binary
            elif(hex == 1):
                print '0x' + '{:04X}'.format(data_ch0[i]) + ', 0x' + '{:04X}'.format(data_ch1[i])
            elif(dec == 1):
                print str(data[2*i]) + ", " + str(data[2*i+1])

    if(dump_pscope_data != 0):
        outfile = open("pscope_data.csv", "w")
        for i in range(0, n.BuffSize/2):
            outfile.write("{:d}, ,{:d}\n".format((data_ch0[i]-32768)/4, (data_ch1[i]-32768)/4))
        outfile.write("End\n")
        outfile.close()

    nSamps_per_channel = n.BuffSize/2
    return data, data_ch0, data_ch1, nSamps_per_channel, syncErr


def capture4(device, n, dumpdata, dump_pscope_data, verbose):
# Configuration Flow Step 11: Reset Capture Engine
#    device.SetMode(device.ModeMPSSE)
#    device.FPGAWriteAddress(CAPTURE_RESET_REG) 
#    device.FPGAWriteData(0x01)  #Reset
# Step 24
    clockstat = device.hs_fpga_read_data_at_address(CLOCK_STATUS_REG)
    if(verbose != 0):
        print "Reading Clock Status register; should be 0x16 (or at least 0x04 bit set)"
        print "Register 6   (Clock status): 0x{:04X}".format(clockstat)
# Step 25
    capturestat = device.hs_fpga_read_data_at_address(CAPTURE_STATUS_REG)
    syncErr = (capturestat & 0x04) != 0
    if (verbose != 0):
        print "Reading capture status, should be 0xF0 or 0xF4 (CH0, CH1, CH2, CH3 valid, Capture NOT done, data not fetched)"
        print "And it is... 0x{:04X}".format(capturestat)
# Step 26 in config flow
    device.hs_fpga_write_data_at_address(CAPTURE_CONFIG_REG, n.MemSize | 0x08) # CH0 and CH1
# Step 27
    device.hs_fpga_write_data_at_address(CAPTURE_CONTROL_REG, 0x00) #Set FETONLY low first
    device.hs_fpga_write_data_at_address(CAPTURE_CONTROL_REG, 0x01) #Start!! With FETONLY as 0
    sleep(1) #wait for capture
# Step 28
    capturestat = device.hs_fpga_read_data_at_address(CAPTURE_STATUS_REG)
    syncErr = (capturestat & 0x04) != 0
    if (verbose != 0):
        print "Reading capture status, should be 0xF1 (CH0, CH1, CH2, CH3 valid, Capture  IS done, data not fetched)"
        print "And it is... 0x{:04X}".format(capturestat)

#Set endian-ness
    device.data_set_low_byte_first()
    #device.data_set_high_byte_first()

# Step 29
    device.hs_set_bit_mode(comm.HS_BIT_MODE_FIFO)
    sleep(0.1)
# Step 30
    throwaway = 3
    #nSampsRead, data01 = device.data_receive_bytes(end = (n.BuffSize*2 + 100))
    nSampsRead, data01 = device.data_receive_uint16_values(end = (n.BuffSize))
    if(throwaway != 0):
        device.data_receive_bytes(end = throwaway)
# Step 31 
    device.hs_set_bit_mode(comm.HS_BIT_MODE_MPSSE)
    if(verbose != 0):
        print "Read out " + str(nSampsRead) + " samples for CH0, 1"

# Okay, now get CH2, CH3 data...

    device.hs_set_bit_mode(comm.HS_BIT_MODE_MPSSE)
    sleep(0.1)
# Step 32
    device.hs_fpga_write_data_at_address(CAPTURE_RESET_REG, 0x01)   #Reset
# Step 33
    device.hs_fpga_write_data_at_address(CAPTURE_CONFIG_REG, n.MemSize | 0x0A) # CH2 and CH3
# Step 34
    device.hs_fpga_write_data_at_address(CAPTURE_CONTROL_REG, 0x02)  # Set FETONLY high FIRST!!
    device.hs_fpga_write_data_at_address(CAPTURE_CONTROL_REG, 0x03)  #Start!! With FETONLY as 1
    sleep(1) #wait for capture
# Step 35
    capturestat = device.hs_fpga_read_data_at_address(CAPTURE_STATUS_REG)
    syncErr = (capturestat & 0x04) != 0
    if (verbose != 0):
        print "Reading capture status, should be 0xF1 (CH0, CH1, CH2, CH3 valid, Capture  IS done, data not fetched)"
        print "And it is... 0x{:04X}".format(capturestat)
# Step 36
    device.hs_set_bit_mode(comm.HS_BIT_MODE_FIFO)
    sleep(0.1)
# Step 37
    #nSampsRead, data23 = device.data_receive_bytes(end = (n.BuffSize*2 + 100))
    nSampsRead, data23 = device.data_receive_uint16_values(end = (n.BuffSize))
    if(throwaway != 0):
        device.data_receive_bytes(end = throwaway)
    device.hs_set_bit_mode(comm.HS_BIT_MODE_MPSSE)
    sleep(0.1)
    if(verbose != 0):
        print "Read out " + str(nSampsRead) + " samples for CH2, 3"

    # Initialize data arrays
    data_ch0 = [0]*(n.BuffSize/2)
    data_ch1 = [0]*(n.BuffSize/2)
    data_ch2 = [0]*(n.BuffSize/2)
    data_ch3 = [0]*(n.BuffSize/2)

    for i in range(0, (n.BuffSize)/4):
        # Split data for CH0, CH1
        data_ch0[i*2] = data01[i*4]
        data_ch0[i*2+1] = data01[i*4+1]
        data_ch1[i*2] = data01[i*4+2]
        data_ch1[i*2+1] = data01[i*4+3]
        # Split data for CH2, CH3
        data_ch2[i*2] = data23[i*4]
        data_ch2[i*2+1] = data23[i*4+1]
        data_ch3[i*2] = data23[i*4+2]
        data_ch3[i*2+1] = data23[i*4+3]

    if(dumpdata !=0):
        for i in range(0, min(dumpdata, n.BuffSize)):
                print '0x' + '{:04X}'.format(data_ch0[i]) + ', 0x' + '{:04X}'.format(data_ch1[i])+ ', 0x' + '{:04X}'.format(data_ch2[i])+ ', 0x' + '{:04X}'.format(data_ch3[i])

    nSamps_per_channel = nSampsRead/2
    return data_ch0, data_ch1, data_ch2, data_ch3, nSamps_per_channel, syncErr

def pattern_checker(data, nSamps_per_channel, dumppattern):
    printError = True
    errorcount = nSamps_per_channel - 1 #Start big
    #periodicity = lastperiodicity = 0
    golden = next_pbrs(data[0])
    for i in range(0, nSamps_per_channel-1):
        next = next_pbrs(data[i])
        if(i<dumppattern):
            print 'data: 0x' + '{:04X}'.format(data[i]) + ', next: 0x' +'{:04X}'.format(next) + ', XOR: 0x' +'{:04X}'.format(data[i+1] ^ next) + ', golden: 0x' +'{:04X}'.format(golden)      # UN-commet for hex
            #print '0b' + '{:016b}'.format(data[i]) + ',  0x' +'{:016b}'.format(next) + ',  0x' +'{:016b}'.format(data[i] ^ next)   # UN-comment for binary
        if(data[i+1] == next):
            errorcount -= 1
        elif printError:
            printError = False
            print
            print hexStr(data[i-1]) + "; " + hexStr(data[i]) + "; " + hexStr(data[i+1])
            print
#                print "error count = " + str(errorcount)
#                device.Close() #End of main loop.
#                raise Exception("BAD DATA!!!")
        if(data[i] == data[0]):
            #periodicity = i - lastperiodicity
            lastperiodicity = i
        golden = next_pbrs(golden)

    #print "periodicity (only valid for captures > 64k): " + str(periodicity)
    #if errorcount < 0:
    #    errorcount = 100000000
    return errorcount
    


  

# Capture a single channel on a single lane
# NEED TO TEST!!
def capture1(device, n, channels, lanes, dumpdata, dump_pscope_data, verbose):
    device.hs_set_bit_mode(comm.HS_BIT_MODE_MPSSE)
    dec = 0

    if(channels == 1):
        device.hs_fpga_write_data_at_address(CAPTURE_CONFIG_REG, n.MemSize | 0x00) # Channel A active
    elif(channels == 2):
        device.hs_fpga_write_data_at_address(CAPTURE_CONFIG_REG, n.MemSize | 0x02) # Channel B active

    device.hs_fpga_write_data_at_address(CAPTURE_RESET_REG, 0x01)  #Reset
    device.hs_fpga_write_data_at_address(CAPTURE_CONTROL_REG, 0x01)  #Start!!
    sleep(1) #wait for capture

    data = device.hs_fpga_read_data_at_address(CAPTURE_STATUS_REG)
    syncErr = (data & 0x04) != 0
    if (verbose != 0):
        print "Reading capture status, should be 0x31 (CH0, CH1 valid, Capture done, data not fetched)"
        print "And it is... 0x{:04X}".format(data)

    #sleep(sleeptime)
    device.data_set_low_byte_first() #Set endian-ness
    device.hs_set_bit_mode(comm.HS_BIT_MODE_FIFO)
    sleep(0.1)
    nSampsRead, data = device.data_receive_uint16_values(end = (n.BuffSize + 100))
    device.hs_set_bit_mode(comm.HS_BIT_MODE_MPSSE)

    sleep(sleeptime)

    if(verbose != 0):
        print "Read out " + str(nSampsRead) + " samples"
            
    # Split CH0, CH1
    data_ch0 = data[:]
    data_ch1 = data[:]

    if(lanes == 1): #EXPERIMENT!!!
        for i in range(0, (n.BuffSize)/4):
            data[i*4+0] = data_ch0[i*4+0]
            data[i*4+1] = data_ch0[i*4+2]
            data[i*4+2] = data_ch0[i*4+1]
            data[i*4+3] = data_ch0[i*4+3]

    if(channels != 3): #One channel only
    #if(1==1): # Force print single array
        if(dumpdata !=0):
            for i in range(0, min(dumpdata, n.BuffSize)):
                if(hex == 1 & dec == 1):
                    print '0x' + '{:04X}'.format(data[i]) + ', ' + str(data[i])     # UN-comment for hex
                    ##print '0x' + '{:016b}'.format(data[i]) + ', ' + str(data[i])   # UN-comment for binary
                elif(hex == 1):
                    print '0x' + '{:04X}'.format(data[i])
                elif(dec == 1):
                    print data[i]

    else: #Two channels

        if(dumpdata !=0):
            for i in range(0, min(dumpdata, n.BuffSize/2)):
                if(hex == 1 & dec == 1):
                    print '0x' + '{:04X}'.format(data[2*i]) + ', ' + str(data[2*i]) + ', 0x' + '{:04X}'.format(data[2*i+1]) + ', ' + str(data[2*i+1])     # UN-comment for hex
                    #print '0b' + '{:016b}'.format(data[i]) + ', ' + str(data[i])   # UN-comment for binary
                elif(hex == 1):
                    print '0x' + '{:04X}'.format(data_ch0[i]) + ', 0x' + '{:04X}'.format(data_ch1[i])
                elif(dec == 1):
                    print str(data[2*i]) + ", " + str(data[2*i+1])

    if(dump_pscope_data != 0):
        outfile = open("pscope_data.csv", "w")
        for i in range(0, n.BuffSize/2):
            outfile.write("{:d}, ,{:d}\n".format((data_ch0[i]-32768)/4, (data_ch1[i]-32768)/4))

        outfile.write("End\n")
        outfile.close()

    nSamps_per_channel = n.BuffSize
    return data, data_ch0, data_ch1, nSamps_per_channel, syncErr


def write_1ch_32k_pscope_file(data_vector, filename):
    f = open(filename, "w")
    f.write('Version,115\n')
    f.write('Retainers,0,1,32768,1024,6,300.000000000000000,0,1\n')
    f.write('Placement,44,0,1,-1,-1,-1,-1,419,16,1440,740\n')
    f.write('WindMgr,6,2,0\n')
    f.write('Page,0,2\n')
    f.write('Col,3,1\n')
    f.write('Row,2,1\n')
    f.write('Row,3,146\n')
    f.write('Row,1,319\n')
    f.write('Col,2,777\n')
    f.write('Row,4,1\n')
    f.write('Row,0,319\n')
    f.write('Page,1,2\n')
    f.write('Col,1,1\n')
    f.write('Row,1,1\n')
    f.write('Col,2,777\n')
    f.write('Row,4,1\n')
    f.write('Row,0,319\n')
    f.write('DemoID,DC1509,LTC2107,0\n')
    f.write('RawData,1,32768,16,4371,61253,300.000000000000000,0.000000e+000,6.553600e+004	\n')	
    for i in range(0, 32768):
        f.write(str(data_vector[i]))      # str() converts to string
        f.write('\n')


    f.write('End			\n')	
    f.close()

def bitfile_id_warning(id_shouldbe, id_is):
    if(id_is != id_shouldbe):
        print("***********************************")
        print("Warning!!! Bitfile ID should be 0x" + '{:02X}'.format(id_shouldbe))
        print("But is actually 0x"+ '{:02X}'.format(id_is))
        print("Make sure you know what you're doing...")
        print("***********************************\n")
    else:
        print("***********************************")
        print("Bitfile ID is 0x" + '{:02X}'.format(id_is))
        print("All good!!")
        print("***********************************\n")

