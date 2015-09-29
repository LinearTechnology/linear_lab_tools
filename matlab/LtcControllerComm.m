classdef LtcControllerComm < handle
% LtcControllerComm Wrapper for LtcControllerComm.dll
% It provides a class and some constants used to communicate with 
% high-speed Linear Technology devices using an off-the-shelf FPGA 
% demo-board and an LTC communication interface board. It requires the FPGA
% be loaded with an LTC bit-file and allows high-speed data transfer, SPI 
% communication and FPGA configuration. Note that there is no open command,
% the device is opened automatically as needed. There is a close method, 
% but it is not necessary to call it, the destructor will close the handle. 
% If there is an error or the close method is called, the device will again
% be opened automatically as needed.
% To connect do something like this:
% controller = LtcControllerComm();
%     
%     controllerInfoList = controller.ListDevices();
%     controllerInfo = [];
%     for info = controllerInfoList
%        % here you could use did = controller.Init(deviceInfo); to open each
%        % device and query it to make sure it is the controller, or you could
%        % check info.description or info.serialNumber, or even just take
%        % the first controller, depending on your needs. If you open multiple
%        % devices you aren't going to use, you should Cleanup them, or 
%        % they will be unavailable until the Lcc object goes out of scope
%        if thisIsTheOneWeWant
%            controllerInfo = info;
%            break;
%        end
%     end
% 
%     if isempty(controlerInfo)
%         error('TestLtcControllerComm:noDevice', ...
%            'could not find compatible device');
%     end
% 
%     % init a device and get an id
%     did = controller.Init(controllerInfo);

    properties (Constant)
        HS_BIT_MODE_MPSSE = 0 % argument to set_mode for non-FIFO mode.
        HS_BIT_MODE_FIFO = 1  % argument to set_mode for fast FIFO mode.
        
        SPI_CS_STATE_LOW = 0
        SPI_CS_STATE_HIGH = 1
        
        TYPE_NONE = uint32(0)
        TYPE_DC1371 = uint32(1)
        TYPE_DC718 = uint32(2)
        TYPE_DC890 = uint32(4)
        TYPE_HIGH_SPEED = uint32(8)
        TYPE_UNKNOWN = uint32(4294967295)
        
        TRIGGER_NONE = 0
        TRIGGER_START_POSITIVE_EDGE = 1
        TRIGGER_DC890_START_NEGATIVE_EDGE = 2
        TRIGGER_DC1371_STOP_NEGATIVE_EDGE = 3

        DC1371_CHIP_SELECT_ONE = 1
        DC1371_CHIP_SELECT_TWO = 2
        
    end
    
    properties (Access = private)
        handles;        
        nextIndex;
        libraryName;
    end
       
    methods (Access = private)
        function ErrorOnBadStatus(self, did, status)
            if status ~= 0
                errorIds = {'OK', 'HardwareError', 'InvalidArgument', 'LogicError', ...
                    'NotSupported', 'UserAborted', 'UnknownError'};
                errorId = errorIds{-status};
                message = repmat(' ', 1, 256);
                [~, ~, message] = calllib(self.libraryName, ...
                    'LccGetErrorInfo', self.handles{did}, message, 256);
                error(['LtcControllerComm:', errorId],  message);
            end
        end
        
        function varargout = CallWithStatus(self, did, func, varargin)
            handle = self.handles{did};
            if handle.value == 0
                error('LtcControllerComm:InvalidArgument', 'Device has already been cleaned up');
            end
            [varargout{1:nargout}] = calllib(self.libraryName, func, handle, varargin{:});
        end
        
        function varargout = Call(self, did, func, varargin)
            [status, ~, varargout{1:nargout}] = ...
                self.CallWithStatus(did, func, varargin{:});
            self.ErrorOnBadStatus(did, status);
        end
    end
    
    methods    
        function self = LtcControllerComm
            % High speed comm constructor; you need only one of these to 
            % talk to multiple devices. This loads the native DLL as well.
            
            archStr = computer;
            location = winqueryreg('HKEY_LOCAL_MACHINE', ...
                'SOFTWARE\\Linear Technology\\LinearLabTools', 'Location');
            if strcmp(archStr((end-1):end), '64')
                self.libraryName = 'ltc_controller_comm64';
            else
                self.libraryName = 'ltc_controller_comm';
            end
            
            loadlibrary([location, self.libraryName, '.dll'], @LtcControllerCommProto);
            self.handles = {};
            self.nextIndex = 1;
        end
        
        function delete(self)
            % the destructor automatically cleans up all devices that were
            % opened (Init) and then unloads the native DLL.
            for i = 1:length(self.handles)
                if self.handles{i}.value ~= 0
                    calllib(self.libraryName, 'LccCleanup', self.handles{i});
                end
            end
            unloadlibrary(self.libraryName);
        end
        
        function deviceList = ListControllers(self, type, maxControllers)
            % returns an array of 1 structure per connected controllers
            % device.  The structure has a description field and a serial
            % number field that can be used to determine if this is a
            % desired device. Pass the structure corresponding to the 
            % desired device into Init to open the device and get a did.
            nDevices = uint32(0);
            [status, nDevices] = calllib(self.libraryName, ...
                'LccGetNumControllers', type, maxControllers, nDevices);
            if status ~= 0
                error('LtcControllerComm:ListControllers', 'Error creating controller list');
            end
            
            if nDevices == 0
                error('LtcControllerComm:ListControllers', 'No controllers found');
            end
            
            controllerStructArray = uint8(zeros(1, 88 * nDevices));
            [status, controllerStructArray] = calllib(self.libraryName, ...
                'LccGetControllerList', type, controllerStructArray, nDevices);
            
            if status ~= 0
                error('LtcControllerComm:ListControllers', 'Error getting the controller list');
            end
            
            deviceList = struct('type', cell(1, nDevices), ...
                'description', cell(1, nDevices), ...
                'serialNumber', cell(1, nDevices), ...
                'id', cell(1, nDevices));
            byteIndex = 1;
            for i = 1:nDevices
                deviceList(i).type = typecast(...
                    controllerStructArray(byteIndex:byteIndex+3), 'int32');
                byteIndex = byteIndex + 4;
                
                description = controllerStructArray(byteIndex:(byteIndex+63));
                description = description(1:(find(description == 0, 1, 'first')-1));
                deviceList(i).description = char(description);
                byteIndex = byteIndex + 64;               
                
                serialNumber = controllerStructArray(byteIndex:(byteIndex+15));
                serialNumber = serialNumber(1:(find(serialNumber == 0, 1, 'first')-1));
                deviceList(i).serialNumber = char(serialNumber);
                byteIndex = byteIndex + 16;
                
                deviceList(i).id = typecast(...
                    controllerStructArray(byteIndex:byteIndex+3), 'uint32');
                byteIndex = byteIndex + 4;
            end
        end
        
        function did = Init(self, deviceInfo)
            % takes a deviceInfo struct and returns a did, a device ID used
            % by (almost) all the subequent methods to talk to a device.
            deviceStruct = struct(...
                'type', int32(deviceInfo.type), ...
                'serial_number', uint8(zeros(1, 16)), ...
                'description', uint8(zeros(1,64)), ...
                'id', uint32(deviceInfo.id));
            n = length(deviceInfo.serialNumber);
            deviceStruct.serial_number(1:n) = deviceInfo.serialNumber;
            n = length(deviceInfo.description);
            deviceStruct.description(1:n) = deviceInfo.description;
            
            handle = libpointer('voidPtr', 0);
            status = calllib(self.libraryName, 'LccInitController', handle, deviceStruct);
            if status ~= 0
                error('LtcControllerComm:LtcControllerComm', ...
                    'Error creating device');
            end
            did = self.nextIndex;
            self.handles{did} = handle;
            self.nextIndex = self.nextIndex + 1;
        end
        
        function did = Cleanup(self, did)
            % cleanup method closes the device and deletes the underlying
            % native pointer. This can be called manually if you are not 
            % going to use the device anymore and you want it to be
            % available to the system. This is called automatically
            % for all open devices whenever the LtcControllerComm goes away.
           self.CallWithStatus(did, 'LccCleanup');
           self.handles{did}.value = 0;
           did = 0;
        end
        
        function string = EepromReadString(self, did, nChars)
            % Receive string at an address over bit-banged I2C via FPGA reg
            % Address must be a 7-bit address, it will be left-shifted
            % internally.
            string = self.Call(did, 'LccEepromReadString', blanks(nChars), nChars);
        end
        
        function description = GetDescription(self, did)
            % Return the current device's serial number.
            description = self.Call(did, 'LccGetDescription', blanks(64), ...
                64);
        end
        
        function serialNumber = GetSerialNumber(self, did)
            % Return the current device's description.
            serialNumber = self.Call(did, 'LccGetSerialNumber', ...
                blanks(16), 16);
        end
        
        function SetTimeouts(self, did, readTimeout, writeTimeout)
            % Set read and write time-outs.
            self.Call(did, 'LccSetTimeouts', int32(readTimeout), ...
                int32(writeTimeout));
        end
           
        function Reset(self, did)
            % Reset the device, only works for DC1371A, DC890 and DC718
            self.CallWithStatus(did, 'LccReset');
        end
        
        function Close(self, did)
            % Close the device, but keep the handle, device will be
            % automatically re-opened if needed.
            self.CallWithStatus(did, 'LccClose');
        end
        
        function DataSetHighByteFirst(self, did)
            % Make calls to fifo_send/receive_uint16/32_values send/receive
            % high byte first.
            self.Call(did, 'LccDataSetHighByteFirst');
        end
        
        function DataSetLowByteFirst(self, did)
            % Make calls to fifo_send/receive_uint16/32_values send/receive
            % low byte first.
            self.Call(did, 'LccDataSetLowByteFirst');
        end
        
        function nSent = DataSendBytes(self, did, values)
            % Send values as bytes via FIFO
            nSent = 0;
            [~, nSent] = self.Call(did, 'LccDataSendBytes', ...
                values, length(values), nSent);
        end
        
        function nSent = DataSendUint16Values(self, did, values)
            % Send values as uint16 values via FIFO
            nSent = 0;
            [~, nSent] = self.Call(did, 'LccDataSendUint16Values', values, ...
                length(values), nSent);
        end
        
        function nSent = DataSendUint32Values(self, did, values)
            % send values as uint32 values via FIFO
            nSent = 0;
            [~, nSent] = self.Call(did, 'LccDataSendUint32Values', values, ...
                length(values), nSent);
        end
        
        function values = DataReceiveBytes(self, did, nValues)
            % read nValues bytes via FIFO and return as values
            values = uint8(zeros(nValues, 1));
            nBytes = 0;
            [values, nBytes] = self.Call(did, 'LccDataReceiveBytes', values, ...
                nValues, nBytes);
            values = values(1:nBytes, 1);
        end
        
        function [values, nBytes] = DataReceiveUint16Values(self, did, nValues)
            % read nValues uint16 values via FIFO and return as values
            values = uint16(zeros(nValues, 1));
            nBytes = 0;
            [values, nBytes] = self.Call(did, 'LccDataReceiveUint16Values', ...
                values, nValues, nBytes);
            values = values(1:ceil(nBytes/2), 1);
        end
        
        function [values, nBytes] = DataReceiveUint32Values(self, did, nValues)
            % read nValues uint32 values via FIFO and return as values
            values = uint32(zeros(nValues, 1));
            nBytes = 0;
            [values, nBytes] = self.Call(did, 'LccDataReceiveUint32Values', ...
                values, nValues, nBytes);
            values = values(1:ceil(nBytes/4), 1);
        end
        
        
        
        % FIX THESE %
        
        function DataCancelSend(self, did)
            % todo
            self.Call(did, 'LccDataCancelSend');
        end
        
        function DataCancelReceive(self, did)
            % todo
            self.Call(did, 'LccDataCancelReceive');
        end
       
        function DataStartCollect(self, did, total_bytes, trigger)
            % todo
            self.Call(did, 'LccDataStartCollect', int(total_bytes),...
                int(trigger));
        end
        
        function IsDone = DataIsCollectDone(self, did)
            % todo
            checkIsDone = false;
            IsDone = self.Call(did, 'LccDataIsCollectDone', checkIsDone);
        end
        
        function DataCancelCollect(self, did)
            % todo
            self.Call(did, 'LccDataCancelCollect');
        end
        
        function DataSetCharacteristics(self, did, is_multichannel,...
                is_wide_samples, is_positive_clock)
            % todo
            self.Call(did, 'LccDataSetCharacteristics', is_multichannel,...
                is_wide_samples, is_positive_clock);
        end
        % TODO %
        
