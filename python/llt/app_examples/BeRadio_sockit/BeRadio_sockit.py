#!/usr/bin/python
# Example application for running tests on the Arrow SoCkit board
# using the LT_soc_framework
import sys
from time import sleep # So we can make delays that humans can detect
# Okay, now the big one... this is the module that communicates with the SoCkit
from llt.common.mem_func_client_2 import MemClient
#from DC2390_functions import * # Register definitions live in this file
from llt.utils.sockit_system_functions import sockit_uns32_to_signed32, sockit_capture  # More functions for talking to the SoCkit
import numpy as np
from matplotlib import pyplot as plt

# Get the host from the command line argument. Can be numeric or hostname.
# If no host given, assume local machine (such as the SoCkit board itself)
HOST = sys.argv[1] if len(sys.argv) == 2 else '127.0.0.1'

# For example, if you're using the default fixed address that the SoCkit assigns
# itself if DHCP fails, you would run:
# python DC2390_hello_world.py "192.168.1.231"

# If you're running this script ON the sockit board itself, you would run:
# python DC2390_hello_world.py


# Now we create an instance of MemClient, called "client", pointing it at
# the SoCkit's IP address. This is the "pipeline" that allows us to communicate.
print('Starting client')
client = MemClient(host=HOST)

# First thing's First!! Unfortunately we can't even blink a light without first
# Configuring the clocks, which are provided from a crystal oscillator and
# LTC6954 clock distribution divider / driver

# The following routines read and write registers in the FPGA. These can be
# either read or write (or both), depending on the exact design.
# But fundamentally, when reading or writing a register from a script such as
# this one, you are reading or setting the state of a signal in the FPGA design.
# The addresses of the registers we will be talking to are defined in
# DC2390_functions.py, imported above. If you open it up, you will see these lines:
#
REV_ID_BASE = 0x10
LED_BASE = 0x40

VOLUME_BASE = 0x60
DATAPATH_CONTROL_BASE = 0xD0
TUNING_WORD_BASE = 0xF0

NUM_SAMPLES = 2**15

# Here, we use the reg_read() function to read the register that contains
# the FPGA bitfile's type and revision. This allows us to keep track of
# lots of projects, and software (such as this script) can verify that it's
# talking to the correct FPGA code. It's a 32-bit wide register, with the type
# in the lower 16-bits and the revision in the upper 16-bits.
# The reg_read takes the register address as the argument, and returns the
# value read out.

# In the FPGA design, this register is an input, with these values hard-coded.
# Other input registers are used to monitor other signals that may change,
# such as the status of an ADC capture.

rev_id = client.reg_read(REV_ID_BASE)   # The line that actually talks to the FPGA
type_id = rev_id & 0x0000FFFF           # Extract the lower 16-bits
rev = (rev_id >> 16) & 0x0000FFFF       # Extract the upper 16-bits.
print ('FPGA load type ID: %04X' % type_id)
print ('FPGA load revision: %04X' % rev)

# Next, we use the reg_write() function to blink a light! LED0 is connected to
# the least significant bit of register 0x40, and writing a "1" will turn the
# light on. reg_write takes the register address as the first argument, and the
# value to write as the second argument.
#tuning_word = 1 * 214748365 # 2 * 500kHz

player_0 = 1.136 #MHz
player_1 = 1.000 #MHz
player_2 = 0.893 #MHz

channel = player_2

fs = 10000000
f  = channel * 1000000

tuning_word = int((f/fs) * 2**32) #429496730 # 1MHz


client.reg_write(TUNING_WORD_BASE, tuning_word) # Tune radio
client.reg_write(VOLUME_BASE, 254) # Set volume

print ('Okay, now lets blink some lights!!')
for i in range (0, 2):
    client.reg_write(LED_BASE, 0x00000001) # The line that actually talks to the FPGA
    sleep(0.5)
    client.reg_write(LED_BASE, 0x00000000) # The line that actually talks to the FPGA
    sleep(0.5)


# Capture a sine wave
client.reg_write(DATAPATH_CONTROL_BASE, 0x00000000) # First capture ADC A
data = sockit_uns32_to_signed32(sockit_capture(client, NUM_SAMPLES, trigger = 0, timeout = 2.0))

data_ch0 = np.ndarray(NUM_SAMPLES, dtype=float)

numbits = 12
if(numbits == 18):
    for i in range(0, NUM_SAMPLES):
        data_ch0[i] = (data[i] & 0x0003FFFF)
        if(data_ch0[i] > 2**17):
            data_ch0[i] -= 2**18

if(numbits == 16):
    for i in range(0, NUM_SAMPLES):
        data_ch0[i] = (data[i] & 0x0000FFFF)
        if(data_ch0[i] > 2**15):
            data_ch0[i] -= 2**16

if(numbits == 12):
    for i in range(0, NUM_SAMPLES):
        data_ch0[i] = (data[i] & 0x00000FFF)
        if(data_ch0[i] > 2**11):
            data_ch0[i] -= 2**12

data_nodc0 = data_ch0 #- np.average(data)

#data_nodc *= np.blackman(NUM_SAMPLES)
#fftdata = np.abs(np.fft.fft(data_nodc)) / NUM_SAMPLES
#fftdb = 20*np.log10(fftdata / 2.0**31)
plt.figure(1)
plt.plot(data_ch0)

fftdata = 20*np.log10(np.abs(np.fft.fft(np.blackman(len(data_ch0)) * data_ch0)))
plt.figure(2)
plt.plot(fftdata)





# The next section shows how to properly shut down the SoCkit board. It's a
# Linux computer after all, with nonvolatile storage that should be unmounted
# cleanly. Just cutting the power will force a filesystem check (fsck) on the
# next boot. You can either set "choice = 'y'" below, or type
# "client.shutdown()" in the Python console

# What client.shutdown() really does is execute the command:
# "shutdown -h now"
# on the SoCkit board.


choice = 'n'
#choice = raw_input('Shutdown: y/n? ')
if(choice == 'y'):
    print 'Shutting down ...'
#    time.sleep(30)
    client.shutdown()


