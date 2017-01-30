#!/usr/bin/python
# Client for daemon script to inteface with the FPGA peripherals and /dev/mem

import os
from subprocess import call
import socket
import ctypes
import struct
import json
from time import sleep

basedir = os.path.abspath(os.path.dirname(__file__))



# mem_func_lib = ctypes.CDLL(os.path.join(basedir, 'mem_functions'))

def recvall(sock, length):
    data = ''
    while len(data) < length:
        more = sock.recv(length - len(data))
        if not more:
            raise EOFError('socket closed %d bytes into a %d-byte message'
                           % (len(data), length))
        data += more
    return data

def check_address_range(address):
    if (address % 4 != 0):
        print('Address needs to be word aligned.')
        return 0
    
    # FIX THIS
    if (address > 0x10000000):
        print('Address out of range. Must be less than 0x100000')
        return 0

         
class MemClient(object):
    """Class for the socket server"""

    #cmd_id
    REG_READ = 1
    REG_WRITE = 2
    MEM_READ = 3
    MEM_WRITE = 4
    REG_READ_BLOCK = 5 # to be handled
    REG_WRITE_BLOCK = 6
    MEM_READ_BLOCK = 7
    MEM_WRITE_BLOCK = 8 # to be handled
    MEM_READ_TO_FILE = 9
    MEM_WRITE_FROM_FILE = 10
    REG_WRITE_LUT = 11
    
    DC590_TPP_COMMANDS = 90
    
    I2C_IDENTIFY = 12
    I2C_WRITE_BYTE = 17
    I2C_TESTING = 18
    I2C_READ_EEPROM = 19
    
    FILE_TRANSFER = 80
    
    SHUTDOWN = 1024

    ERROR = 0x80000000
    COMMAND_SENT = 0x40000000
    RESPONSE_RECEIVED = 0x20000000
    DUMMY_FUNC = 0x10000000
    
    def __init__(self, host='localhost', port=1992):
        self.port = port
        self.host = host
    
    # Func Desc: Read a register
    def reg_read(self, address, dummy = False):
        check_address_range(address)
        length = 12 # 4 bytes CMD + 4 bytes LN + 4 bytes Register Location
        command = MemClient.REG_READ | MemClient.COMMAND_SENT
        if (dummy == True):
            command = command | MemClient.DUMMY_FUNC
            
        sock_msg = struct.pack('III', command, length, address)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.host, self.port))
        s.sendall(sock_msg)
        
        # register value is 32 bits
        response = recvall(s, 12)
        (response_command, response_length, register_value) = struct.unpack('III', response)
        #check for error
        s.close()
        return register_value
      
    # Func Desc: Write into a register
    def reg_write(self, address, value, dummy = False):
        check_address_range(address)
        length = 16
        command = MemClient.REG_WRITE | MemClient.COMMAND_SENT
        if (dummy == True):
            command = command | MemClient.DUMMY_FUNC
        # register_location = MemClient.handle_command(self, command, length, (address, value))        
        
        sock_msg = struct.pack('IIII', command, length, address, value)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.host, self.port))
        s.sendall(sock_msg)
        
        # third parameter is the register location that was written into    
        response = recvall(s, 12)
        (response_command, response_length, register_location) = struct.unpack('III', response)
        s.close()

        return register_location

    # Func Desc: Read a memory location
    def mem_read(self, address, dummy = False):
        check_address_range(address)
        length = 12
        command = MemClient.MEM_READ | MemClient.COMMAND_SENT
        if (dummy == True):
            command = command | MemClient.DUMMY_FUNC
        sock_msg = struct.pack('III', command, length, address)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.host, self.port))
        s.sendall(sock_msg)
        response = recvall(s, 12)
        (response_command, response_length, memory_value) = struct.unpack('III', response)
        s.close()

        return memory_value
    
    # Func Desc: Write into memory location    
    def mem_write(self, address, value, dummy = False):
        check_address_range(address)
        length = 16
        command = MemClient.MEM_WRITE | MemClient.COMMAND_SENT
        if (dummy == True):
            command = command | MemClient.DUMMY_FUNC
        sock_msg = struct.pack('IIII', command, length, address, value)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.host, self.port))
        s.sendall(sock_msg)
        response = recvall(s, 12)
        # third parameter is the register location that was written into
        (response_command, response_length, memory_location) = struct.unpack('III', response)
        s.close()
        
        return memory_location
    
    # Func Desc: Read a block of registers
    def reg_read_block(self, address, size, dummy = False):
        check_address_range(address)
        length = 16
        command = MemClient.REG_READ_BLOCK | MemClient.COMMAND_SENT
        if (dummy == True):
            command = command | MemClient.DUMMY_FUNC
        sock_msg = struct.pack('IIII', command, length, address, size)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.host, self.port))
        s.sendall(sock_msg)
        
        block = recvall(s, size * 4)
        ret=[]
        for i in range(0, size*4, 4):
            ret.append(struct.unpack('I', block[i:i+4])[0])
        s.close()
        return ret
        
    # Func Desc: Read a block of memory locations    
    def mem_read_block(self, address, capture_size, dummy = False):
        check_address_range(address)
        length = 16
        command = MemClient.MEM_READ_BLOCK | MemClient.COMMAND_SENT
        if (dummy == True):
            command = command | MemClient.DUMMY_FUNC
        sock_msg = struct.pack('IIII', command, length, address, capture_size)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.host, self.port))
        s.sendall(sock_msg)
        ret = 0
        block = recvall(s, capture_size * 4)
        ret=[]
        for i in range(0, capture_size*4, 4):
            ret.append(struct.unpack('I', block[i:i+4])[0])
        s.close()
        return ret        
            
    # Func Desc: Write into a block of register locations
    def reg_write_block(self, address, size, reg_values, dummy = False):
        check_address_range(address)
        length = 16 + size * 4
        command = MemClient.REG_WRITE_BLOCK | MemClient.COMMAND_SENT
        if (dummy == True):
            command = command | MemClient.DUMMY_FUNC
        sock_msg = struct.pack('IIII', command, length, address, size)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.host, self.port))
        s.sendall(sock_msg)
        # transmit each value as a string (32 bits)        
        val = struct.pack('I'*size, *reg_values)
        s.sendall(val)

        response = recvall(s, 12)
        # third parameter is the register location that was last written into
        (response_command, response_length, last_location) = struct.unpack('III', response)
        if(last_location != (address + (size - 1)*4)):
            print 'Not all locations written!'
        s.close()
        return last_location
    
    # Func Desc: Write into a block of memory locations
    def mem_write_block(self, address, size, mem_values, dummy = False):
        check_address_range(address)
        length = 16 + size * 4
        command = MemClient.MEM_WRITE_BLOCK | MemClient.COMMAND_SENT
        if (dummy == True):
            command = command | MemClient.DUMMY_FUNC
        sock_msg = struct.pack('IIII', command, length, address, size)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.host, self.port))
        s.sendall(sock_msg)
        # transmit each value as a string (32 bits)
        val = struct.pack('I'*size, *mem_values)
        s.sendall(val)

        response = recvall(s, 12)
        # third parameter is the register location that was last written into
        (response_command, response_length, last_location) = struct.unpack('III', response)
        if(last_location != (address + (size - 1)*4)):
            print 'Not all locations written!'
        s.close()
        return last_location
        
        
        
        
        
    # read a block of memory and write into a file
    def mem_read_to_file(self, address, capture_size, filename, dummy = False):
        check_address_range(address)
        length = 16 + len(filename)
        command = MemClient.MEM_READ_TO_FILE | MemClient.COMMAND_SENT
        if (dummy == True):
            command = command | MemClient.DUMMY_FUNC
        sock_msg = struct.pack('IIII', command, length, address, capture_size)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.host, self.port))
        s.sendall(sock_msg)
        s.sendall(filename)
        
        response = recvall(s, 12)
        (response_command, response_length, val) = struct.unpack('III', response)
        s.close()
        
      
    def mem_write_from_file(self, address, capture_size, filename, dummy = False):
        check_address_range(address)
        length = 16 + len(filename)
        command = MemClient.MEM_WRITE_FROM_FILE | MemClient.COMMAND_SENT
        if (dummy == True):
            command = command | MemClient.DUMMY_FUNC
        sock_msg = struct.pack('IIII', command, length, address, capture_size)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.host, self.port))
        s.sendall(sock_msg)
        s.sendall(filename)
        
        response = recvall(s, 12)
        (response_command, response_length, val) = struct.unpack('III', response)
        s.close()

        
    def reg_write_LUT(self, address, size, data_array, dummy = False):
        check_address_range(address)
        length = 16 + size * 4
        command = MemClient.REG_WRITE_LUT | MemClient.COMMAND_SENT
        if (dummy == True):
            command = command | MemClient.DUMMY_FUNC
        print command
        sock_msg = struct.pack('IIII', command, length, address, size)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.host, self.port))
        s.sendall(sock_msg)

        s.sendall(data_array)
        response = recvall(s, 12)
        # third parameter is the register location that was last written into
        #last_location = struct.unpack('III', response)[2]
        (response_command, response_length, last_location) = struct.unpack('III', response)
        s.close()

        return last_location            

    

     
    def i2c_identify(self, dummy = False):
        length = 12
        command = MemClient.I2C_IDENTIFY | MemClient.COMMAND_SENT
        val = 0xFF
        if (dummy == True):
            command = command | MemClient.DUMMY_FUNC
        sock_msg = struct.pack('III', command, length, val)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.host, self.port))
        s.sendall(sock_msg)
        response = recvall(s, 12)
        
        # third parameter is the register location that was written into
        (response_command, response_length, count) = struct.unpack('III', response)
        s.close()
        return count
        
    def i2c_write_byte(self, slave_address, part_command, num_of_bytes, val, dummy = False):       
        length = 20 + num_of_bytes * 4
        command = MemClient.I2C_WRITE_BYTE | MemClient.COMMAND_SENT
        if (dummy == True):
            command = command | MemClient.DUMMY_FUNC
        sock_msg = struct.pack('IIIII', command, length, slave_address, part_command, num_of_bytes)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.host, self.port))
        s.sendall(sock_msg)

        # transmit each value as a string (32 bits)
        for i in range(0, num_of_bytes):
            value = struct.pack('I', val[i])            
            s.sendall(value)

        response = recvall(s, 12)
        # third parameter is the register location that was last written into
        (response_command, response_length, response_val) = struct.unpack('III', response)
        s.close()
        return response_val
        
    def i2c_testing(self, dummy = False):
        print 'In I2C testing...'
        command = MemClient.I2C_TESTING | MemClient.COMMAND_SENT
        length = 12
        if (dummy == True):
            command = command | MemClient.DUMMY_FUNC
        val = 0xFF
        sock_msg = struct.pack('III', command, length, val)
        s = socket.socket(socket.AF_INET, socket.SOCK_STR/EAM)
        s.connect((self.host, self.port))
        s.sendall(sock_msg)
        response = recvall(s, 12)
        s.close()
        (response_command, response_length, val) = struct.unpack('III', response)
        if(val == 0xFF):
            return True
        else:
            return False
          
    def i2c_read_eeprom(self, dummy = False):
        command = MemClient.I2C_READ_EEPROM | MemClient.COMMAND_SENT
        length = 12
        if (dummy == True):
            command = command | MemClient.DUMMY_FUNC
        val = 0xFF
        sock_msg = struct.pack('III', command, length, val)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.host, self.port))
        s.sendall(sock_msg)
        response = recvall(s, 12)
        s.close()
        (response_command, response_length, val) = struct.unpack('III', response)
        if(val == 0xFF):
            return True
        else:
            return False       
        
    def file_transfer(self, file_to_read, file_write_path, dummy = False):   
        print '\nTesting file transfer...'        
        path_size = len(file_write_path)    
        print path_size
        # Size of the file transferred
        fp = open(file_to_read, "rb")
        fp.seek(0, os.SEEK_END)
        size = fp.tell()
        fp.close()
        
        print 'File size = ',
        print size,
        print ' bytes'
        command = MemClient.FILE_TRANSFER | MemClient.COMMAND_SENT
        length = 12 + path_size + size
        if (dummy == True):
            command = command | MemClient.DUMMY_FUNC        

        sock_msg = struct.pack('III', command, length, path_size)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.host, self.port))
        s.sendall(sock_msg)

        # Transfer file_path and the file
        s.send(file_write_path)
        
        # Read the file to be transferred
        fp = open(file_to_read, "rb")
        packet_size = 1024
        print("Reading file...")
 
        file_data = fp.read(packet_size)
        while(file_data):
            s.send(file_data)
            file_data = fp.read(packet_size)

        fp.close()  
        response = recvall(s, 12)
        (response_command, response_length, val) = struct.unpack('III', response)
        s.close()
        print 'Files transfer done!'
        return val
        
    def read_eeprom_id(self, i2c_output_base_reg, i2c_input_base_reg):
        #string = 'sSA0S00psSA1RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRQp'
        string = 'sSA0S00psSA1RRRRRRRRRRRRRRRRRRRQp'
        ret = MemClient.send_dc590(self, i2c_output_base_reg, i2c_input_base_reg, string)
        eeprom_id = ''
        result = ''
        count = 0
        for character in ret:
            result = result + character    
            count = count + 1
            if(count == 2):
                #print result
                hex_result = '0x'+result
                #print hex_result
                eeprom_id = eeprom_id + chr(int(hex_result, 16))
                result = ''
                count = 0
        #print eeprom_id    
        return eeprom_id
        
        
    def send_dc590(self, i2c_output_base_reg, i2c_input_base_reg, DC590_command, dummy = False):
        size = len(DC590_command)
        command = MemClient.DC590_TPP_COMMANDS | MemClient.COMMAND_SENT
        length = 16 + size
        if (dummy == True):
            command = command | MemClient.DUMMY_FUNC   
        sock_msg = struct.pack('IIII', command, length, i2c_output_base_reg, i2c_input_base_reg)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.host, self.port))
        s.sendall(sock_msg)
        s.send(str(DC590_command))
        
        response = recvall(s, 8)
        ret = s.recv(100)
        (response_command, response_length) = struct.unpack('II', response)
        
        s.close()
