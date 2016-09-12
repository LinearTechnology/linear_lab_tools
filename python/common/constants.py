# -*- coding: utf-8 -*-
"""
    Created by: Noe Quintero
    E-mail: nquintero@linear.com

    REVISION HISTORY
    $Revision: 2583 $
    $Date: 2014-06-27 17:21:46 -0700 (Fri, 27 Jun 2014) $
    
    Copyright (c) 2015, Linear Technology Corp.(LTC)
    All rights reserved.

    Redistribution and use in source and binary forms, with or without
    modification, are permitted provided that the following conditions are met:

    1. Redistributions of source code must retain the above copyright notice, 
       this list of conditions and the following disclaimer.
    2. Redistributions in binary form must reproduce the above copyright 
       notice, this list of conditions and the following disclaimer in the 
       documentation and/or other materials provided with the distribution.

    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
    AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE 
    IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE 
    ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE 
    LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
    CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF 
    SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS 
    INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN 
    CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
    ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE 
    POSSIBILITY OF SUCH DAMAGE.

    The views and conclusions contained in the software and documentation are 
    those of the authors and should not be interpreted as representing official
    policies, either expressed or implied, of Linear Technology Corp.

    Description:
        The purpose of this module is to contain all constants for linear
        lab tools
"""

ERROR_BUFFER_SIZE = 256
SERIAL_NUMBER_BUFFER_SIZE = 16
DESCRIPTION_BUFFER_SIZE = 64

TYPE_NONE = 0x00000000
TYPE_DC1371 = 0x00000001
TYPE_DC718 = 0x00000002
TYPE_DC890 = 0x00000004
TYPE_HIGH_SPEED = 0x00000008
TYPE_UNKNOWN = 0xFFFFFFFF

SPI_CS_STATE_LOW = 0
SPI_CS_STATE_HIGH = 1

TRIGGER_NONE = 0
TRIGGER_START_POSITIVE_EDGE = 1
TRIGGER_DC890_START_NEGATIVE_EDGE = 2
TRIGGER_DC1371_STOP_NEGATIVE_EDGE = 3

DC1371_CHIP_SELECT_ONE = 1
DC1371_CHIP_SELECT_TWO = 2

# mode argument to set_mode. For data (FIFO) communication use BIT_MODE_FIFO, for
# everything else use BIT_MODE_MPSSE
HS_BIT_MODE_MPSSE = 0x02
HS_BIT_MODE_FIFO = 0x40

# Controller EEPROM size
DC890_EEPROM_SIZE = 50
DC718_EEPROM_SIZE = 50
DC1371_EEPROM_SIZE = 400