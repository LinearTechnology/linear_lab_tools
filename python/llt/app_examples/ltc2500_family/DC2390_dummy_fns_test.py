#!/usr/bin/python
# Example application for running tests on the Arrow SoCkit board
# using the LT_soc_framework

# This script tests all the dummy functions

import sys

from llt.common.mem_func_client_2 import MemClient

# Get the host from the command line argument. Can be numeric or hostname.
#HOST = sys.argv.pop() if len(sys.argv) == 2 else '127.0.0.1'
HOST = sys.argv[1] if len(sys.argv) == 2 else '127.0.0.1'

print('Starting client\n')
client = MemClient(host=HOST)

# no need for any configuration
verbose = True
dummy = True
error = 0

reg_address = 0x60
reg_value = 0xB7
mem_address = 0x88
mem_value = 0xB5
number_of_writes = 3
number_of_reads = 50
starting_address = reg_address

reg_values = []
mem_values = []
for i in range(0, number_of_writes):
    reg_values.append(i*2)
    mem_values.append(i*2)

i2c_output_base_reg = 0x120
i2c_input_base_reg = 0x140

# Testing reg_write
if(verbose == True):    print 'Writing 0x%X to register 0x%X...' %(reg_value, reg_address)
written_address = client.reg_write(reg_address, reg_value, dummy)
if (written_address != reg_address):    
    print 'ERROR in Register Write. Returned wrong address.'
    error = error + 1
    
# Testing reg_read
if(verbose == True):    print 'Reading back register 0x%X...' % reg_address
reg_value_read = client.reg_read(reg_address, dummy)
if(verbose == True):    print 'Value at register 0x%X: 0x%X' % (reg_address, reg_value_read)
if(reg_value_read != reg_value):    
    print 'ERROR in Register Read. Returned wrong value.'
    error = error + 1
    
print '** Tested Reg read and write. **\n'

# Testing mem write
if(verbose == True):    print 'Writing 0x%X to memory location 0x%X...' % (mem_value, mem_address)
written_address = client.mem_write(mem_address, mem_value, dummy)
if (written_address != mem_address):    
    print 'ERROR in Memory Write. Returned wrong address.'
    error = error + 1

# Testing mem read
if(verbose == True):    print 'Reading back memory location 0x%X...'% mem_address
mem_value_read = client.mem_read(mem_address, dummy)
if(verbose == True):    print 'Value at memory location 0x%X : 0x%X' % (mem_address, mem_value_read)
if(mem_value_read != mem_value):
    print 'ERROR in Memroy Read. Returned wrong value.'
    error = error + 1
    
print '** Tested Mem read and write. **\n'

# Testing reg write block
if(verbose == True):    print 'Writing block of %d values to register location 0x%X...' % (number_of_writes, starting_address)
last_location = client.reg_write_block(starting_address, number_of_writes, reg_values, dummy)
if(verbose == True):    print 'Last location written into: 0x%X' % last_location
if(last_location != (starting_address + (number_of_writes-1)*4)):
    print 'ERROR in Reg Write Block. Returned wrong last location'
    error = error + 1
print '** Tested reg_write_block. **\n'
    
# Testing reg read block
values = client.reg_read_block(starting_address, number_of_reads, dummy)
if(verbose):
    print 'Reading out block of %d values from register location 0x%X... ' % (number_of_reads, starting_address)
    print 'Values read out:'
    print values
print '** Tested reg_read_block. **\n'

# Testing mem_write_block
if(verbose == True):    print 'Writing block of %d values to memory location 0x%X...' % (number_of_writes, starting_address)
last_location = client.mem_write_block(starting_address, number_of_writes, mem_values, dummy)
if(verbose == True):    print 'Last location written into: 0x%X' % last_location
if(last_location != (starting_address + (number_of_writes-1)*4)):
    print 'ERROR in Mem Write Block. Returned wrong last location'
    error = error + 1
print '** Tested mem_write_block. **\n'

# Testing mem_read_block
values = client.mem_read_block(starting_address, number_of_reads, dummy)
if(verbose):
    print 'Reading out block of %d values from memory location 0x%X... ' % (number_of_reads, starting_address)
    print 'Values read out:'
    print values
print '** Tested mem_read_block. **\n'

# Testing mem_read_to_file
if(verbose):    print 'Reading block of memory and writing into file...'
client.mem_read_to_file(starting_address, number_of_reads, 'hello.txt', dummy)
print '** Tested mem_read_to_file. **\n'

# Testing mem_write_from_file
if(verbose):    print 'Reading a file and writing into memory...'
client.mem_write_from_file(starting_address + 100, number_of_reads, 'hello.txt', dummy)
values = client.mem_read_block(starting_address + 100, number_of_reads, dummy)
if(verbose):
    print 'Values read out:'
    print values
print '** Tested mem_write_from_file**\n'

# Testing file transfer
file_to_read = "C:/Users/MSajikumar/Documents/DC2390_ABCD_123F.rbf"
file_write_path = "/home/sockit/fpga_bitfiles/test.rbf"
if(verbose):
    print 'Transferring a file to deamon...'
    print 'File to read: %s' % file_to_read
    print 'File write path: %s' % file_write_path
client.file_transfer(file_to_read, file_write_path)
print '**Tested File transfer**\n'

# Testing DC590 commands - Non-dummy functions
print 'TESTING DC590 COMMANDS'
print 'Enter 0 to stop.'
command = ""
while(command != "0"):
    command = raw_input("\nEnter a string: ")   
    if(command != "0"):
        rawstring = client.send_dc590(i2c_output_base_reg, i2c_input_base_reg, command)
        print("Raw data, no interpretation: %s") % rawstring
    
# Testing Read EEPROM    
print '\nReading EEPROM...'
eeprom_id = client.read_eeprom_id(i2c_output_base_reg, i2c_input_base_reg)
if(verbose):    print 'EEPROM ID string: %s' % eeprom_id
print 'IC identified: %s' %(eeprom_id.split(','))[0]

print '**Tested DC590 commands**\n'




############client.send_json("cd fpga_bitfiles")

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
choice = raw_input('\nShutdown: y/n? ')
if(choice == 'y'):
    shut = client.shutdown(dummy = False)
    print('Shutting down...' if shut == True else 'Shutdown Failed!')
    