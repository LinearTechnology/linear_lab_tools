

classdef MemFuncClient
    properties
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
    end
    
    methods

        function obj = MemFuncClient
            disp('MemFuncClient Constructor');
        end

        function register_value = reg_read(obj, address, dummy)
            if nargin < 2
                dummy = false;
            end
            
            if dummy == true
                command = obj.REG_READ + obj.DUMMY_FUNC + obj.COMMAND_SENT;
            else
                command = obj.REG_READ + obj.COMMAND_SENT;
            end
            length = 12;

            t = tcpip('10.54.1.128', 1992, 'NetworkRole', 'client');
            fopen(t);
            fwrite(t, swap4Bytes(command), 'uint32');   % big endian
            fwrite(t, swap4Bytes(length), 'uint32');    % big endian
            fwrite(t, swap4Bytes(address), 'uint32');   % big endian

            ret = fread(t, 3, 'uint32');
            response = uint32(swap4Bytes(ret(1)));
            length_returned = uint32(swap4Bytes(ret(2)));
            register_value = uint32(swap4Bytes(ret(3)));
            
            fprintf('\nResponse command: 0x');
            disp(dec2hex(response));
            fprintf('Response packet length: %d\n', length_returned);
            fprintf('Register value read: %d\n', register_value);
            
            fclose(t);
            delete(t)
            clear t
        end
        
        function register_location = reg_write(obj, address, value, dummy)
            if nargin < 3
                dummy = false;
            end
            
            if dummy == true
                command = obj.REG_WRITE + obj.DUMMY_FUNC + obj.COMMAND_SENT;
            else
                command = obj.REG_WRITE + obj.COMMAND_SENT;
            end
            length = 16;

            t = tcpip('10.54.1.128', 1992, 'NetworkRole', 'client');
            fopen(t);
            fwrite(t, swap4Bytes(command), 'uint32');   % big endian
            fwrite(t, swap4Bytes(length), 'uint32');    % big endian
            fwrite(t, swap4Bytes(address), 'uint32');   % big endian
            fwrite(t, swap4Bytes(value), 'uint32');   % big endian

            ret = fread(t, 3, 'uint32');
            response = uint32(swap4Bytes(ret(1)));
            length_returned = uint32(swap4Bytes(ret(2)));
            register_location = uint32(swap4Bytes(ret(3)));
            
            fprintf('\nResponse command: 0x');
            disp(dec2hex(response));
            fprintf('Response packet length: %d\n', length_returned);
            fprintf('Register location written into: %d\n', register_location);
            
            fclose(t);
            delete(t)
            clear t
        end 
    end
end    


function ret = swap4Bytes(value)
    a = uint32(value);
    ret = swapbytes(a);
end
    

    
