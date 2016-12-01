classdef Dc890
    % Class to connect to the DC890 controller
    %
    % REVISION HISTORY
    % $Revision: 2583 $
    % $Date: 2014-06-27 17:21:46 -0700 (Fri, 27 Jun 2014) $
    % 
    % Copyright (c) 2016, Linear Technology Corp.(LTC)
    % All rights reserved.
    %
    % Redistribution and use in source and binary forms, with or without
    % modification, are permitted provided that the following conditions are met:
    %
    % 1. Redistributions of source code must retain the above copyright notice, 
    %    this list of conditions and the following disclaimer.
    % 2. Redistributions in binary form must reproduce the above copyright 
    %    notice, this list of conditions and the following disclaimer in the 
    %    documentation and/or other materials provided with the distribution.
    %
    % THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
    % AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE 
    % IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE 
    % ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE 
    % LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
    % CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF 
    % SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS 
    % INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN 
    % CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
    % ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE 
    % POSSIBILITY OF SUCH DAMAGE.
    %
    % The views and conclusions contained in the software and documentation are 
    % those of the authors and should not be interpreted as representing official
    % policies, either expressed or implied, of Linear Technology Corp.
    
    properties (Access = protected)
        lcc;
        num_bits;
        alignment;
        is_bipolar;
        bytes_per_sample;
        num_channels;
        is_verbose;
        cid;
    end
    
    methods 
        function self = Dc890(lcc, dc_number, fpga_load, num_channels, is_positive_clock, ...
                num_bits, alignment, is_bipolar, spi_reg_values, is_verbose)
            if ~exist('spi_reg_values', 'var'); spi_reg_values = []; end;
            if ~exist('is_verbose', 'var'); is_verbose = false; end
            
            self.lcc = lcc;
            self.num_bits = num_bits;
            self.alignment = alignment;
            self.is_bipolar = is_bipolar;
            self.num_channels = num_channels;
            self.is_verbose = is_verbose;
            
            if alignment > 16
                self.bytes_per_sample = 4;
            else
                self.bytes_per_sample = 2;
            end

            controller_info = llt.common.get_controller_info_by_eeprom(lcc, ...
                lcc.TYPE_DC890, dc_number, lcc.DC890_EEPROM_SIZE, is_verbose);
            self.cid = lcc.init(controller_info);
            
            is_multichannel = num_channels > 1;
            self.init_controller(fpga_load, is_multichannel, is_positive_clock);
            
            self.set_spi_registers(spi_reg_values);
        end
        
        function varargout = collect(self, num_samples, trigger, timeout, is_randomized, ...
                is_alternate_bit)
            if ~exist('timeout', 'var'); timeout = 5; end
            if ~exist('is_randomized', 'var'); is_randomized = false; end
            if ~exist('is_alternate_bit', 'var'); is_alternate_bit = false; end
            
            num_samples = num_samples * self.num_channels;
            
            self.lcc.dc890_flush(self.cid);
            self.vprint('Starting collect...');
            llt.common.start_collect(self.lcc, self.cid, num_samples, trigger, timeout);
            self.vprint('Done.\nReading data...');
            self.lcc.dc890_flush(self.cid);
            
            if self.bytes_per_sample == 2
                [raw_data, num_bytes] = self.lcc.data_receive_uint16_values(self.cid, num_samples);
                if num_bytes ~= num_samples * 2
                    error('LtcControllerComm:HardwareError', 'Didn''t get all bytes.');
                end
            else
                [raw_data, num_bytes] = self.lcc.data_receive_uint32_values(self.cid, num_samples);
                if num_bytes ~= num_samples * 4
                    error('LtcControllerComm:HardwareError', 'Didn''t get all bytes.');
                end
            end
            
            self.vprint('Done.');
            
            data = self.fix_data(raw_data, is_randomized, is_alternate_bit);
            [varargout{1:nargout}] = llt.common.scatter(data, self.num_channels);
        end
               
        function set_spi_registers(self, register_values)
            if ~isempty(register_values)
                self.lcc.dc890_gpio_set_byte(self.cid, 240); % 0xF0
                self.lcc.dc890_gpio_spi_set_bits(self.cid, 3, 0, 1);
                for i = 1:2:length(register_values)
                    self.lcc.spi_send_byte_at_address(self.cid, register_values(i), ...
                        register_values(i+1));
                end
                self.lcc.dc890_gpio_set_byte(self.cid, 255); % 0xFF
            end
        end
        
        function data = fix_data(self, raw_data, is_randomized, is_alternate_bit)
            data = llt.common.fix_data(raw_data, self.num_bits, self.alignment, ...
                self.is_bipolar, is_randomized, is_alternate_bit);
        end
        
        function num_bits = get_num_bits(self)
            num_bits = self.num_bits;
        end
    end
    
    methods (Access = private)
        function init_controller(self, fpga_load, is_multichannel, is_positive_clock)
            if ~self.lcc.fpga_get_is_loaded(self.cid, fpga_load)
                self.vprint('Loading FPGA...');
                self.lcc.fpga_load_file(self.cid, fpga_load);
                self.vprint('done.\n');
            else
                self.vprint('FPGA already loaded\n');
            end
            self.lcc.data_set_high_byte_first(self.cid);
            self.lcc.data_set_characteristics(self.cid, is_multichannel, self.bytes_per_sample, is_positive_clock);
        end
        
        function vprint(self, message)
            if self.is_verbose
                fprintf(message);
            end
        end
    end
end
