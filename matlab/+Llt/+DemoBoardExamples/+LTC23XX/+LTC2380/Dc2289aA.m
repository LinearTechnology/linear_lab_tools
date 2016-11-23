classdef Dc2289aA < Llt.Common.Dc890
    % Class to connect to the DC890 controller and use the DC2289A-A
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
        isDistributedRead;
    end
    
    methods 
        function self = Dc2289aA(lcc, osr, verify, isDistributedRead, isVerbose)
            if ~exist('isVerbose', 'var'); isVerbose = false; end

            self = self@Llt.Common.Dc890(lcc, 'DC2289A-A', 'CMOS', 1, false, ...
                24, 24, true, [], isVerbose);
            self.osr = osr;
            self.verify = verify;
            self.ConfigCpld(osr, verify, isDistributedRead);
        end
        
        function varargout = Collect(self, nSamples, trigger, timeout, ...
                isRandomized, isAlternateBit)
            if ~exist('timeout', 'var'); timeout = 5; end
            if ~exist('isRandomized', 'var'); isRandomized = false; end
            if ~exist('isAlternateBit', 'var'); isAlternateBit = false; end
            
            [varargout{1:nargout}] = Collect@Llt.Common.Dc890(self, nSamples * 2, trigger, timeout, ...
                isRandomized, isAlternateBit);
        end
               
        function ConfigCpld(self, osr, verify, isDistributedRead)
            if verify && isDistributedRead
                error('Dc2289aA:ConfigCpld:NotSupported', ...
                    'Cannot use verify and distributed read');
            end
            if isDistributedRead && osr < 25
                error('Dc2289aA:ConfigCpld:NotSupported', ...
                    'OSR Must be >=25 for distributed read');
            end
            self.verify = verify;
            self.osr = osr;
            % Bit Map
            % 7 => WRIN (CS)
            % 6 => SDI
            % 5 => SCK
            % 4 => AUX0
            % 3 => AUX1 (Always set)
            % 2 => AUX2 (~Disributed/normal)
            % 1 => Unused
            % 0 => ~VERIFY (~Verify/normal)
            WRITE_IN    = 128; % 0x80
            AUX_0       = 16;  % 0x10
            AUX_1       = 8;   % 0x08
            AUX_2       = 4;   % 0x04
            VERIFY_N    = 1;   % 0x01
            base = AUX_1;
            if ~isDistributedRead
                base = bitor(base, AUX_2);
            end
            if ~self.verify
                base = bitor(base, VERIFY_N);
            end

            % Configure CPLD port
            self.lcc.Dc890GpioSpiSetBits(self.cid, 0, 5, 6);

            % Bring everything down to make sure the CPLD is not listening
            self.lcc.Dc890GpioSetByte(self.cid, 0); % 0x00

            self.lcc.Dc890GpioSetByte(self.cid, base);
            self.lcc.SpiSendNoChipSelect(self.cid, [bitand(bitshift(osr, -8), 255), bitand(osr, 255)]);

            % Now pull WRIN high
            self.lcc.Dc890GpioSetByte(self.cid, bitor(base, WRITE_IN));

            % Now pull AUX0 high
            self.lcc.Dc890GpioSetByte(self.cid, bitor(base, bitor(WRITE_IN, AUX_0)));
        end
    
        function data = FixData(self, rawData, isRandomized, isAlternateBit)
            if self.verify
                rawData = self.GetData(rawData);
            end
            data = Llt.Common.FixData(rawData, self.nBits, self.alignment, ...
                                  self.isBipolar, isRandomized, isAlternateBit);
        end
    end
    
    methods (Access = private)
        function rawData = FormatData(self, data, metaData)
            rawData = bitand(data, 16777215); % 0xFFFFFF
            osrMinus1 = bitor(bitand(bitshift(data, -24), 255), ...
                bitand(bitshift(metaData, -16), 65280));
            if nnz(osrMinus1 ~= self.osr - 1) ~= 0
                      error('Dc2289aA:Collect:HardwareError', 'Invalid OSR data');
            end
        end

        function rawData = GetData(self, data)
            osrMinus1 = self.osr - 1;
            data0 = data(1:2:end);
            data1 = data(2:2:end);

            if bitand(osrMinus1, 255) ~=  bitand(bitshift(osrMinus1, -8), 255) 
                if bitand(bitshift(data0(1), -24), 255) == bitand(osrMinus1, 255)
                    % data0 is the data
                    rawData = self.FormatData(data0, data1);
                else
                    % data1 is the data
                    rawData = self.FormatData(data1, data0);
                end
            elseif any(bitand(data0, 16777215) ~= 0)
                rawData = self.FormatData(data1, data0);
            else
                rawData = self.FormatData(data0, data1);
            end
        end
    end
end

