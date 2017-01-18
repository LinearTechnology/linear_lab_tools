

function MemFuncClient()

    % cmd_id
    REG_READ = 1;
    REG_WRITE = 2;
    MEM_READ = 3;
    MEM_WRITE = 4;
    REG_READ_BLOCK = 5; % to be handled
    REG_WRITE_BLOCK = 6;
    MEM_READ_BLOCK = 7;
    MEM_WRITE_BLOCK = 8; % to be handled
    MEM_READ_TO_FILE = 9;
    MEM_WRITE_FROM_FILE = 10;
    REG_WRITE_LUT = 11;
    
    I2C_DC590 = 90;
    I2C_IDENTIFY = 12;
    I2C_WRITE_BYTE = 17;
    I2C_TESTING = 18;
    I2C_READ_EEPROM = 19;
    
    FILE_TRANSFER = 80;
    
    SHUTDOWN = 1024;

    ERROR = hex2dec('80000000');
    COMMAND_SENT = hex2dec('40000000');
    RESPONSE_RECEIVED = hex2dec('20000000');
    DUMMY_FUNC = hex2dec('10000000');
    


    command = '1';
    length = '08000000';
    address = '63';


    % 201326592 = 0x 0C 00 00 00 --> 12

    % dummand command reg read (1): 0x 50 00 00 01
    % byte order inversion : 0x 01 00 00 50 = 16777296

    
    sendPacket(2, 16);
    register_value = reg_read(1000)
end

function sendPacket(command, length)
    t = tcpip('10.54.1.128', 1992, 'NetworkRole', 'client');
    %t.ByteOrder = 'bigEndian';     % this made no difference
    fopen(t);
    fwrite(t, swap4Bytes(command), 'uint32');   % big endian
    fwrite(t, swap4Bytes(length), 'uint32');   % big endian
    fwrite(t, swap4Bytes(1000), 'uint32');   % big endian
    fwrite(t, swap4Bytes(100), 'uint32');   % big endian
    fclose(t);
    delete(t)
    clear t
end

function ret = swap4Bytes(value)
    a = uint32(value);
    ret = swapbytes(a);
end
    
function register_value = reg_read(address, dummy)
    if nargin < 2
        dummy = false;
    end
    
    %command = REG_READ + COMMAND_SENT;
    command = 1073741825;
    length = 12;
    
    t = tcpip('10.54.1.128', 1992, 'NetworkRole', 'client');
    fopen(t);
    fwrite(t, swap4Bytes(command), 'uint32');   % big endian
    fwrite(t, swap4Bytes(length), 'uint32');    % big endian
    fwrite(t, swap4Bytes(address), 'uint32');   % big endian
    
    register_value = fread(t, 3, 'uint32');
    %register_value = fread(t,t.BytesAvailable, 'uint32')
    %  s = fread(fid,120,'40*uchar=>uchar',8, 'ieee-be');
    fclose(t);
    delete(t)
    clear t
end
    