#        print 'DC590 command executed!'
#        print type(ret)
#        print 'String returned: ',
#        print ret
#        print 'String returned in hex: ',
#        for i in range(1, len(ret)):
#            print format(ord(ret[i]), "x"),
#            print ', ',
        return ret

        
        
    def send_json(self, command_line, dummy = False):
                
        sock_msg = json.loads('{"command": "60", "command_line": "cd fpga_bitfiles"}')
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.host, self.port))
        s.sendall(sock_msg)
        
        response = recvall(s, 12)
        # third parameter is the register location that was last written into
        (response_command, response_length, last_location) = struct.unpack('III', response)
        s.close()
        return 1
        
    def shutdown(self, dummy = False):
        command = MemClient.SHUTDOWN | MemClient.COMMAND_SENT
        length = 12
        if (dummy == True):
            command = command | MemClient.DUMMY_FUNC
        val = 0x48414C54 # "HALT" in ASCII
        sock_msg = struct.pack('III', command, length, val)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.host, self.port))
        s.sendall(sock_msg)
        response = recvall(s, 12)
        s.close()
        (response_command, response_length, halt_command) = struct.unpack('III', response)
        if(halt_command == 0x48414C54):
            return True
        else:
            return False

#    def handle_command(self, command, length, payload):
#        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#        s.connect((self.host, self.port))
#        
#        if(length == 12):
#            transmit_packet = struct.pack('III', (command | MemClient.COMMAND_SENT), length, payload)
#        elif(length == 16):
#            transmit_packet = struct.pack('IIII', (command | MemClient.COMMAND_SENT), length, payload[0], payload[1]) 
#        
#        print '\nTransmitting command: ',
#        print command
#        print 'Length of packet: ',
#        print length
#        s.sendall(transmit_packet)
#
#        response = s.recv(8) # Specify the maximum number of bytes that can be received.
#        (command_received, length_received) = struct.unpack('II', response)      
#        print 'Response received: ',
#        print command_received
#        print 'Length received: ',
#        print length_received
#        #size_payload = length_received - 8
#        size_payload = 4
#        print 'Expected response payload size: ',
#        print size_payload
#        payload = recvall(s, size_payload)
#
#        
#        print 'Size of payload: ',       
#        print len(payload)
#        
#        if(length_received == 12):
#            payload_received = struct.unpack('I', payload)[0]
#        elif(length_received == 16):
#            payload_received = struct.unpack('II', payload)
#        else:
#            payload_received = payload
#        
#        command_key = command_received & 0x00FFFFFF
#        
#        if(command_received != (command | MemClient.RESPONSE_RECEIVED)):
#            print 'Received corrupted response packet - Wrong command field received!!'
#        if(command_received & MemClient.RESPONSE_RECEIVED != MemClient.RESPONSE_RECEIVED):
#            print 'Received corrupted response packet - Response bit not set!!'
#        if(command_received & MemClient.ERROR == MemClient.ERROR):
#            print 'Received ERROR bit!!'
#            
#        # check for 0xDEADC0DE
#        s.close()
#        
##        response = recvall(s, 12)
##        (command_received, length_received, payload_received) = struct.unpack('III', response)        
##        s.close()
#        
#        return payload_received
        
        
if __name__ == '__main__':
    client = MemClient()

    print('Starting client')
    print('Read from register 16: ' + str(client.reg_read(16)))
    client.reg_write(16, 234)
    #print('reading and writing test.csv')
    #client.mem_read(0, 100, os.path.join(basedir, 'test.csv'))
    #client.mem_write(0, 100, os.path.join(basedir, 'test.csv'))
    #client.mem_read(0, 100, 'test.csv')
    #client.mem_write(0, 100, 'test.csv')
    print('Reading a block...')
    numsamps = 1024
    dummy, block = client.mem_read_block(16777216, numsamps)
    data = (ctypes.c_uint * numsamps).from_buffer(bytearray(block))
    print('Got a %d byte block back' % len(block))
    print('first 16 elements:')
    for i in range(0, 16):
        print('value %d' % data[i])
    print('and the last element: %d' % data[numsamps - 1])
    
    
    
    
    
#    def send_msg(self, cmd=0, length=0, param1=0, param2=0, msg=''):
#        # assemble socket message
#        sock_msg = struct.pack('IIII64s', cmd, length, param1, param2, msg)
#        if (cmd == MemClient.MEM_READ_BLOCK):
#            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#            s.connect((self.host, self.port))
#            s.sendall(sock_msg)
#            sleep(1.0)
#            ret = 0
#            block = recvall(s, param2 * 4)
#            #print ('got this block: ' + repr(block))
#            s.close()
#        else:    
#            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#            s.connect((self.host, self.port))
#            s.sendall(sock_msg)
#            response = s.recv(128)
#            block = ''
#            ret = struct.unpack('I', response)[0]
#            s.close()
#        return ret, block