#!/usr/bin/env python
# Import libraries

import sys
sys.path.append("../modules/spi_avalon_bridge")
from ltc_spi_avalon import *

from random import randint
from Altera_JESD204B_RX_Regmap import *

import msvcrt 

dump_jesd204b_registers = 1
led_scan = 1




# ************************************************
# Globals
# ************************************************

# Base addresses 
LED_BASE = 0x0000
JESD204B_BASE = 0x0400
DIPSW_BASE = 0x0800

# Constants 


# ************************************************
# Function Definitions
# ************************************************
def serialloopbacken(enable):
    if(enable == 1):
        transaction_write(dc590, LED_BASE, 4, [0xFF, 0x00, 0x00, 0x00]) #Disable serial loopback...
    else:
        transaction_write(dc590, LED_BASE, 4, [0xFE, 0x00, 0x00, 0x00]) #Disable serial loopback...
# ************************************************
# Begining of Program
# ************************************************

try:
    dc590 = DC590() ## Look for the DC590

    print "Configuring ADC via SPI\n"
    #string = dc590.transfer_packets('G M0 xS00S80X', 0) #reset!
    #                                      
    string = dc590.transfer_packets('G M0 xS03SABX xS04S0CX xS06S1FX xS07S01X xS08S11X xS0AS03X', 0)
    #Dump ALL registers
    string = dc590.transfer_packets('G M0 ZxS81RXZ xS82RXZ xS83RXZ xS84RXZ xS85RXZ xS86RXZ xS87RXZ xS88RXZ xS89RXZ xS8ARXZ', 6)
    print "got back (starting w/ reg 1) :" + string
    dc590.transfer_packets('M1', 0)
    dc590.transfer_packets('g', 0) # Set the GPIO LOW to talk to SPI-Avalon bridge

    if(led_scan == 1):
        print "Sending data to LED's\n"
        # Send / read data from PIO thats located on the memory bus
        for y in range(0, 5):
            for x in range(0,7):   
                data = [(0x01<<x)^0xFF, 0x00, 0x00, 0x00]
    #            print "data sent: " + hex(data[0])
                # Send data to PIO
                transaction_write(dc590, LED_BASE, 4, data)
                # Read data from PIO
    #            data_packet = transaction_read(dc590, LED_BASE, 1)
    #            print "data read: " + hex(data_packet[0])
            for x in range(0,7):    
                data = [(0x01<<(7-x))^0xFF, 0x00, 0x00, 0x00]
    #            print "data sent: " + hex(data[0])
                # Send data to PIO
                transaction_write(dc590, LED_BASE, 4, data)
                # Read data from PIO
    #            data_packet = transaction_read(dc590, LED_BASE, 1)
    #            print "data read: " + hex(data_packet[0])
    
            #transaction_write(dc590, LED_BASE, 1, [0xFF])
    #transaction_write(dc590, LED_BASE, 1, [0xFF]) #ENABLE serial loopback...
    #transaction_write(dc590, LED_BASE, 1, [0xFE]) #Disable serial loopback...
    serialloopbacken(1)
    #IMPORTANT REMINDER!! Bytes order is reversed!!!
    transaction_write(dc590, (JESD204B_BASE + 0x50), 4, [0x04, 0x00, 0x00, 0x00]) #disable lane sync
    transaction_write(dc590, (JESD204B_BASE + 0x54), 4, [0x02, 0x08, 0x10, 0x00]) # ENABLE rbd_offset
#    transaction_write(dc590, (JESD204B_BASE + 0x54), 4, [0x00, 0x08, 0x00, 0x00]) # override rbd_offset
    transaction_write(dc590, (JESD204B_BASE + 0x78), 4, [0xFF, 0xFF, 0xFF, 0xFF]) # Enable resync on any errors!

#    data_packet = transaction_read(dc590, DIPSW_BASE, 4)
#    print "DIP Switch status: " + hex(data_packet[3])+ hex(data_packet[2])+ hex(data_packet[1])+ hex(data_packet[0])

