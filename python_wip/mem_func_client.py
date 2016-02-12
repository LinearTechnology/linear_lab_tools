#!/usr/bin/python
'''
Client to communicate with socket daemon running in the HPS side of an Altera SoC.

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




import os
from subprocess import call
import socket
import ctypes
import struct
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

class MemClient(object):
    """Class for the socket server"""

    #cmd_id
    REG_READ = 1
    REG_WRITE = 2
    MEM_READ = 3
    MEM_WRITE = 4
    MEM_READ_BLOCK = 5

    def __init__(self, host='localhost', port=1994):
        self.port = port
        self.host = host
    
    def send_msg(self, cmd=0, param1=0, param2=0, msg=''):
        # assemble socket message
        sock_msg = struct.pack('III64s', cmd, param1, param2, msg)
        if (cmd == MemClient.MEM_READ_BLOCK):
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((self.host, self.port))
            s.sendall(sock_msg)
            sleep(1.0)
            ret = 0
            block = recvall(s, param2 * 4)
            #print ('got this block: ' + repr(block))
            s.close()
        else:    
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((self.host, self.port))
            s.sendall(sock_msg)
            response = s.recv(128)
            block = ''
            ret = struct.unpack('I', response)[0]
            s.close()
        return ret, block

    def reg_read(self, address):
        if (address % 4 != 0):
            print('Address needs to be word aligned.')
            return 0

        if (address > 0x100000):
            print('Address out of range. Must be less than 0x100000')
            return 0

        reg_value, dummyblock = self.send_msg(MemClient.REG_READ, address)
        #print('Read %d from %x' % (reg_value, address))
        return reg_value

    def reg_write(self, address, value):
        if (address % 4 != 0):
            print('Address needs to be word aligned.')
            return 0

        if (address > 0x100000):
            print('Address out of range. Must be less than 0x100000')
            return 0

        ret, dummyblock = self.send_msg(MemClient.REG_WRITE, address, value)
        return ret

    def mem_read(self, address, size, filename):
        if (address % 4 != 0):
            print('Address needs to be word aligned.')

        if (address > 0x40000000):
            print('Address out of range. Must be less than 0x40000000')
            return 0

        ret, dummyblock = self.send_msg(MemClient.MEM_READ, address, size, filename)

    def mem_write(self, address, size, filename):
        if (address % 4 != 0):
            print('Address needs to be word aligned.')

        if (address > 0x40000000):
            print('Address out of range. Must be less than 0x40000000')
            return 0

        ret, dummyblock = self.send_msg(MemClient.MEM_WRITE, address, size, filename)

    def mem_read_block(self, address, size):
        ret, dummyblock = self.send_msg(MemClient.MEM_READ_BLOCK, address, size)
        return ret, dummyblock

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