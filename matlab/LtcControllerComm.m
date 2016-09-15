classdef LtcControllerComm < handle
% LtcControllerComm Wrapper for LtcControllerComm.dll
% It provides a class and some constants used to communicate with 
% the DC1371A, DC718C, DC890B, and high-speed commerical FPGA demo-boards
% used as controllers for Linear Technology demo-boards. Note that there is
% no open command, the controller is opened automatically as needed. There 
% is a close method, but it is not necessary to call it, the destructor will
%  close the handle. If there is an error or the close method is called, the 
% device will again be opened automatically as needed.
% To connect do something like this:
%
%     lcc = LtcControllerComm();
%     
%     % ListControllers finds all connected controllers of the specified
%     % type(s)
%     controllerInfoList = lcc.ListControllers( ...
%         bitor(lcc.TYPE_DC718, lcc.TYPE_DC890));
%     controllerInfo = [];
%     for info = controllerInfoList
%        % here you could use cid = lcc.Init(controllerInfo); to open each
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
%     cid = lcc.Init(controllerInfo);

    properties (Constant)
        HS_BIT_MODE_MPSSE = 0 % argument to set_mode for non-FIFO mode.
        HS_BIT_MODE_FIFO = 1  % argument to set_mode for fast FIFO mode.
        
        TYPE_NONE = uint32(0)
        TYPE_DC1371 = uint32(1)
        TYPE_DC718 = uint32(2)
        TYPE_DC890 = uint32(4)
        TYPE_HIGH_SPEED = uint32(8)
        TYPE_UNKNOWN = uint32(4294967295)
        
        SPI_CS_STATE_LOW = 0
        SPI_CS_STATE_HIGH = 1
               
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
        function ErrorOnBadStatus(self, cid, status)
            if status ~= 0
                errorIds = {'OK', 'HardwareError', 'InvalidArgument', 'LogicError', ...
                    'NotSupported', 'UserAborted', 'UnknownError'};
                errorId = errorIds{1-status};
                message = repmat(' ', 1, 256);
                [~, ~, message] = calllib(self.libraryName, ...
                    'LccGetErrorInfo', self.handles{cid}, message, 256);
                error(['LtcControllerComm:', errorId],  message);
            end
        end
        
        function varargout = CallWithStatus(self, cid, func, varargin)
            handle = self.handles{cid};
            if handle.value == 0
                error('LtcControllerComm:InvalidArgument', 'Device has already been cleaned up');
            end
            [varargout{1:nargout}] = calllib(self.libraryName, func, handle, varargin{:});
        end
        
        function varargout = Call(self, cid, func, varargin)
            [status, ~, varargout{1:nargout}] = ...
                self.CallWithStatus(cid, func, varargin{:});
            self.ErrorOnBadStatus(cid, status);
        end
    end
    
    methods    
        function self = LtcControllerComm
            % the lcc object keeps track of all controllers and the DLL library
            % when it goes out of scope it Cleanup's all connections and unloads the
            % library
            
            archStr = computer;
            location = winqueryreg('HKEY_LOCAL_MACHINE', ...
                'SOFTWARE\\Linear Technology\\LinearLabTools', 'Location');
            if strcmp(archStr((end-1):end), '64')
                self.libraryName = 'ltc_controller_comm64';
            else
                self.libraryName = 'ltc_controller_comm';
            end
            
            loadlibrary([location, self.libraryName, '.dll'], 'ltc_controller_comm_matlab.h');
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
        
        function deviceList = ListControllers(self, type)
            % returns an array of 1 structure per connected controller of
            % the specified type(s) type can be a bitwise OR combination
            % of TYPE_* values.
            % The structure has a description field and a serial
            % number field that can be used to determine if this is a
            % desired controller. Pass the structure corresponding to the 
            % desired controller into Init to open the device and get a cid.
            nControllers = uint32(0);
            [status, nDevices] = calllib(self.libraryName, ...
                'LccGetNumControllers', type, 100, nControllers);
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
        
        function cid = Init(self, controllerInfo)           
            controllerStruct = uint8(zeros(1, 88));
            controllerStruct(1:4) = typecast(controllerInfo.type, 'uint8');
            n = length(controllerInfo.description);
            controllerStruct((1:n)+4) = controllerInfo.description;
            n = length(controllerInfo.serialNumber);
            controllerStruct((1:n)+68) = controllerInfo.serialNumber;
            controllerStruct((1:4)+84) = typecast(controllerInfo.id, 'uint8');

            handle = libpointer('voidPtr', 0);
            status = calllib(self.libraryName, 'LccInitController', handle, controllerStruct);
            if status ~= 0
                error('LtcControllerComm:LtcControllerComm', ...
                    'Error creating device');
            end
            cid = self.nextIndex;
            self.handles{cid} = handle;
            self.nextIndex = self.nextIndex + 1;
        end
        
        function cid = Cleanup(self, cid)
            % cleanup method closes the device and deletes the underlying
            % native pointer. This can be called manually if you are not 
            % going to use the device anymore and you want it to be
            % available to the system. This is called automatically
            % for all open devices whenever the LtcControllerComm goes away.
           self.CallWithStatus(cid, 'LccCleanup');
           self.handles{cid}.value = 0;
           cid = 0;
        end
        
        function serialNumber = GetSerialNumber(self, cid)
            % Return the current device's description.
            serialNumber = self.Call(cid, 'LccGetSerialNumber', ...
                blanks(16), 16);
        end
        
        function description = GetDescription(self, cid)
            % Return the current device's serial number.
            description = self.Call(cid, 'LccGetDescription', blanks(64), 64);
        end
           
        function Reset(self, cid)
            % Reset the device, only works for DC1371A, DC890 and DC718
            self.CallWithStatus(cid, 'LccReset');
        end
        
        function Close(self, cid)
            % Close the device, but keep the handle, device will be
            % automatically re-opened if needed.
            self.CallWithStatus(cid, 'LccClose');
        end
        
        function DataSetHighByteFirst(self, cid)
            % Make calls to fifo_send/receive_uint16/32_values send/receive
            % high byte first.
            self.Call(cid, 'LccDataSetHighByteFirst');
        end
        
        function DataSetLowByteFirst(self, cid)
            % Make calls to fifo_send/receive_uint16/32_values send/receive
            % low byte first.
            self.Call(cid, 'LccDataSetLowByteFirst');
        end
        
        function nSent = DataSendBytes(self, cid, values)
            % Send values as bytes via FIFO .
            % Only used with high_speed controllers.
            nSent = 0;
            [~, nSent] = self.Call(cid, 'LccDataSendBytes', ...
                values, length(values), nSent);
        end
        
        function nSent = DataSendUint16Values(self, cid, values)
            % Send values as uint16 values via FIFO. 
            % Only used with high_speed controllers.
            nSent = 0;
            [~, nSent] = self.Call(cid, 'LccDataSendUint16Values', values, ...
                length(values), nSent);
        end
        
        function nSent = DataSendUint32Values(self, cid, values)
            % Send values as uint32 values via FIFO.
            % Only used with high_speed controllers.
            nSent = 0;
            [~, nSent] = self.Call(cid, 'LccDataSendUint32Values', values, ...
                length(values), nSent);
        end
        
        function values = DataReceiveBytes(self, cid, nValues)
            % read nValues bytes via FIFO and return as values
            values = uint8(zeros(nValues, 1));
            nBytes = 0;
            [values, nBytes] = self.Call(cid, 'LccDataReceiveBytes', values, ...
                nValues, nBytes);
            values = values(1:nBytes, 1);
        end
        
        function [values, nBytes] = DataReceiveUint16Values(self, cid, nValues)
            % read nValues uint16 values via FIFO and return as values
            values = uint16(zeros(nValues, 1));
            nBytes = 0;
            [values, nBytes] = self.Call(cid, 'LccDataReceiveUint16Values', ...
                values, nValues, nBytes);
            values = values(1:ceil(nBytes/2), 1);
        end
        
        function [values, nBytes] = DataReceiveUint32Values(self, cid, nValues)
            % read nValues uint32 values via FIFO and return as values
            values = uint32(zeros(nValues, 1));
            nBytes = 0;
            [values, nBytes] = self.Call(cid, 'LccDataReceiveUint32Values', ...
                values, nValues, nBytes);
            values = values(1:ceil(nBytes/4), 1);
        end
      
        function DataStartCollect(self, cid, totalSamples, trigger)
            % Start an ADC collect into memory, works with DC1371, DC890, DC718.
            % totalSamples -- Number of samples to collect
            % trigger -- Trigger type
            self.Call(cid, 'LccDataStartCollect', totalSamples, trigger);
        end
        
        function isDone = DataIsCollectDone(self, cid)
            % Check if an ADC collect is done, works with DC1371, DC890, DC718
            refIsDone = false;
            isDone = self.Call(cid, 'LccDataIsCollectDone', refIsDone);
        end
        
        function DataCancelCollect(self, cid)
            % Cancel any ADC collect, works with DC1371, DC890, DC718
            % Note this function must be called to cancel a pending collect
            % OR if a collect has finished but you do not read the full 
            % collection of data.
            self.Call(cid, 'LccDataCancelCollect');
        end
        
        function DataSetCharacteristics(self, cid, isMultichannel,...
                sampleBytes, isPositiveClock)
            % ADC collection characteristics for DC718 and DC890
            % isMultichannel -- True if the ADC has 2 or more channels
            % sampleBytes -- The total number of bytes occupied by a sample
            %     including alignment and meta data (if applicable)
            % isPositiveClock -- True if data is sampled on positive
            %     (rising) clock edges
            self.Call(cid, 'LccDataSetCharacteristics', isMultichannel,...
                sampleBytes, isPositiveClock);
        end
        
        function SpiSendBytes(self, cid, values)
            % Send values via SPI controlling chip select.
            % Not used with DC718. Will cause a bunch of ineffective I2C
            % traffic on a DC890 if the demo-board does not have an I/O expander.
            self.Call(cid, 'LccSpiSendBytes', values, length(values));
        end
        
        function values = SpiReceiveBytes(self, cid, nValues)
            % Receive nValues bytes via SPI controlling chip select.
            % Not used with DC718 or DC890.
            values = uint8(zeros(nValues, 1));
            values = self.Call(cid, 'LccSpiReceiveBytes', values, nValues);
        end
        
        function receiveValues = SpiTransceiveBytes(self, cid, sendValues)
            % Transceive sendValues via SPI controlling chip select.
            % Not used with DC718 or DC890.
            nValues = length(sendValues);
            receiveValues = uint8(zeros(nValues, 1));
            [~, receiveValues] = self.Call(cid, 'LccSpiTransceiveBytes', ...
                sendValues, receiveValues, nValues);
        end
        
        function SpiSendByteAtAddress(self, cid, address, value)
            % Write an address and a value via SPI.
            %
            % Not used with DC718. Will cause a bunch of ineffective I2C
            % traffic on a DC890 if the demo-board does not have an I/O expander.
            %
            % Many SPI devices adopt a convention similar to I2C addressing
            % where a byte is sent indicating which register address the
            % rest of the data pertains to. Often there is a read-write bit
            % in the address, this function will not shift or set any bits 
            % in the address, it basically just writes two bytes, (the 
            % address byte and data byte) one after the other.
            self.Call(cid, 'LccSpiSendByteAtAddress', address, value);
        end
        
        function SpiSendBytesAtAddress(self, cid, address, values)
            % Write an address byte and values via SPI.
            %
            % Not used with DC718. Will cause a bunch of ineffective I2C
            % traffic on a DC890 if the demo-board does not have an I/O expander.
            %
            % Many SPI devices adopt a convention similar to I2C addressing
            % where a byte is sent indicating which register address the 
            % rest of the data pertains to. Often there is a read-write bit
            % in the address, this function will not shift or set any bits 
            % in the address, it basically just writes the address byte and
            % data bytes one after the other.
            self.Call(cid, 'LccSpiSendBytesAtAddress', address, ...
                values, length(values));
        end
        
        function value = SpiReceiveByteAtAddress(self, cid, address)
            % Write an address and receive a value via SPI; return the Value.
            %
            % Not used with DC718 or DC890.
            %
            % Many SPI devices adopt a convention similar to I2C 
            % addressing, where a byte is sent indicating which register 
            % address the rest of the data pertains to. Often there is a 
            % read-write bit in the address, this function will not shift 
            % or set any bits in the address, it basically just writes the
            % address byte and then reads one data byte.
            value = 0;
            value = self.Call(cid, 'LccSpiReceiveByteAtAddress', address, ...
                value);
        end
        
        function values = SpiReceiveBytesAtAddress(self, cid, address, ...
                nValues)
            % Receive nValues bytes via SPI at an address.
            %
            % Not used with DC718 or DC890.
            %
            % Many SPI devices adopt a convention similar to I2C addressing
            % where a byte is sent indicating which register address the 
            % rest of the data pertains to. Often there is a read-write bit
            % in the address, this function will not shift or set any bits 
            % in the address, it basically just writes the address byte and
            % then reads several data bytes. 
            values = uint8(zeros(nValues, 1));
            values = self.Call(cid, 'LccSpiReceiveBytesAtAddress', address, ...
                values, nValues);
        end
        
        function SpiSetCsState(self, cid, chipSelectState)
            % Set the SPI chip-select high or low.
            % Not used with DC718. Will cause a bunch of ineffective I2C
            % traffic on a DC890 if the demo-board does not have an I/O expander.
            if chipSelectState == self.SPI_CS_STATE_HIGH
                state = 1;
            elseif chipSelectState == self.SPI_CS_STATE__LOW
                state = 0;
            else
                error('LtcControllerComm:spiSetCsState', ...
                    ['chipSelectState must be SPI_CS_STATE_HIGH or ', ...
                    'SPI_CS_STATE__LOW']);
            end
            self.Call(cid, 'LccSpiSetCsState', state);
        end
        
        function SpiSendNoChipSelect(self, cid, values)
            % Send values via SPI without controlling chip-select.
            % Not used with DC718. Will cause a bunch of ineffective I2C
            % traffic on a DC890 if the demo-board does not have an I/O expander.
            self.Call(cid, 'LccSpiSendNoChipSelect', values, length(values));
        end
        
        function values = SpiReceiveNoChipSelect(self, cid, nValues)
            % Receive nValues bytes via SPI without controlling SPI
            % Not used with DC718 or DC890.
            values = uint8(zeros(nValues, 1));
            values = self.Call(cid, 'LccSpiReceiveNoChipSelect', ...
                values, nValues);
        end
        
        function receiveValues = SpiTransceiveNoChipSelect(self, cid, ...
                sendValues)
            % Transceive sendValues bytes via SPI without controlling SPI
            % Not used with DC718 or DC890.
            nValues = length(sendValues);
            values = uint8(zeros(nValues, 1));
            [~, receiveValues] = self.Call(cid, ...
                'LccSpiTransceiveNoChipSelect', sendValues, ...
                values, nValues);
        end
        
        function is_loaded = FpgaGetIsLoaded(self, cid, fpgaFilename)
            % Check if a particular FPGA load is loaded.
            % Not used with high_speed controllers or DC718
            % fpgaFilename -- The base file name without any folder, extension
            % or revision info, for instance 'DLVDS' or 'S2175', case insensitive.
            refIsLoaded = false;
            is_loaded = self.Call(cid, 'LccFpgaGetIsLoaded', fpgaFilename, refIsLoaded);
        end
        
        function FpgaLoadFile(self, cid, fpga_filename)
            % Loads an FPGA file
            % Not used with high_speed controllers or DC718
            % fpgaFilename -- The base file name without any folder, extension
            % or revision info, for instance 'DLVDS' or 'S2175', case insensitive.
            self.Call(cid, 'LccFpgaLoadFile', fpga_filename);
        end
        
        function progress = FpgaLoadFileChunked(self, cid, fpgaFilename)
            % Load a particular FPGA file a chunk at a time. 
            % Not used with high_speed controllers or DC718
            % fpga_filename -- The base file name without any folder, extension
            % or revision info, for instance 'DLVDS' or 'S2175', case insensitive.
            % The first call returns a number, each subsequent call will return a
            % SMALLER number. The process is finished when it returns 0.
            refProgress = 0;
            progress = self.Call(cid, 'LccFpgaLoadFileChunked', fpgaFilename, refProgress);
        end
        
        function FpgaCancelLoad(self, cid)
            % Must be called if you abandon loading the FPGA file before complete
            % Not used with high_speed controllers or DC718
            self.Call(cid, 'LccFpgaCancelLoad');
        end
        
        function string = EepromReadString(self, cid, nChars)
            % Receive an EEPROM string.
            string = self.Call(cid, 'LccEepromReadString', blanks(nChars), nChars);
        end
        
        % The following functions apply ONLY to HighSpeed type controllers
        
        function HsSetBitMode(self, cid, bitMode)
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
            self.Call(cid, 'LccHsSetBitMode', mode);
        end
        
        function HsPurgeIo(self, cid)
            % Clear all data in the USB I/O buffers.
            self.Call(cid, 'LccHsPurgeIo');
        end
        
        function HsFpgaToggleReset(self, cid)
            % Set the FPGA reset bit low then high.
            self.Call(cid, 'LccHsFpgaToggleReset');
        end
        
        function HsFpgaWriteAddress(self, cid, address)
            % Set the FPGA address to write or read.
            self.Call(cid, 'LccHsFpgaWriteAddress', address);
        end
        
        function HsFpgaWriteData(self, cid, data)
            % Write a value to the current FPGA address.
            self.Call(cid, 'LccHsFpgaWriteData', data);
        end
        
        function data = HsFpgaReadData(self, cid)
            % Read a value from the current FPGA address and return it.
            data = 0;
            data = self.Call(cid, 'LccHsFpgaReadData', data);
        end
        
        function HsFpgaWriteDataAtAddress(self, cid, address, data)
            % Set the current address and write a value to it.
            self.Call(cid, 'LccHsFpgaWriteDataAtAddress', address, data);
        end
        
        function data = HsFpgaReadDataAtAddress(self, cid, address)
            % Set the current address and read a value from it.
            data = 0;
            data = self.Call(cid, 'LccHsFpgaReadDataAtAddress', address, ...
                data);
        end
        
        function HsGpioWriteHighByte(self, cid, value)
            % Set the GPIO high byte to a value.
            self.Call(cid, 'LccHsGpioWriteHighByte', value);
        end
        
        function value = HsGpioReadHighByte(self, cid)
            % Read the GPIO high byte and return the value.
            value = 0;
            value = self.Call(cid, 'LccHsGpioReadHighByte', value);
        end
        
        function HsGpioWriteLowByte(self, cid, value)
            % Set the GPIO low byte to a value.
            self.Call(cid, 'LccHsGpioWriteLowByte', value);
        end
        
        function value = HsGpioReadLowByte(self, cid)
            % Read the GPIO low byte and return the value
            value = 0;
            value = self.Call(cid, 'LccHsGpioReadLowByte', value);
        end
        
        function HsFpgaEepromSetBitBangRegister(self, cid, registerAddress)
            % Set the FPGA register used to do bit-banged I2C.
            % If not called, address used is 0x11.
            self.Call(cid, 'LccHsFpgaEepromSetBitBangRegister', registerAddress);
        end
             
        % The following functions apply ONLY to DC1371 controllers
             
        function DC1371SetGenericConfig(self, cid, genericConfig)
            % genericConfig is always 0, so you never have to call this function
            genericConfig = hex2dec(genericConfig);
            self.Call(cid, 'Lcc1371SetGenericConfig', genericConfig);
        end
        
        function DC1371SetDemoConfig(self, cid, demoConfig)
            % Set the value corresponding to the four pairs of hex digits at the end
            % of line three of the EEPROM string for a DC1371A demo-board.
            % demoConfig -- If an ID string were to have 01 02 03 04,
            %     demoConfig would be '01020304' (a string)
            demoConfig = hex2dec(demoConfig);
            self.Call(cid, 'Lcc1371SetDemoConfig', demoConfig);
        end
        
        function DC1371SpiChooseChipSelect(self, cid, newChipSelect)
            % Set the chip select to use in future spi commands, 1 (default) is
            % correct for most situations, rarely 2 is needed.
            % newChipSelect -- 1 (usually) or 2
            self.Call(cid, 'Lcc1371SpiChooseChipSelect', newChipSelect);
        end
        
        % The following functions apply ONLY to DC890 controllers
        
        function DC890GpioSetByte(self, cid, byte)
            % Set the IO expander GPIO lines to byte, all spi transaction use this as
            % a base value, or can be used to bit bang lines
            % byte -- The bits of byte correspond to the output lines of the IO expander.
            self.Call(cid, 'Lcc890GpioSetByte', byte);
        end
        
        function DC890GpioSpiSetBits(self, cid, csBit, sckBit, sdiBit)
            % Set the bits used for SPI transactions, which are performed by
            % bit-banging the IO expander on demo-boards that have one. This function
            % must be called before doing any spi transactions with the DC890
            % 
            % csBit -- the bit used as chip select
            % sckBit -- the bit used as sck
            % sdiBit -- the bit used as sdi
            self.Call(cid, 'Lcc890GpioSpiSetBits', csBit, sckBit, sdiBit);
        end
        
        function DC890Flush(self, cid)
            % Causes the DC890 to terminate any I2C (or GPIO or SPI) transactions then
            % purges the buffers.
            self.Call(cid, 'Lcc890Flush');
        end
    end
end