%     // Since the send calls block, they must be started in a separate thread to be cancelled
%     // This is the only instance where calling functions from this library from separate threads
%     // is safe.
%     LTC_CONTROLLER_COMM_API int LccDataCancelSend(LccHandle handle);
% 
%     // Since the receive calls block, they must be started in a separate thread to be cancelled
%     // This is the only instance where calling functions from this library from separate threads
%     // is safe.
%     LTC_CONTROLLER_COMM_API int LccDataCancelReceive(LccHandle handle);
% 
%     // ADC collection functions for DC1371, DC890, DC718
%     LTC_CONTROLLER_COMM_API int LccDataStartCollect(LccHandle handle, int total_bytes, int trigger);
% 
%     LTC_CONTROLLER_COMM_API int LccDataIsCollectDone(LccHandle handle, bool* is_done);
%     
%     LTC_CONTROLLER_COMM_API int LccDataCancelCollect(LccHandle handle);
% 
%     // ADC collection characteristics for DC718 and DC890
%     LTC_CONTROLLER_COMM_API int LccDataSetCharacteristics(LccHandle handle, bool is_multichannel,
%         bool is_wide_samples, bool is_positive_clock);
        
        function SpiSendBytes(self, did, values)
            % Send values via SPI controlling chip select.
            self.Call(did, 'LccSpiSendBytes', values, length(values));
        end
        
        function values = SpiReceiveBytes(self, did, nValues)
            % Receive nValues bytes via SPI controlling chip select.
            values = uint8(zeros(nValues, 1));
            values = self.Call(did, 'LccSpiReceiveBytes', values, nValues);
        end
        
        function receiveValues = SpiTransceiveBytes(self, did, sendValues)
            % Transceive sendValues via SPI controlling chip select.
            nValues = length(sendValues);
            receiveValues = uint8(zeros(nValues, 1));
            [~, receiveValues] = self.Call(did, 'LccSpiTransceiveBytes', ...
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
            self.Call(did, 'LccSpiSendByteAtAddress', address, value);
        end
        
        function SpiSendBytesAtAddress(self, did, address, values)
            % Write an address byte and values via SPI.
            % Many SPI devices adopt a convention similar to I2C addressing
            % where a byte is sent indicating which register address the 
            % rest of the data pertains to. Often there is a read-write bit
            % in the address, this function will not shift or set any bits 
            % in the address, it basically just writes the address byte and
            % data bytes one after the other.
            self.Call(did, 'LccSpiSendBytesAtAddress', address, ...
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
            value = self.Call(did, 'LccSpiReceiveByteAtAddress', address, ...
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
            values = self.Call(did, 'LccSpiReceiveBytesAtAddress', address, ...
                values, nValues);
        end
        
        function SpiSetCsState(self, did, chipSelectState)
            % Set the SPI chip-select high or low.
            if chipSelectState == self.SPI_CS_STATE_HIGH
                state = 1;
            elseif chipSelectState == self.SPI_CS_STATE__LOW
                state = 0;
            else
                error('LtcControllerComm:spiSetCsState', ...
                    ['chipSelectState must be SPI_CS_STATE_HIGH or ', ...
                    'SPI_CS_STATE__LOW']);
            end
            self.Call(did, 'LccSpiSetCsState', state);
        end
        
        function SpiSendNoChipSelect(self, did, values)
            % Send values via SPI without controlling chip-select.
            self.Call(did, 'LccSpiSendNoChipSelect', values, length(values));
        end
        
        function values = SpiReceiveNoChipSelect(self, did, nValues)
            % Receive nValues bytes via SPI without controlling SPI
            values = uint8(zeros(nValues, 1));
            values = self.Call(did, 'LccSpiReceiveNoChipSelect', ...
                values, nValues);
        end
        
        function receiveValues = SpiTransceiveNoChipSelect(self, did, ...
                sendValues)
            % Transceive sendValues bytes via SPI without controlling SPI
            nValues = length(sendValues);
            values = uint8(zeros(nValues, 1));
            [~, receiveValues] = self.Call(did, ...
                'LccSpiTransceiveNoChipSelect', sendValues, ...
                values, nValues);
        end
        
        
        
        function HsSetBitMode(self, did, bitMode)
            % Set the device to MPSSE mode (for SPI, FPGA registers and
            % GPIO) or FIFO mode (for fast FIFO communication)
            if bitMode == self.HS_BIT_MODE_FIFO
                mode = 64;
            elseif bitMode == self.HS_BIT_MODE_MPSSE
                mode = 2;
            else
                error('LtcControllerComm:setBitMode', ...
                    'bitMode must be HS_BIT_MODE_MPSSE or HS_BIT_MODE_FIFO');
            end
            self.Call(did, 'LccHsSetBitMode', mode);
        end
        
        function HsPurgeIo(self, did)
            % Clear all data in the USB I/O buffers.
            self.Call(did, 'LccHsPurgeIo');
        end
        
        function HsFpgaToggleReset(self, did)
            % Set the FPGA reset bit low then high.
            self.Call(did, 'LccHsFpgaToggleReset');
        end
        
        function HsFpgaWriteAddress(self, did, address)
            % Set the FPGA address to write or read.
            self.Call(did, 'LccHsFpgaWriteAddress', address);
        end
        
        function HsFpgaWriteData(self, did, data)
            % Write a value to the current FPGA address.
            self.Call(did, 'LccHsFpgaWriteData', data);
        end
        
        function data = HsFpgaReadData(self, did)
            % Read a value from the current FPGA address and return it.
            data = 0;
            data = self.Call(did, 'LccHsFpgaReadData', data);
        end
        
        function HsFpgaWriteDataAtAddress(self, did, address, data)
            % Set the current address and write a value to it.
            self.Call(did, 'LccHsFpgaWriteDataAtAddress', address, data);
        end
        
        function data = HsFpgaReadDataAtAddress(self, did, address)
            % Set the current address and read a value from it.
            data = 0;
            data = self.Call(did, 'LccHsFpgaReadDataAtAddress', address, ...
                data);
        end
        
        function HsGpioWriteHighByte(self, did, value)
            % Set the GPIO high byte to a value.
            self.Call(did, 'LccHsGpioWriteHighByte', value);
        end
        
        function value = HsGpioReadHighByte(self, did)
            % Read the GPIO high byte and return the value.
            value = 0;
            value = self.Call(did, 'LccHsGpioReadHighByte', value);
        end
        
        function HsGpioWriteLowByte(self, did, value)
            % Set the GPIO low byte to a value.
            self.Call(did, 'LccHsGpioWriteLowByte', value);
        end
        
        function value = HsGpioReadLowByte(self, did)
            % Read the GPIO low byte and return the value
            value = 0;
            value = self.Call(did, 'LccHsGpioReadLowByte', value);
        end
        
        function HsFpgaEepromSetBitBangRegister(self, did, registerAddress)
            % Set the FPGA register used to do bit-banged I2C.
            % If not called, address used is 0x11.
            self.Call(did, 'LccHsFpgaEepromSetBitBangRegister', registerAddress);
        end
      
        % TODO %
        
        function DC1371SetGenericConfig(self, did, generic_config)
            % todo
            self.Call(did, 'Lcc1371SetGenericConfig', generic_config);
        end
        
        function DC1371SetDemoConfig(self, did, demo_config)
            % todo
            self.Call(did, 'Lcc1371SetDemoConfig', demo_config);
        end
        
        function DC890GpioSetByte(self, did, byte)
            % todo
            self.Call(did, 'Lcc890GpioSetByte', byte);
        end
        
        function DC890GpioSpiSetBits(self, did, cs_bit, sck_bit, sdi_bit)
            % todo
            self.Call(did, 'Lcc890GpioSpiSetBits', cs_bit, sck_bit, sdi_bit);
        end
        
        function DC890Flush(self, did)
            % todo
            self.Call(did, 'Lcc890Flush');
        end
            
%     LTC_CONTROLLER_COMM_API int Lcc1371SetGenericConfig(LccHandle handle, uint32_t generic_config);
% 
%     LTC_CONTROLLER_COMM_API int Lcc1371SetDemoConfig(LccHandle handle, uint32_t demo_config);
% 
%     // Set the chip select used to be LCC_1371_CHIP_SELECT_ONE or LCC_1371_CHIP_SELECT_TWO
%     // ONE is the most common value and is used if this function is never called.
%     LTC_CONTROLLER_COMM_API int Lcc1371SpiChooseChipSelect(LccHandle handle, int new_chip_select);
% 
%     /////////////////////////
%     // Functions for DC890 //
%     /////////////////////////
% 
%     // These functions control the I2C I/O expander present on some DC890 compatible demo0boards
%     // They are used to set certain lines, and the SPI functions use them under the hood to do
%     // bit-banged SPI. (The DC890 doesn't have a SPI interface.)
% 
%     LTC_CONTROLLER_COMM_API int Lcc890GpioSetByte(LccHandle handle, uint8_t byte);
% 
%     LTC_CONTROLLER_COMM_API int Lcc890GpioSpiSetBits(LccHandle handle, int cs_bit, 
%         int sck_bit, int sdi_bit);
% 
%     // Flush commands and clear IO buffers
%     LTC_CONTROLLER_COMM_API int Lcc890Flush(LccHandle handle);
        
    end
end

