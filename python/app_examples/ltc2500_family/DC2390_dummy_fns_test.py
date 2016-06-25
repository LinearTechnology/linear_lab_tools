#!/usr/bin/python
# Example application for running tests on the Arrow SoCkit board
# using the LT_soc_framework

# This script tests all the dummy functions

import sys
sys.path.append('C:\Users\MSajikumar\Documents\LT_soc_framework')
from mem_func_client_2 import MemClient

# Get the host from the command line argument. Can be numeric or hostname.
#HOST = sys.argv.pop() if len(sys.argv) == 2 else '127.0.0.1'
HOST = sys.argv[1] if len(sys.argv) == 2 else '127.0.0.1'

print('Starting client\n')
client = MemClient(host=HOST)

verbose = True

# no need for any configuration
reg_address = 0x20
reg_value = 0xA6
if(verbose == True):
    print 'Writing 0x%X to dummy register 0x%X...' %(reg_address, reg_value)
client.reg_write(reg_address, reg_value, dummy = True)
if(verbose == True):
    print 'Reading back dummy register 0x%X...' % reg_address
reg_value_read = client.reg_read(reg_address, dummy = True)
if(verbose == True):
    print 'Value at dummy register 0x%X: ' % reg_address,
    print hex(reg_value_read)
if(reg_value == reg_value_read):
    print '** Tested Reg read and write. **\n'
    
mem_address = 0x40
mem_value = 0xB5
if(verbose == True):
    print 'Writing 0x%X to dummy memory location 0x%X...' % (mem_value, mem_address)
client.reg_write(mem_address, mem_value, dummy = True)
if(verbose == True):
    print 'Reading back dummy memory location 0x%X...'% mem_address
mem_value_read = client.mem_read(mem_address, dummy = True)
if(verbose == True):
    print 'Value at dummy memory location 0x%X : ' % mem_address,
    print hex(mem_value_read)
if(mem_value_read == mem_address):
    print '** Tested mem read and write. **\n'

starting_address = 900
number_of_writes = 100
reg_values = []
for i in range(0, 100):
    reg_values.append(i*5)
if(verbose == True):
    print 'Writing block of %d values to dummy register location %d...' % (number_of_writes, starting_address)
last_location = client.reg_write_block(starting_address, number_of_writes, reg_values, dummy = True)
if(verbose == True):
    print 'Last location written into: %d' % last_location
if(last_location == starting_address + ((number_of_writes-1) * 4)):
    print '** Tested reg_write_block. **\n'
    
starting_address = 900
number_of_reads = 100
values = client.reg_read_block(starting_address, number_of_reads, dummy = True)
if(verbose):
    print 'Reading out block of %d values from dummy register location %d... ' % (number_of_reads, starting_address)
    print values
print '** Tested reg_read_block. **\n'
