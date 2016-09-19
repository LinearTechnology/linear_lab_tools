#!/usr/bin/python
# Example application for running tests on the Arrow SoCkit board
# using the LT_soc_framework

# This script tests all the dummy functions

import sys
sys.path.append("../../")
sys.path.append("../../utils/")
from mem_func_client_2 import MemClient

# Get the host from the command line argument. Can be numeric or hostname.
#HOST = sys.argv.pop() if len(sys.argv) == 2 else '127.0.0.1'
HOST = sys.argv[1] if len(sys.argv) == 2 else '127.0.0.1'

print('Starting client\n')
client = MemClient(host=HOST)

verbose = True

# no need for any configuration

# Testing reg_read and reg_write
reg_address = 0x60
reg_value = 0xB6
if(verbose == True):
    print 'Writing 0x%X to dummy register 0x%X...' %(reg_value, reg_address)
client.reg_write(reg_address, reg_value, dummy = False)
if(verbose == True):
    print 'Reading back dummy register 0x%X...' % reg_address
reg_value_read = client.reg_read(reg_address, dummy = False)
if(verbose == True):
    print 'Value at dummy register 0x%X: ' % reg_address,
    print hex(reg_value_read)
if(reg_value == reg_value_read):
    print '** Tested Reg read and write. **\n'
    
# Testing mem read and mem write
mem_address = 0x56
mem_value = 0xB5
if(verbose == True):
    print 'Writing 0x%X to dummy memory location 0x%X...' % (mem_value, mem_address)
client.mem_write(mem_address, mem_value, dummy = False)
if(verbose == True):
    print 'Reading back dummy memory location 0x%X...'% mem_address
mem_value_read = client.mem_read(mem_address, dummy = False)
if(verbose == True):
    print 'Value at dummy memory location 0x%X : ' % mem_address,
    print hex(mem_value_read)
if(mem_value_read == mem_address):
    print '** Tested mem read and write. **\n'
else:
    print '** Check mem read and write ** \n'
    
    
# Testing reg write block
starting_address = 0x60
number_of_writes = 3
reg_values = []
for i in range(1, number_of_writes+1):
    reg_values.append(i*2)
if(verbose == True):
    print 'Writing block of %d values to dummy register location %d...' % (number_of_writes, starting_address)
last_location = client.reg_write_block(starting_address, number_of_writes, reg_values, dummy = False)
if(verbose == True):
    print 'Last location written into: %d' % last_location
if(last_location == starting_address + ((number_of_writes-1) * 4)):
    print '** Tested reg_write_block. **\n'
    
# Testing reg read block
starting_address = 0x60
number_of_reads = 3
values = client.reg_read_block(starting_address, number_of_reads, dummy = False)
if(verbose):
    print 'Reading out block of %d values from dummy register location %d... ' % (number_of_reads, starting_address)
    print values
print '** Tested reg_read_block. **\n'

# Testing mem_write_block
starting_address = 800
number_of_writes = 25
mem_values = []
for i in range(0, number_of_writes):
    mem_values.append(i*2)
if(verbose == True):
    print 'Writing block of %d values to dummy memory location %d...' % (number_of_writes, starting_address)
last_location = client.mem_write_block(starting_address, number_of_writes, mem_values, dummy = False)
if(verbose == True):
    print 'Last location written into: %d' % last_location
if(last_location == starting_address + ((number_of_writes-1) * 4)):
    print '** Tested mem_write_block. **\n'
    
#Testing mem_read_block
starting_address = 800
number_of_reads = 50
values = client.mem_read_block(starting_address, number_of_reads, dummy = False)
if(verbose):
    print 'Reading out block of %d values from dummy memory location %d... ' % (number_of_reads, starting_address)
    print values
print '** Tested mem_read_block. **\n'

client.mem_read_to_file(starting_address, number_of_reads, 'hello.txt', dummy = True)
client.mem_write_from_file(starting_address + 100, number_of_reads, 'hello.txt', dummy = True)
values = client.mem_read_block(starting_address + 100, number_of_reads, dummy = False)
print values

#testing file transfer
file_to_read = "C:\Users\MSajikumar\Documents\linear_technology\linear_lab_tools_svn\python\DC2390_ABCD_123E.rbf"
file_write_path = "/home/sockit/fpga_bitfiles/test.rbf"
path_size = 64
client.file_transfer(file_to_read, file_write_path)


client.send_json("cd fpga_bitfiles")

#### I2C stuff - to be tested again. #####

#print 'Detecting I2C devices. Number of device: ',
#print client.i2c_identify()

#print 'I2C Testing... ',
#print client.i2c_testing()
#
#slave_address = 0x73  # Globoal 7-bit address: 111 0011
#part_command = 0x2F      # 0010 (write and update all) 1111 (all DACs)
#num_of_bytes = 2
#vals = [0x00, 0x00]
#print 'I2C write byte... ',
#print client.i2c_write_byte(slave_address, part_command, num_of_bytes, vals, dummy = True)
#
#print 'I2C read EEPROM... ',
#print client.i2c_read()
#
#choice = raw_input('Shutdown: y/n? ')
#if(choice == 'y'):
#    shut = client.shutdown(dummy = True)
#    print('Shutting down...' if shut == True else 'Shutdown Failed!')
    