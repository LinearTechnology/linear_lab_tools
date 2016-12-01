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
    %     % list_controllers finds all connected controllers of the specified
    %     % type(s)
    %     controller_info_list = lcc.list_controllers( ...
    %         bitor(lcc.TYPE_DC718, lcc.TYPE_DC890));
    %     controller_info = [];
    %     for info = controller_info_list
    %        % here you could use cid = lcc.init(controller_info); to open each
    %        % device and query it to make sure it is the controller, or you could
    %        % check info.description or info.serialNumber, or even just take
    %        % the first controller, depending on your needs. If you open multiple
    %        % devices you aren't going to use, you should Cleanup them, or 
    %        % they will be unavailable until the Lcc object goes out of scope
    %        if this_is_the_one_we_want
    %            controller_info = info;
    %            break;
    %        end
    %     end
    % 
    %     if isempty(controler_isnfo)
    %         error('TestLtcControllerComm:noDevice', ...
    %            'could not find compatible device');
    %     end
    % 
    %     % init a device and get an id
    %     cid = lcc.init(controller_info);

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
        
        DC718_EEPROM_SIZE = 50
        DC890_EEPROM_SIZE = 50
        DC1371_EEPROM_SIZE = 400
    end
    
    properties (Access = private)
        handles;        
        next_index;
        library_name;
    end
       
    methods (Access = private)
        function error_on_bad_status(self, cid, status)
            if status ~= 0
                error_ids = {'OK', 'HardwareError', 'InvalidArgument', 'LogicError', ...
                    'NotSupported', 'UserAborted', 'UnknownError'};
                error_id = error_ids{1-status};
                message = repmat(' ', 1, 256);
                [~, ~, message] = calllib(self.library_name, ...
                    'LccGetErrorInfo', self.handles{cid}, message, 256);
                error(['LtcControllerComm:', error_id],  message);
            end
        end
        
        function varargout = call_with_status(self, cid, func, varargin)
            handle = self.handles{cid};
            if handle.value == 0
                error('LtcControllerComm:InvalidArgument', 'Device has already been cleaned up');
            end
            [varargout{1:nargout}] = calllib(self.library_name, func, handle, varargin{:});
        end
        
        function varargout = call(self, cid, func, varargin)
            [status, ~, varargout{1:nargout}] = ...
                self.call_with_status(cid, func, varargin{:});
            self.error_on_bad_status(cid, status);
        end
    end
    
    methods    
        function self = LtcControllerComm
            % the lcc object keeps track of all controllers and the DLL library
            % when it goes out of scope it Cleanup's all connections and unloads the
            % library
            
            arch_str = computer;
            location = winqueryreg('HKEY_LOCAL_MACHINE', ...
                'SOFTWARE\\Linear Technology\\LinearLabTools', 'Location');
            if strcmp(arch_str((end-1):end), '64')
                self.library_name = 'ltc_controller_comm64';
            else
                self.library_name = 'ltc_controller_comm';
            end
            
            this_folder = fileparts(mfilename('fullpath'));
            
            loadlibrary([location, self.library_name, '.dll'], ...
                fullfile(this_folder, 'ltc_controller_comm_matlab.h'));

            self.handles = {};
            self.next_index = 1;
        end
        
        function delete(self)
            % the destructor automatically cleans up all devices that were
            % opened (Init) and then unloads the native DLL.
            for i = 1:length(self.handles)
                if self.handles{i}.value ~= 0
                    calllib(self.library_name, 'LccCleanup', self.handles{i});
                end
            end
            unloadlibrary(self.library_name);
        end
        
        function device_list = list_controllers(self, type)
            % returns an array of 1 structure per connected controller of
            % the specified type(s) type can be a bitwise OR combination
            % of TYPE_* values.
            % The structure has a description field and a serial
            % number field that can be used to determine if this is a
            % desired controller. Pass the structure corresponding to the 
            % desired controller into Init to open the device and get a cid.
            num_controllers = uint32(0);
            [status, num_controllers] = calllib(self.library_name, ...
                'LccGetNumControllers', type, 100, num_controllers);
            if status ~= 0
                error('LtcControllerComm:ListControllers', 'Error creating controller list');
            end
            
            if num_controllers == 0
                error('LtcControllerComm:ListControllers', 'No controllers found');
            end
            
            controller_struct_bytes = uint8(zeros(1, 88 * num_controllers));
            [status, controller_struct_bytes] = calllib(self.library_name, ...
                'LccGetControllerList', type, controller_struct_bytes, num_controllers);
            
            if status ~= 0
                error('LtcControllerComm:ListControllers', 'Error getting the controller list');
            end
            
            device_list = struct('type', cell(1, num_controllers), ...
                'description', cell(1, num_controllers), ...
                'serial_number', cell(1, num_controllers), ...
                'id', cell(1, num_controllers));
            byte_index = 1;
            for i = 1:num_controllers
                device_list(i).type = typecast(...
                    controller_struct_bytes(byte_index:byte_index+3), 'int32');
                byte_index = byte_index + 4;
                
                description = controller_struct_bytes(byte_index:(byte_index+63));
                description = description(1:(find(description == 0, 1, 'first')-1));
                device_list(i).description = char(description);
                byte_index = byte_index + 64;               
                
                serial_number = controller_struct_bytes(byte_index:(byte_index+15));
                serial_number = serial_number(1:(find(serial_number == 0, 1, 'first')-1));
                device_list(i).serial_number = char(serial_number);
                byte_index = byte_index + 16;
                
                device_list(i).id = typecast(...
                    controller_struct_bytes(byte_index:byte_index+3), 'uint32');
                byte_index = byte_index + 4;
            end
        end
        
        function cid = init(self, controller_info)
            controller_struct = uint8(zeros(1, 88));
            controller_struct(1:4) = typecast(controller_info.type, 'uint8');
            n = length(controller_info.description);
            controller_struct((1:n)+4) = controller_info.description;
            n = length(controller_info.serial_number);
            controller_struct((1:n)+68) = controller_info.serial_number;
            controller_struct((1:4)+84) = typecast(controller_info.id, 'uint8');

            handle = libpointer('voidPtr', 0);
            status = calllib(self.library_name, 'LccInitController', handle, controller_struct);
            if status ~= 0
                error('LtcControllerComm:LtcControllerComm', ...
                    'Error creating device');
            end
            cid = self.next_index;
            self.handles{cid} = handle;
            self.next_index = self.next_index + 1;
        end
        
        function cid = cleanup(self, cid)
            % cleanup method closes the device and deletes the underlying
            % native pointer. This can be called manually if you are not 
            % going to use the device anymore and you want it to be
            % available to the system. This is called automatically
            % for all open devices whenever the LtcControllerComm goes away.
           self.call_with_status(cid, 'LccCleanup');
           self.handles{cid}.value = 0;
           cid = 0;
        end
        
        function serial_number = get_serial_number(self, cid)
            % Return the current device's description.
            serial_number = self.call(cid, 'LccGetSerialNumber', ...
                blanks(16), 16);
        end
        
        function description = get_description(self, cid)
            % Return the current device's serial number.
            description = self.call(cid, 'LccGetDescription', blanks(64), 64);
        end
           
        function reset(self, cid)
            % Reset the device, only works for DC1371A, DC890 and DC718
            self.call_with_status(cid, 'LccReset'); % should this be call?
            % not sure why we are ignoring the status here
        end
        
        function close(self, cid)
            % Close the device, but keep the handle, device will be
            % automatically re-opened if needed.
            self.call_with_status(cid, 'LccClose'); % ignore status because we close on errors
        end
        
        function data_set_high_byte_first(self, cid)
            % Make calls to fifo_send/receive_uint16/32_values send/receive
            % high byte first.
            self.call(cid, 'LccDataSetHighByteFirst');
        end
        
        function data_set_low_byte_first(self, cid)
            % Make calls to fifo_send/receive_uint16/32_values send/receive
            % low byte first.
            self.call(cid, 'LccDataSetLowByteFirst');
        end
        
        function num_sent = data_send_bytes(self, cid, values)
            % Send values as bytes via FIFO .
            % Only used with high_speed controllers.
            num_sent = 0;
            [~, num_sent] = self.call(cid, 'LccDataSendBytes', ...
                values, length(values), num_sent);
        end
        
        function num_sent = data_send_uint16_values(self, cid, values)
            % Send values as uint16 values via FIFO. 
            % Only used with high_speed controllers.
            num_sent = 0;
            [~, num_sent] = self.call(cid, 'LccDataSendUint16Values', values, ...
                length(values), num_sent);
        end
        
        function num_sent = data_send_uint32_values(self, cid, values)
            % Send values as uint32 values via FIFO.
            % Only used with high_speed controllers.
            num_sent = 0;
            [~, num_sent] = self.call(cid, 'LccDataSendUint32Values', values, ...
                length(values), num_sent);
        end
        
        function values = data_receive_bytes(self, cid, num_values)
            % read num_values bytes via FIFO and return as values
            values = uint8(zeros(num_values, 1));
            num_bytes = 0;
            [values, num_bytes] = self.call(cid, 'LccDataReceiveBytes', values, ...
                num_values, num_bytes);
            values = values(1:num_bytes, 1);
        end
        
        function [values, num_bytes] = data_receive_uint16_values(self, cid, num_values)
            % read num_values uint16 values via FIFO and return as values
            values = uint16(zeros(num_values, 1));
            num_bytes = 0;
            [values, num_bytes] = self.call(cid, 'LccDataReceiveUint16Values', ...
                values, num_values, num_bytes);
            values = values(1:ceil(num_bytes/2), 1);
        end
        
        function [values, num_bytes] = data_receive_uint32_values(self, cid, num_values)
            % read num_values uint32 values via FIFO and return as values
            values = uint32(zeros(num_values, 1));
            num_bytes = 0;
            [values, num_bytes] = self.call(cid, 'LccDataReceiveUint32Values', ...
                values, num_values, num_bytes);
            values = values(1:ceil(num_bytes/4), 1);
        end
      
        function data_start_collect(self, cid, total_samples, trigger)
            % Start an ADC collect into memory, works with DC1371, DC890, DC718.
            % totalSamples -- Number of samples to collect
            % trigger -- Trigger type
            self.call(cid, 'LccDataStartCollect', total_samples, trigger);
        end
        
        function is_done = data_is_collect_done(self, cid)
            % Check if an ADC collect is done, works with DC1371, DC890, DC718
            is_done = false;
            is_done = self.call(cid, 'LccDataIsCollectDone', is_done);
        end
        
        function data_cancel_collect(self, cid)
            % Cancel any ADC collect, works with DC1371, DC890, DC718
            % Note this function must be called to cancel a pending collect
            % OR if a collect has finished but you do not read the full 
            % collection of data.
            self.call(cid, 'LccDataCancelCollect');
        end
        
        function data_set_characteristics(self, cid, is_multichannel,...
                sample_bytes, is_positive_clock)
            % ADC collection characteristics for DC718 and DC890
            % isMultichannel -- True if the ADC has 2 or more channels
            % sampleBytes -- The total number of bytes occupied by a sample
            %     including alignment and meta data (if applicable)
            % isPositiveClock -- True if data is sampled on positive
            %     (rising) clock edges
            self.call(cid, 'LccDataSetCharacteristics', is_multichannel,...
                sample_bytes, is_positive_clock);
        end
        
        function spi_send_bytes(self, cid, values)
            % Send values via SPI controlling chip select.
            % Not used with DC718. Will cause a bunch of ineffective I2C
            % traffic on a DC890 if the demo-board does not have an I/O expander.
            self.call(cid, 'LccSpiSendBytes', values, length(values));
        end
        
        function values = spi_receive_bytes(self, cid, num_values)
            % Receive num_values bytes via SPI controlling chip select.
            % Not used with DC718 or DC890.
            values = uint8(zeros(num_values, 1));
            values = self.call(cid, 'LccSpiReceiveBytes', values, num_values);
        end
        
        function receive_values = spi_transceive_bytes(self, cid, send_values)
            % Transceive sendValues via SPI controlling chip select.
            % Not used with DC718 or DC890.
            num_values = length(send_values);
            receive_values = uint8(zeros(num_values, 1));
            [~, receive_values] = self.call(cid, 'LccSpiTransceiveBytes', ...
                send_values, receive_values, num_values);
        end
        
        function spi_send_byte_at_address(self, cid, address, value)
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
            self.call(cid, 'LccSpiSendByteAtAddress', address, value);
        end
        
        function spi_send_bytes_at_address(self, cid, address, values)
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
            self.call(cid, 'LccSpiSendBytesAtAddress', address, ...
                values, length(values));
        end
        
        function value = spi_receive_byte_at_address(self, cid, address)
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
            value = self.call(cid, 'LccSpiReceiveByteAtAddress', address, ...
                value);
        end
        
        function values = spi_receive_bytes_at_address(self, cid, address, ...
                num_values)
            % Receive num_values bytes via SPI at an address.
            %
            % Not used with DC718 or DC890.
            %
            % Many SPI devices adopt a convention similar to I2C addressing
            % where a byte is sent indicating which register address the 
            % rest of the data pertains to. Often there is a read-write bit
            % in the address, this function will not shift or set any bits 
            % in the address, it basically just writes the address byte and
            % then reads several data bytes. 
            values = uint8(zeros(num_values, 1));
            values = self.call(cid, 'LccSpiReceiveBytesAtAddress', address, ...
                values, num_values);
        end
        
        function spi_set_cs_state(self, cid, chip_select_state)
            % Set the SPI chip-select high or low.
            % Not used with DC718. Will cause a bunch of ineffective I2C
            % traffic on a DC890 if the demo-board does not have an I/O expander.
            if chip_select_state == self.SPI_CS_STATE_HIGH
                state = 1;
            elseif chip_select_state == self.SPI_CS_STATE__LOW
                state = 0;
            else
                error('LtcControllerComm:spiSetCsState', ...
                    ['chipSelectState must be SPI_CS_STATE_HIGH or ', ...
                    'SPI_CS_STATE__LOW']);
            end
            self.call(cid, 'LccSpiSetCsState', state);
        end
        
        function spi_send_no_chip_select(self, cid, values)
            % Send values via SPI without controlling chip-select.
            % Not used with DC718. Will cause a bunch of ineffective I2C
            % traffic on a DC890 if the demo-board does not have an I/O expander.
            self.call(cid, 'LccSpiSendNoChipSelect', values, length(values));
        end
        
        function values = spi_receive_no_chip_select(self, cid, num_values)
            % Receive num_values bytes via SPI without controlling SPI
            % Not used with DC718 or DC890.
            values = uint8(zeros(num_values, 1));
            values = self.call(cid, 'LccSpiReceiveNoChipSelect', ...
                values, num_values);
        end
        
        function receive_values = spi_transceive_no_chip_select(self, cid, ...
                send_values)
            % Transceive send_values bytes via SPI without controlling SPI
            % Not used with DC718 or DC890.
            num_values = length(send_values);
            values = uint8(zeros(num_values, 1));
            [~, receive_values] = self.call(cid, ...
                'LccSpiTransceiveNoChipSelect', send_values, ...
                values, num_values);
        end
        
        function is_loaded = fpga_get_is_loaded(self, cid, fpga_filename)
            % Check if a particular FPGA load is loaded.
            % Not used with high_speed controllers or DC718
            % fpgaFilename -- The base file name without any folder, extension
            % or revision info, for instance 'DLVDS' or 'S2175', case insensitive.
            ref_is_loaded = false;
            [~, is_loaded] = self.call(cid, 'LccFpgaGetIsLoaded', fpga_filename, ref_is_loaded);
        end
        
        function fpga_load_file(self, cid, fpga_filename)
            % Loads an FPGA file
            % Not used with high_speed controllers or DC718
            % fpgaFilename -- The base file name without any folder, extension
            % or revision info, for instance 'DLVDS' or 'S2175', case insensitive.
            self.call(cid, 'LccFpgaLoadFile', fpga_filename);
        end
        
        function progress = fpga_load_file_chunked(self, cid, fpga_filename)
            % Load a particular FPGA file a chunk at a time. 
            % Not used with high_speed controllers or DC718
            % fpga_filename -- The base file name without any folder, extension
            % or revision info, for instance 'DLVDS' or 'S2175', case insensitive.
            % The first call returns a number, each subsequent call will return a
            % SMALLER number. The process is finished when it returns 0.
            ref_progress = 0;
            progress = self.call(cid, 'LccFpgaLoadFileChunked', fpga_filename, ref_progress);
        end
        
        function fpga_cancel_load(self, cid)
            % Must be called if you abandon loading the FPGA file before complete
            % Not used with high_speed controllers or DC718
            self.call(cid, 'LccFpgaCancelLoad');
        end
        
        function string = eeprom_read_string(self, cid, num_chars)
            % Receive an EEPROM string.
            string = self.call(cid, 'LccEepromReadString', blanks(num_chars), num_chars);
        end
        
        % The following functions apply ONLY to HighSpeed type controllers
        
        function hs_set_bit_mode(self, cid, bit_mode)
            % Set the device to MPSSE mode (for SPI, FPGA registers and
            % GPIO) or FIFO mode (for fast FIFO communication)
            if bit_mode == self.HS_BIT_MODE_FIFO
                mode = 64;
            elseif bit_mode == self.HS_BIT_MODE_MPSSE
                mode = 2;
            else
                error('LtcControllerComm:setBitMode', ...
                    'bitMode must be HS_BIT_MODE_MPSSE or HS_BIT_MODE_FIFO');
            end
            self.call(cid, 'LccHsSetBitMode', mode);
        end
        
        function hs_purge_io(self, cid)
            % Clear all data in the USB I/O buffers.
            self.call(cid, 'LccHsPurgeIo');
        end
        
        function hs_fpga_toggle_reset(self, cid)
            % Set the FPGA reset bit low then high.
            self.call(cid, 'LccHsFpgaToggleReset');
        end
        
        function hs_fpga_write_address(self, cid, address)
            % Set the FPGA address to write or read.
            self.call(cid, 'LccHsFpgaWriteAddress', address);
        end
        
        function hs_fpga_write_data(self, cid, data)
            % Write a value to the current FPGA address.
            self.call(cid, 'LccHsFpgaWriteData', data);
        end
        
        function data = hs_fpga_read_data(self, cid)
            % Read a value from the current FPGA address and return it.
            data = 0;
            data = self.call(cid, 'LccHsFpgaReadData', data);
        end
        
        function hs_fpga_write_data_at_address(self, cid, address, data)
            % Set the current address and write a value to it.
            self.call(cid, 'LccHsFpgaWriteDataAtAddress', address, data);
        end
        
        function data = hs_fpga_read_data_at_address(self, cid, address)
            % Set the current address and read a value from it.
            data = 0;
            data = self.call(cid, 'LccHsFpgaReadDataAtAddress', address, ...
                data);
        end
        
        function hs_mpsse_enable_divide_by_5(self, cid, enable)
            % Enables or disables the MPSSE master clock divide-by-5 (enabled by default)
            self.call(cid, 'LccHsMpsseEnableDivideBy5', enable);
        end

        function hs_mpsse_set_clk_divider(self, cid, divider)
            % Sets MPSSE SCK divider (default 0) frequency is F / (2 * (1 + divider)) where F is 60 or 12MHz
            self.call(cid, 'LccHsMpsseSetClkDivider', divider);
        end
        
        function hs_gpio_write_high_byte(self, cid, value)
            % Set the GPIO high byte to a value.
            self.call(cid, 'LccHsGpioWriteHighByte', value);
        end
        
        function value = hs_gpio_read_high_byte(self, cid)
            % Read the GPIO high byte and return the value.
            value = 0;
            value = self.call(cid, 'LccHsGpioReadHighByte', value);
        end
        
        function hs_gpio_write_low_byte(self, cid, value)
            % Set the GPIO low byte to a value.
            self.call(cid, 'LccHsGpioWriteLowByte', value);
        end
        
        function value = hs_gpio_read_low_byte(self, cid)
            % Read the GPIO low byte and return the value
            value = 0;
            value = self.call(cid, 'LccHsGpioReadLowByte', value);
        end
        
        function hs_fpga_eeprom_set_bit_bang_register(self, cid, register_address)
            % Set the FPGA register used to do bit-banged I2C.
            % If not called, address used is 0x11.
            self.call(cid, 'LccHsFpgaEepromSetBitBangRegister', register_address);
        end
             
        % The following functions apply ONLY to DC1371 controllers
             
        function dc1371_set_generic_config(self, cid, generic_config)
            % genericConfig is always 0, so you never have to call this function
            generic_config = hex2dec(generic_config);
            self.call(cid, 'Lcc1371SetGenericConfig', generic_config);
        end
        
        function dc1371_set_demo_config(self, cid, demo_config)
            % Set the value corresponding to the four pairs of hex digits at the end
            % of line three of the EEPROM string for a DC1371A demo-board.
            % demoConfig -- If an ID string were to have 01 02 03 04,
            %     demoConfig would be '01020304' (a string) or '0x01020304'
            demo_config = sscanf(demo_config, '%x');
            self.call(cid, 'Lcc1371SetDemoConfig', demo_config);
        end
        
        function dc1371_spi_choose_chip_select(self, cid, new_chip_select)
            % Set the chip select to use in future spi commands, 1 (default) is
            % correct for most situations, rarely 2 is needed.
            % newChipSelect -- 1 (usually) or 2
            self.call(cid, 'Lcc1371SpiChooseChipSelect', new_chip_select);
        end
        
        % The following functions apply ONLY to DC890 controllers
        
        function dc890_gpio_set_byte(self, cid, byte)
            % Set the IO expander GPIO lines to byte, all spi transaction use this as
            % a base value, or can be used to bit bang lines
            % byte -- The bits of byte correspond to the output lines of the IO expander.
            self.call(cid, 'Lcc890GpioSetByte', byte);
        end
        
        function dc890_gpio_spi_set_bits(self, cid, cs_bit, sck_bit, sdi_bit)
            % Set the bits used for SPI transactions, which are performed by
            % bit-banging the IO expander on demo-boards that have one. This function
            % must be called before doing any spi transactions with the DC890
            % 
            % cs_bit -- the bit used as chip select
            % sck_bit -- the bit used as sck
            % sdi_bit -- the bit used as sdi
            self.call(cid, 'Lcc890GpioSpiSetBits', cs_bit, sck_bit, sdi_bit);
        end
        
        function dc890_flush(self, cid)
            % Causes the DC890 to terminate any I2C (or GPIO or SPI) transactions then
            % purges the buffers.
            self.call(cid, 'Lcc890Flush');
        end
    end
end