#    for x in range(0,63):
#        data = [(0x01<<x)^0xFF]
#master_write_32 $master_path [expr $base_address + 0x50] 0x00000001
    if (dump_jesd204b_registers == 1):
        transaction_write(dc590, (JESD204B_BASE + 0x50), 4, [0x00, 0x00, 0x00, 0x00])
        ilas_octet_0 = transaction_read(dc590, JESD204B_BASE + 0xA0, 4)
        ilas_octet_1 = transaction_read(dc590, JESD204B_BASE + 0xA4, 4)
        ilas_octet_2 = transaction_read(dc590, JESD204B_BASE + 0xA8, 4)
        ilas_octet_3 = transaction_read(dc590, JESD204B_BASE + 0xAC, 4)
        print "Lane 0..."
        print "ILAS Octet 0: " + ' '.join(['0x%02x' % b for b in reversed(ilas_octet_0)]) 
        print "ILAS Octet 1: " + ' '.join(['0x%02x' % b for b in reversed(ilas_octet_1)]) 
        print "ILAS Octet 2: " + ' '.join(['0x%02x' % b for b in reversed(ilas_octet_2)]) 
        print "ILAS Octet 3: " + ' '.join(['0x%02x' % b for b in reversed(ilas_octet_3)]) 

        transaction_write(dc590, (JESD204B_BASE + 0x50), 4, [0x80, 0x00, 0x00, 0x00])
        ilas_octet_0 = transaction_read(dc590, JESD204B_BASE + 0xA0, 4)
        ilas_octet_1 = transaction_read(dc590, JESD204B_BASE + 0xA4, 4)
        ilas_octet_2 = transaction_read(dc590, JESD204B_BASE + 0xA8, 4)
        ilas_octet_3 = transaction_read(dc590, JESD204B_BASE + 0xAC, 4)
        print "Lane 1..."
        print "ILAS Octet 0: " + ' '.join(['0x%02x' % b for b in reversed(ilas_octet_0)]) 
        print "ILAS Octet 1: " + ' '.join(['0x%02x' % b for b in reversed(ilas_octet_1)]) 
        print "ILAS Octet 2: " + ' '.join(['0x%02x' % b for b in reversed(ilas_octet_2)]) 
        print "ILAS Octet 3: " + ' '.join(['0x%02x' % b for b in reversed(ilas_octet_3)])
        
        print "okay, now FULL DUMP from 0x04"
        for i in range(0,32):
            reg_data = transaction_read(dc590, JESD204B_BASE + JESD204B_RX_Regmap[i], 4)
            print "Reg " + '0x%02x ' % JESD204B_RX_Regmap[i] + JESD204B_RX_String[i] + " : " + ' '.join(['0x%02x' % b for b in reversed(reg_data)]) 




        #print "ILAS Octet 0: 0x{:08X}".format(ilas_octet_0_word)
        
#        print "ILAS Octet 0: " + hex(ilas_octet_0[3])+ hex(ilas_octet_0[2])+ hex(ilas_octet_0[1])+ hex(ilas_octet_0[0])
#        print "ILAS Octet 1: " + hex(ilas_octet_1[3])+ hex(ilas_octet_1[2])+ hex(ilas_octet_1[1])+ hex(ilas_octet_1[0])
#        print "ILAS Octet 2: " + hex(ilas_octet_2[3])+ hex(ilas_octet_2[2])+ hex(ilas_octet_2[1])+ hex(ilas_octet_2[0])
#        print "ILAS Octet 3: " + hex(ilas_octet_3[3])+ hex(ilas_octet_3[2])+ hex(ilas_octet_3[1])+ hex(ilas_octet_3[0])
                         #     "M0 G xS00S80X xS03SABX xS04S0CX xS08S01X Z xS83T00XZ xS84T00XZ xS06S1FX xS86T00XZ"

finally:
    dc590.close()
print 'Done!'

