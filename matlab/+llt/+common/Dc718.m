classdef Dc718    
    % Class to connect to the DC718 controller
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
        is_verbose;
        cid;
    end
    
    methods 
        function self = Dc718(lcc, dc_number, is_positive_clock, ...
                num_bits, alignment, is_bipolar, is_verbose)
            if ~exist('is_verbose', 'var'); is_verbose = false; end
            
            self.lcc = lcc;
            self.num_bits = num_bits;
            self.alignment = alignment;
            self.is_bipolar = is_bipolar;
            self.is_verbose = is_verbose;
            
            if alignment > 16
                self.bytes_per_sample = 3;
            else
                self.bytes_per_sample = 2;
            end

            controller_info = llt.common.get_controller_info_by_eeprom(lcc, ...
                lcc.TYPE_DC718, dc_number, lcc.DC718_EEPROM_SIZE, is_verbose);
            self.cid = lcc.init(controller_info);
            
            lcc.data_set_high_byte_first(self.cid);
            lcc.data_set_characteristics(self.cid, false, self.bytes_per_sample, ...
                is_positive_clock);
        end
        
        function data = collect(self, num_samples, trigger, timeout, is_randomized, ...
                is_alternate_bit)
            if ~exist('timeout', 'var'); timeout = 5; end
            if ~exist('is_randomized', 'var'); is_randomized = false; end
            if ~exist('is_alternateBit', 'var'); is_alternate_bit = false; end
            
            self.vprint('Starting collect...');
            llt.common.start_collect(self.lcc, self.cid, num_samples, trigger, timeout);
            self.vprint('Done.\nReading data...');
            
            if self.bytes_per_sample == 2
                [raw_data, num_bytes] = self.lcc.data_receive_uint16_values(self.cid, num_samples);
                if num_bytes ~= num_samples * 2
                    error('LtcControllerComm:HardwareError', 'Didn''t get all bytes.');
                end
            else
                raw_data = self.read_3_byte_values(num_samples);
            end
            
            self.vprint('Done.');
            
            data = llt.common.fix_data(raw_data, self.num_bits, self.alignment, ...
                self.is_bipolar, is_randomized, is_alternate_bit);
        end
        
        function num_bits = get_num_bits(self)
            num_bits = self.num_bits;
        end
    end
    methods (Access = private)
        function data = read_3_byte_values(self, num_samples)
            raw_data = self.lcc.data_receive_bytes(self.cid, num_samples * 3);
            if length(raw_data) ~= num_samples*3
                error('LtcControllerComm:HardwareError', 'Didn''t get all bytes.');
            end
            raw_data = int32(reshape(raw_data, 3, num_samples));
            data = bitor(bitshift(raw_data(1,:), 16), ...
                bitor(bitshift(raw_data(2,:), 8), raw_data(3,:)));
        end
        
        function vprint(self, message)
            if self.is_verbose
                fprintf(message);
            end
        end
    end
end

