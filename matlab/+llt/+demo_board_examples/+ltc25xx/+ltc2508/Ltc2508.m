classdef Ltc2508 < llt.common.Dc890
    % Class to connect to the DC890 controller and use Ltc2320/24/25 demoboards
    %
    % REVISION HISTORY
    % $Revision: 2583 $
    % $Date: 2017-04-12 17:21:46 -0700 (Fri, 27 Jun 2014) $
    %
    % Copyright (c) 2017, Linear Technology Corp.(LTC)
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
        df;
        verify;
        is_distributed_read;
        is_filtered_data;
        df_map;
    end
    properties (Constant)
        SINC_1_FILTER     = 1;
    end
    
    methods
        function self = Ltc2508(lcc, df, verify, is_distributed_rd, is_filtered_data, verbose)
            if ~exist('verbose', 'var'); verbose = false; end
            self = self@llt.common.Dc890(lcc, 'DC2222A-B', 'CMOS', 1, false, ...
                32, 32, true, [], verbose);
            self.df_map = containers.Map([256, 1024, 4092, 16384],[0,1,2,3]);
            self = self.config_cpld(df, verify, is_distributed_rd, is_filtered_data);
        end
        
        function varargout = collect(self, num_samples, trigger, timeout, ...
                is_randomized, is_alternate_bit)
            if ~exist('timeout', 'var'); timeout = 30; end
            if ~exist('is_randomized', 'var'); is_randomized = false; end
            if ~exist('is_alternate_bit', 'var'); is_alternate_bit = false; end
            if self.verify; num_samples = num_samples * 2; end
            
            [varargout{1:nargout}] = collect@llt.common.Dc890(self, num_samples, trigger, timeout, ...
                is_randomized, is_alternate_bit);
        end
        
        function self = config_cpld(self, df, verify, is_distributed_rd, is_filtered_data)
            if ~is_filtered_data && (verify || is_distributed_rd)
                error('LtcControllerComm:NotSupported', ...
                    'Verify and distributed read do not work with unfiltered data');
            end
            self.verify = verify;
            self.df = df;
            self.is_filtered_data = is_filtered_data;
            
            % order of events:
            % 1. Bring down WRTIN_I2C and both chip selects (and verify if needed).
            % 2. Send main config info with SDI1/SCK1.
            % 3. Send variable df if needed with SDI2/SCK2.
            % 4. Bring up CS2.
            % 5. Bring up CS1 and WRTIN_I2C
            % steps two and three can be done in either order.
            
            % Dist. Read: bit 11
            % df code (0-> df 256, 1-> df 1024, 2-> df 4096, 3-> 16384) bits 8:5
            % A/B (0->nyquist data, 1->filtered data) bit 0
            
            % IO expander bit numbers
            CS1_BIT      = 7;
            SDI1_BIT     = 6;
            SCK1_BIT     = 5;
            N_VERIFY_BIT = 4;
            WRITE_IN_BIT = 3;
            CS2_BIT      = 2;
            %SDI2_BIT     = 1;
            %SCK2_BIT     = 0;
            
            % IO expander byte values
            CS1      = bitshift(1, CS1_BIT);
            N_VERIFY = bitshift(1, N_VERIFY_BIT);
            WRITE_IN = bitshift(1, WRITE_IN_BIT);
            CS2      = bitshift(1, CS2_BIT);
            
            DIST_READ = 8;
            FILTERED  = 1;
            df_code = self.df_map(df);
            if is_filtered_data
                msb = 0;
                if is_distributed_rd; msb = bitor(msb, DIST_READ); end
                lsb = bitor(FILTERED, bitshift(df_code, 5));
            else
                msb = 0;
                lsb = 0;
            end
            base = 0;
            if ~verify; base = bitor(base, N_VERIFY); end
            
            self.lcc.dc890_gpio_spi_set_bits(self.cid, 0, SCK1_BIT, SDI1_BIT);
            self.lcc.dc890_gpio_set_byte(self.cid, base);
            self.lcc.spi_send_no_chip_select(self.cid, [msb, lsb]);
            
            base = bitor(base, CS2);
            self.lcc.dc890_gpio_set_byte(self.cid, base);
            base = bitor(base, bitor(CS1, WRITE_IN));
            self.lcc.dc890_gpio_set_byte(self.cid, base);
        end
        
        function data = fix_data(self, raw_data, ~, ~)
            if self.verify
                data = self.get_data_and_check_df(raw_data);
            elseif self.is_filtered_data
                data = typecast(raw_data,'int32');
            else
                [data, cm_data] = self.get_all_data(raw_data);
                data = {data, cm_data};
            end
        end
        
        function num_bits = get_num_bits(self)
            if self.is_filtered_data
                num_bits = self.num_bits;
            else
                num_bits = 14;
            end
        end
        
    end
    methods (Access = private)
        function data = get_data_and_check_df(self, data)
            % figure out the expected metadata
            df_code = self.df_map(self.df);
            check = bitshift(bitor(bitshift(df_code*2+8, 4), 5),24);
            check_mask = 4278190080; % 0xFF000000
            
            % figure out which is data and which is metadata
            data_1 = reshape(data(1:2:end), 1, []);
            data_2 = reshape(data(2:2:end), 1, []);
            
            
            for d = [data_1; data_2]
                if bitand(d(1), check_mask) ~= check
                    data = data_1;
                    meta = data_2;
                    break;
                elseif bitand(d(2), check_mask) ~= check
                    data = data_2;
                    meta = data_1;
                    break;
                end
            end
            
            % check metadata
            for m = meta
                if bitand(m, check_mask) ~= check
                    error('LtcControllerComm:HardwareError', 'Invalid data');
                end
            end
            
            data = typecast(data,'int32');
        end
        
        function [data, cm_data] = get_all_data(~, raw_data)
            cm_data = llt.common.fix_data(raw_data, 8, 18, true);
            data = llt.common.fix_data(bitshift(raw_data, -18), 14, 14, true);
        end
    end
end
