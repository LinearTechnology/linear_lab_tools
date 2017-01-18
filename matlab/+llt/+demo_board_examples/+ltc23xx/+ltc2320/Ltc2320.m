classdef Ltc2320 < llt.common.Dc890
% Class to connect to the DC890 controller and use Ltc2320/24/25 demoboards
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
        osr;
        verify;
        is_distributed_read;
    end
    
    methods 
        function self = Ltc2320(lcc, dc_number, num_channels, num_bites, is_verbose)
            if ~exist('is_verbose', 'var'); is_verbose = false; end

            self = self@llt.common.Dc890(lcc, dc_number, 'CMOS', num_channels, false, ...
                num_bites, 32, true, [], is_verbose);
        end
        
        function varargout = collect(self, num_samples, trigger, timeout, ...
                is_randomized, is_alternate_bit)
            if ~exist('timeout', 'var'); timeout = 5; end
            if ~exist('is_randomized', 'var'); is_randomized = false; end
            if ~exist('is_alternate_bit', 'var'); is_alternate_bit = false; end
            if (num_samples * self.num_channels) > MAX_TOTAL_SAMPLES
                error('LtcControllerComm:InvalidArgument', ...
                    'Num samples must be <= %d', MAX_TOTAL_SAMPLES / self.num_channels)
            end
            [varargout{1:nargout}] = collect@llt.common.Dc890(self, 2*num_samples, trigger, timeout, ...
                is_randomized, is_alternate_bit);
        end
                  
        function data = fix_data(self, rawData, is_randomized, is_alternateBit)
            rawData = self.get_data(rawData);
            data = llt.common.fix_data(rawData, self.num_bits, 16, ...
                                  self.is_bipolar, is_randomized, is_alternateBit);
        end
    end
    
    methods (Access = private)
        function start_sample = get_start_sample(self, first_sample)
            channel = bitand(first_sample, 7);
            if channel == 0
                start_sample = 1;
            else
                start_sample = self.num_channels - channel + 1;
            end
        end

        function data = get_data(self, data)
            num_samples = length(data) / 2;
            start_sample = self.get_start_sample(data(0));
            data = data(start_sample:(start_sample + num_samples - 1));
            for i = 1:num_samples
                if bitand(data(i), 7) ~= mod((i-1), self.num_channels)
                    error('LtcControllerComm:HardwareError', ...
                        'Unexpected channel number in metadata');
                end
                data(i) = bitshift(data(i), -16);
            end
        end
    end
end

