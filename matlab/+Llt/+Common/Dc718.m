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
        nBits;
        alignment;
        isBipolar;
        bytesPerSample;
        isVerbose;
        cid;
    end
    
    methods 
        function self = Dc718(lcc, dcNumber, isPositiveClock, ...
                nBits, alignment, isBipolar, isVerbose)
            if ~exist('isVerbose', 'var'); isVerbose = false; end
            
            self.lcc = lcc;
            self.nBits = nBits;
            self.alignment = alignment;
            self.isBipolar = isBipolar;
            self.isVerbose = self.isVerbose;
            
            if alignment > 16
                self.bytesPerSample = 3;
            else
                self.bytesPerSample = 2;
            end

            controllerInfo = Llt.Common.GetControllerInfoByEeeprom(lcc, ...
                lcc.TYPE_DC718, dcNumber, lcc.DC718_EEPROM_SIZE, isVerbose);
            self.cid = lcc.Init(controllerInfo);
            
            lcc.DataSetHighByteFirst();
            lcc.DataSetCharacteristics(false, self.bytesPerSample, isPositiveClock);
        end
        
        function data = Collect(self, nSamples, trigger, timeout, isRandomized, isAlternateBit)
            if ~exist('timeout', 'var'); timeout = 5; end
            if ~exist('isRandomized', 'var'); isRandomized = false; end
            if ~exist('isAlternateBit', 'var'); isAlternateBit = false; end
            
            self.VPrint('Starting collect...');
            Llt.Common.StartCollect(self.lcc, self.cid, nSamples, trigger, timeout);
            self.VPrint('Done.\nReading data...');
            
            if self.bytesPerSample == 2
                [nBytes, rawData] = self.lcc.DataReceiveUint16Values(self.cid, nSamples);
                if nBytes ~= nSamples * 2
                    error('LtcControllerComm:HardwareError', 'Didn''t get all bytes.');
                end
            else
                rawData = self.read3ByteValues(nSamples);
            end
            
            self.VPrint('Done.');
            
            data = Llt.Common.FixData(rawData, self.nBits, self.alignmnet, ...
                self.isBipolar, isRandomized, isAlternateBit);
        end
        
        function nBits = GetNBits(self)
            nBits = self.nBits;
        end
    end
    methods (Access = private)
        function data = Read3ByteValues(self, nSamples)
            [nBytes, rawData] = self.lcc.DataReceiveBytes(nSamples * 3);
            if nBytes ~= nSamples*3
                error('LtcControllerComm:HardwareError', 'Didn''t get all bytes.');
            end
            rawData = reshape(rawData, 3, nSamples);
            data = bitor(bitshift(rawData(1,:), 16), ...
                bitor(bitshift(rawData(2,:), 8), rawData(3,:)));
        end
        
        function VPrint(self, message)
            if self.isVerbose
                fprintf(message);
            end
        end
    end
    
end

