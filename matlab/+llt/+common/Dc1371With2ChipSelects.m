classdef Dc1371With2ChipSelects
    % Class to connect to the DC1371 controller
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
    
    properties (Access = private)
        lcc;
        num_bits;
        alignment;
        is_bipolar;
        bytes_per_sample;
        num_channels;
        fpga_load;
        is_verbose;
        cid;
    end
    
    methods 
        function self = Dc1371With2ChipSelects(lcc, dc_number, fpga_load, num_channels, ...
                num_bits, alignment, is_bipolar, demo_config, spi_reg_values, is_verbose)
            if ~exist('spi_reg_values', 'var'); spi_reg_values = []; end;
            if ~exist('is_verbose', 'var'); is_verbose = false; end
            
            self.lcc = lcc;
            self.num_bits = num_bits;
            self.alignment = alignment;
            self.is_bipolar = is_bipolar;
            self.num_channels = num_channels;
            self.fpga_load = fpga_load;
            self.is_verbose = is_verbose;
            
            controller_info = llt.common.get_controller_info_by_eeprom(lcc, ...
                lcc.TYPE_DC1371, dc_number, lcc.DC1371_EEPROM_SIZE, is_verbose);
            self.cid = lcc.init(controller_info);
            
            self.init_controller(demo_config, spi_reg_values);
        end
        
        function varargout = collect(self, num_samples, trigger, timeout, is_randomized, ...
                is_alternate_bit)
            if ~exist('timeout', 'var'); timeout = 5; end
            if ~exist('is_randomized', 'var'); is_randomized = false; end
            if ~exist('is_alternate_bit', 'var'); is_alternate_bit = false; end
            
            num_samples = num_samples * self.num_channels;
            
            self.vprint('Starting collect...');
            llt.common.start_collect(self.lcc, self.cid, num_samples, trigger, timeout);
            self.vprint('done.\nReading data...');
            
            [raw_data, num_bytes] = self.lcc.data_receive_uint16_values(self.cid, num_samples);
            if num_bytes ~= num_samples * 2
                error('LtcControllerComm:HardwareError', 'Didn''t get all bytes.');
            end           
            self.vprint('done.\n');
            
            data = llt.common.fix_data(raw_data, self.num_bits, self.alignment, ...
                self.is_bipolar, is_randomized, is_alternate_bit);
            [varargout{1:nargout}] = llt.common.scatter(data, self.num_channels);
        end
               
        function set_spi_registers(self, register_values)
            if ~isempty(register_values)
                self.vprint('Updating SPI registers...');
                self.lcc.dc1371_spi_set_chip_select(self.cid, 0);
                for i = 1:2:length(register_values)
                    self.lcc.spi_send_byte_at_address(self.cid, register_values(i), register_values(i+1));
                end
                self.lcc.dc1371_spi_set_chip_select(self.cid, 1);
                for i = 1:2:length(register_values)
                    self.lcc.spi_send_byte_at_address(self.cid, register_values(i), register_values(i+1));
                end
                self.vprint('done.\n');
            end
            % The DC1371 needs to check for FPGA load after a change in the SPI registers
            if ~self.lcc.fpga_get_is_loaded(self.cid, self.fpga_load)
                self.vprint('Loading FPGA...');
                self.lcc.fpga_load_file(self.cid, self.fpga_load);
                self.vprint('done.\n');
            else
                self.vprint('FPGA already loaded\n');
            end
        end
        
        function num_bits = get_num_bits(self)
            num_bits = self.num_bits;
        end
        
    end
    
    methods (Access = private)
        
       function init_controller(self, demo_config, spi_register_values)
            self.lcc.data_set_high_byte_first(self.cid);
            self.set_spi_registers(spi_register_values);
            % demo-board specific information needed by the DC1371
            self.lcc.dc1371_set_demo_config(self.cid, demo_config);
        end
        
        function vprint(self, message)
            if self.is_verbose
                fprintf(message);
            end
        end
    end
end
