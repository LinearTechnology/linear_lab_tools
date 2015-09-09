classdef LtcHighSpeedComm < handle
% LtcHighSpeedComm Wrapper for LtcHighSpeedComm.dll
% It provides a class and some constants used to communicate with 
% high-speed Linear Technology devices using an off-the-shelf FPGA 
% demo-board and an LTC communication interface board. It requires the FPGA
% be loaded with an LTC bit-file and allows high-speed data transfer, SPI 
% communication and FPGA configuration. Note that there is no open command,
% the device is opened automatically as needed. There is a close method, 
% but it is not necessary to call it, the destructo will close the handle. 
% If there is an error or the close method is called, the device will again
% be opened automatically as needed.
% To connect do something like this:
% lths = LtcHighSpeedComm();
%     
%     deviceInfoList = lths.ListDevices();
%     deviceInfo = [];
%     for info = deviceInfoList
%        % here you could use did = lths.Init(deviceInfo); to open each
%        % device and query it to make sure it is the device, or you could
%        % check info.description or info.serialNumber, or even just take
%        % the first device, depending on your needs. If you open multiple
%        % devices you aren't going to use, you should Cleanup them, or 
%        % they will be unavailable until the lths object goes out of scope
%        if thisIsTheOneWeWant
%            device_info = info;
%            break;
%        end
%     end
% 
%     if isempty(deviceInfo)
%         error('TestLtcHighSpeedComm:noDevice', ...
%            'could not find compatible device');
%     end
% 
%     % init a device and get an id
%     did = lths.Init(deviceInfo);
%     lths.SetBitMode(did, lths.BIT_MODE_MPSSE);
%     ltsh.GpioWriteHighByte(did, 0xFF);

    properties (Constant)
        BIT_MODE_MPSSE = 0 % argument to set_mode for non-FIFO mode.
        BIT_MODE_FIFO = 1  % argument to set_mode for fast FIFO mode.
        
        SPI_CHIP_SELECT_LOW = 0
        SPI_CHIP_SELECT_HIGH = 1
    end
    
    properties (Access = private)
        handles;        
        nextIndex;
        libraryName;
    end
       
    methods (Access = private)
        function ErrorOnBadStatus(self, did, errorEd, status)
            if status ~= 0
                message = repmat(' ', 1, 256);
                [~, ~, message] = calllib(self.libraryName, ...
                    'LthsGetErrorInfo', self.handles{did}, message, 256);
                error(['LtcHighSpeedComm:', errorEd],  message);
            end
        end
        
        function varargout = CallWithStatus(self, did, func, varargin)
            handle = self.handles{did};
            if handle.value == 0
                error(['LtcHighSpeedComm:', func], 'Device has already been cleaned up');
            end
            [varargout{1:nargout}] = calllib(self.libraryName, func, ...
                handle, varargin{:});
        end
        
        function varargout = Call(self, did, func, varargin)
            [status, ~, varargout{1:nargout}] = ...
                self.CallWithStatus(did, func, varargin{:});
            self.ErrorOnBadStatus(did, func, status);
        end
    end
    
    methods (Static)
        function deviceList = ListDevices()
            % returns an array of 1 structure per connected high speed
            % device.  The structure has a description field and a serial
            % number field that can be used to determine if this is a
            % desired device. Pass the structure corresponding to the 
            % desired device into Init to open the device and get a did.
            nDevices = uint32(0);
            [status, nDevices] = calllib(self.libraryName, ...
                'LthsCreateDeviceList', nDevices);
            if status ~= 0
                error('LtcHighSpeedComm:ListDevices', 'Error creating device list');
            end
            
            if nDevices == 0
                error('LtcHighSpeedComm:ListDevices', 'No devices found');
            end
            
            deviceStructArray = uint8(zeros(1, 88 * nDevices));
            [status, deviceStructArray] = calllib(self.libraryName, ...
                'LthsGetDeviceList', deviceStructArray, nDevices);
            
            if status ~= 0
                error('LtcHighSpeedComm:ListDevices', 'Error getting the device list');
            end
            
            deviceList = struct('indices', cell(1, nDevices), ...
                'serialNumber', cell(1, nDevices), ...
                'description', cell(1, nDevices));
            byteIndex = 1;
            for i = 1:nDevices
                deviceList(i).indices = typecast(...
                    deviceStructArray(byteIndex:byteIndex+7), 'uint32');
                byteIndex = byteIndex + 8;
                
                if deviceList(i).indices(1) == 4294967295
                    deviceList = deviceList(1:(i-1));
                    break;
                end
                
                serialNumber = deviceStructArray(byteIndex:(byteIndex+11));
                serialNumber = serialNumber(1:(find(serialNumber == 0, 1, 'first')-1));
                deviceList(i).serialNumber = char(serialNumber);
                byteIndex = byteIndex + 16;
                description = deviceStructArray(byteIndex:(byteIndex+63));
                description = description(1:(find(description == 0, 1, 'first')-1));
                deviceList(i).description = char(description);
                byteIndex = byteIndex + 64;
            end
        end
    end
    
    methods    
        function self = LtcHighSpeedComm
            % High speed comm constructor; you need only one of these to 
            % talk to multiple devices. This loads the native DLL as well.
            
            archStr = computer;
            if strcmp(archStr((end-1):end), '64')
                self.libraryName = 'LtcHighSpeedComm64.dll';
            else
                self.libraryName = 'LtcHighSpeedComm.dll';
            end
            
            loadlibrary(self.libraryName, @LtcHighSpeedCommProto);
            self.handles = {};
            self.nextIndex = 1;
        end
        
        function delete(self)
            % the destructor automatically cleans up all devices that were
            % opened (Init) and then unloads the native DLL.
            for i = 1:length(self.handles)
                if self.handles{i}.value ~= 0
                    calllib(self.libraryName, 'LthsCleanup', self.handles{i});
                end
            end
            unloadlibrary(self.libraryName);
        end
        
        function did = Init(self, deviceInfo)
            % takes a deviceInfo struct and returns a did, a device ID used
            % by (almost) all the subequent methods to talk to a device.
            deviceStruct = struct(...
                'serial_number', uint8(zeros(1, 16)), ...
                'description', uint8(zeros(1,64)), ...
                'indices', uint8(deviceInfo.indices));
            n = length(deviceInfo.serialNumber);
            deviceStruct.serial_number(1:n) = deviceInfo.serialNumber;
            n = length(deviceInfo.description);
            deviceStruct.description(1:n) = deviceInfo.description;
            
            handle = libpointer('voidPtr', 0);
            status = calllib(self.libraryName, 'LthsInitDevice', handle, deviceStruct);
            if status ~= 0
                error('LtcHighSpeedComm:LtcHighSpeedComm', ...
                    'Error creating device');
            end
            did = self.nextIndex;
            self.handles{did} = handle;
            self.nextIndex = self.nextIndex + 1;
        end
        
        function Cleanup(self, did)
            % cleanup method closes the device and deletes the underlying
            % native pointer. This can be called manually if you are not 
            % going to use the device anymore and you want it to be
            % available to the system. This is called automatically
            % for all open devices whenever the LtcHighSpeedComm goes away.
           self.CallWithStatus(did, 'LthsCleanup');
           self.handles{did}.value = 0;
        end
        
        function description = GetDescription(self, did)
            % Return the current device's serial number.
            description = self.Call(did, 'LthsGetDescription', blanks(64), ...
                64);
        end
        
        function serialNumber = GetSerialNumber(self, did)
            % Return the current device's description.
            serialNumber = self.Call(did, 'LthsGetSerialNumber', ...
                blanks(16), 16);
        end
        
        function SetTimeouts(self, did, readTimeout, writeTimeout)
            % Set read and write time-outs.
            self.Call(did, 'LthsSetTimeouts', int32(readTimeout), ...
                int32(writeTimeout));
        end
        
        function SetBitMode(self, did, bitMode)
            % Set the device to MPSSE mode (for SPI, FPGA registers and
            % GPIO) or FIFO mode (for fast FIFO communication)
            if bitMode == self.BIT_MODE_FIFO
                mode = 64;
            elseif bitMode == self.BIT_MODE_MPSSE
                mode = 2;
            else
                error('LtcHighSpeedComm:setBitMode', ...
                    'bitMode must be BIT_MODE_MPSSE or BIT_MODE_FIFO');
            end
            self.Call(did, 'LthsSetBitMode', mode);
        end
        
        function PurgeIo(self, did)
            % Clear all data in the USB I/O buffers.
            self.Call(did, 'LthsPurgeIo');
        end
        
        function Close(self, did)
            % Close the device, but keep the handle, device will be
            % automatically re-opened if needed.
            self.CallWithStatus(did, 'LthsClose');
        end
        
        function FifoSetHighByteFirst(self, did)
            % Make calls to fifo_send/receive_uint16/32_values send/receive
            % high byte first.
            self.Call(did, 'LthsFifoSetHighByteFirst');
        end
        
        function FifoSetLowByteFirst(self, did)
            % Make calls to fifo_send/receive_uint16/32_values send/receive
            % low byte first.
            self.Call(did, 'LthsFifoSetLowByteFirst');
        end
        
        function nSent = FifoSendBytes(self, did, values)
            % Send values as bytes via FIFO
            nSent = 0;
            [~, nSent] = self.Call(did, 'LthsFifoSendBytes', ...
                values, length(values), nSent);
        end
        
        function nSent = FifoSendUint16Values(self, did, values)
            % Send values as uint16 values via FIFO
            nSent = 0;
            [~, nSent] = self.Call(did, 'LthsFifoSendUint16Values', values, ...
                length(values), nSent);
        end
        
        function nSent = FifoSendUint32Values(self, did, values)
            % send values as uint32 values via FIFO
            nSent = 0;
            [~, nSent] = self.Call(did, 'LthsFifoSendUint32Values', values, ...
                length(values), nSent);
        end
        
        function values = FifoReceiveBytes(self, did, nValues)
            % read nValues bytes via FIFO and return as values
            values = uint8(zeros(nValues, 1));
            nBytes = 0;
            [values, nBytes] = self.Call(did, 'LthsFifoReceiveBytes', values, ...
                nValues, nBytes);
            values = values(1:nBytes, 1);
        end
        
        function [values, nBytes] = FifoReceiveUint16Values(self, did, nValues)
            % read nValues uint16 values via FIFO and return as values
            values = uint16(zeros(nValues, 1));
            nBytes = 0;
            [values, nBytes] = self.Call(did, 'LthsFifoReceiveUint16Values', ...
                values, nValues, nBytes);
            values = values(1:ceil(nBytes/2), 1);
        end
        
        function [values, nBytes] = FifoReceiveUint32Values(self, did, nValues)
            % read nValues uint32 values via FIFO and return as values
            values = uint32(zeros(nValues, 1));
            nBytes = 0;
            [values, nBytes] = self.Call(did, 'LthsFifoReceiveUint32Values', ...
                values, nValues, nBytes);
            values = values(1:ceil(nBytes/4), 1);
        end
        
        function SpiSendBytes(self, did, values)
            % Send values via SPI controlling chip select.
            self.Call(did, 'LthsSpiSendBytes', values, length(values));
        end
        
        function values = SpiReceiveBytes(self, did, nValues)
            % Receive nValues bytes via SPI controlling chip select.
            values = uint8(zeros(nValues, 1));
            values = self.Call(did, 'LthsSpiReceiveBytes', values, nValues);
        end
        
        function receiveValues = SpiTransceiveBytes(self, did, sendValues)
            % Transceive sendValues via SPI controlling chip select.
            nValues = length(sendValues);
            receiveValues = uint8(zeros(nValues, 1));
            [~, receiveValues] = self.Call(did, 'LthsSpiTransceiveBytes', ...
                sendValues, receiveValues, nValues);
        end
        
        function SpiSendByteAtAddress(self, did, address, value)
            % Write an address and a value via SPI.
            % Many SPI devices adopt a convention similar to I2C addressing
            % where a byte is sent indicating which register address the
            % rest of the data pertains to. Often there is a read-write bit
            % in the address, this function will not shift or set any bits 
            % in the address, it basically just writes two bytes, the 
            % address byte and data byte one after the other.
            self.Call(did, 'LthsSpiSendByteAtAddress', address, value);
        end
        
        function SpiSendBytesAtAddress(self, did, address, values)
            % Write an address byte and values via SPI.
            % Many SPI devices adopt a convention similar to I2C addressing
            % where a byte is sent indicating which register address the 
            % rest of the data pertains to. Often there is a read-write bit
            % in the address, this function will not shift or set any bits 
            % in the address, it basically just writes the address byte and
            % data bytes one after the other.
            self.Call(did, 'LthsSpiSendBytesAtAddress', address, ...
                values, length(values));
        end
        
        function value = SpiReceiveByteAtAddress(self, did, address)
            % Write an address and receive a value via SPI; return the 
            % value. Many SPI devices adopt a convention similar to I2C 
            % addressing, where a byte is sent indicating which register 
            % address the rest of the data pertains to. Often there is a 
            % read-write bit in the address, this function will not shift 
            % or set any bits in the address, it basically just writes two 
            % bytes, the address byte and data byte one after the other.
            value = 0;
            value = self.Call(did, 'LthsSpiReceiveByteAtAddress', address, ...
                value);
        end
        
        function values = SpiReceiveBytesAtAddress(self, did, address, ...
                nValues)
            % Receive nValues bytes via SPI at an address.
            % Many SPI devices adopt a convention similar to I2C addressing
            % where a byte is sent indicating which register address the 
            % rest of the data pertains to. Often there is a read-write bit
            % in the address, this function will not shift or set any bits 
            % in the address, it basically just writes the address byte and
            % data bytes one after the other. 
            values = uint8(zeros(nValues, 1));
            values = self.Call(did, 'LthsSpiReceiveBytesAtAddress', address, ...
                values, nValues);
        end
        
        function SpiSetChipSelect(self, did, chipSelect)
            % Set the SPI chip-select high or low.
            if chipSelect == self.SPI_CHIP_SELECT_HIGH
                state = 1;
            elseif chipSelect == self.SPI_CHIP_SELECT_LOW
                state = 0;
            else
                error('LtcHighSpeedComm:spiSetChipSelect', ...
                    ['PinState must be SPI_CHIP_SELECT_HIGH or ', ...
                    'SPI_CHIP_SELECT_LOW']);
            end
            self.Call(did, 'LthsSpiSetChipSelect', state);
        end
        
        function SpiSendNoChipSelect(self, did, values)
            % Send values via SPI without controlling chip-select.
            self.Call(did, 'LthsSpiSendNoChipSelect', values, length(values));
        end
        
        function values = SpiReceiveNoChipSelect(self, did, nValues)
            % Receive nValues bytes via SPI without controlling SPI
            values = uint8(zeros(nValues, 1));
            values = self.Call(did, 'LthsSpiReceiveNoChipSelect', ...
                values, nValues);
        end
        
        function receiveValues = SpiTransceiveNoChipSelect(self, did, ...
                sendValues)
            % Transceive sendValues bytes via SPI without controlling SPI
            nValues = length(sendValues);
            values = uint8(zeros(nValues, 1));
            [~, receiveValues] = self.Call(did, ...
                'LthsSpiTransceiveNoChipSelect', sendValues, ...
                values, nValues);
        end
        
        function FpgaToggleReset(self, did)
            % Set the FPGA reset bit low then high.
            self.Call(did, 'LthsFpgaToggleReset');
        end
        
        function FpgaWriteAddress(self, did, address)
            % Set the FPGA address to write or read.
            self.Call(did, 'LthsFpgaWriteAddress', address);
        end
        
        function FpgaWriteData(self, did, data)
            % Write a value to the current FPGA address.
            self.Call(did, 'LthsFpgaWriteData', data);
        end
        
        function data = FpgaReadData(self, did)
            % Read a value from the current FPGA address and return it.
            data = 0;
            data = self.Call(did, 'LthsFpgaReadData', data);
        end
        
        function FpgaWriteDataAtAddress(self, did, address, data)
            % Set the current address and write a value to it.
            self.Call(did, 'LthsFpgaWriteDataAtAddress', address, data);
        end
        
        function data = FpgaReadDataAtAddress(self, did, address)
            % Set the current address and read a value from it.
            data = 0;
            data = self.Call(did, 'LthsFpgaReadDataAtAddress', address, ...
                data);
        end
        
        function GpioWriteHighByte(self, did, value)
            % Set the GPIO high byte to a value.
            self.Call(did, 'LthsGpioWriteHighByte', value);
        end
        
        function value = GpioReadHighByte(self, did)
            % Read the GPIO high byte and return the value.
            value = 0;
            value = self.Call(did, 'LthsGpioReadHighByte', value);
        end
        
        function GpioWriteLowByte(self, did, value)
            % Set the GPIO low byte to a value.
            self.Call(did, 'LthsGpioWriteLowByte', value);
        end
        
        function value = GpioReadLowByte(self, did)
            % Read the GPIO low byte and return the value
            value = 0;
            value = self.Call(did, 'LthsGpioReadLowByte', value);
        end
        
        function FpgaEepromSetBitBangRegister(self, did, registerAddress)
            % Set the FPGA register used to do bit-banged I2C.
            % If not called, address used is 0x11.
            self.Call(did, 'LthsFpgaEepromSetBitBangRegister', registerAddress);
        end
               
        function string = FpgaEepromReadString(self, did, nChars)
            % Receive string at an address over bit-banged I2C via FPGA reg
            % Address must be a 7-bit address, it will be left-shifted
            % internally.
            string = self.Call(did, 'LthsFpgaEepromReadString', blanks(nChars), nChars);
        end
    end
end

