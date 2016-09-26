classdef Dc1371
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
        nBits;
        alignment;
        isBipolar;
        bytesPerSample;
        nChannels;
        fpgaLoad;
        isVerbose;
        cid;
    end
    
    methods 
        function self = Dc1371(lcc, dcNumber, fpgaLoad, nChannels, ...
                nBits, alignment, isBipolar, demoConfig, spiRegValues, isVerbose)
            if ~exist('spiRegValues', 'var'); spiRegValues = []; end;
            if ~exist('isVerbose', 'var'); isVerbose = false; end
            
            self.lcc = lcc;
            self.nBits = nBits;
            self.alignment = alignment;
            self.isBipolar = isBipolar;
            self.nChannels = nChannels;
            self.fpgaLoad = fpgaLoad;
            self.isVerbose = isVerbose;
            
            controllerInfo = Llt.Common.GetControllerInfoByEeeprom(lcc, ...
                lcc.TYPE_DC1371, dcNumber, lcc.DC1371_EEPROM_SIZE, isVerbose);
            self.cid = lcc.Init(controllerInfo);
            
            self.InitController(demoConfig, spiRegValues);
        end
        
        function varargout = Collect(self, nSamples, trigger, timeout, isRandomized, isAlternateBit)
            if ~exist('timeout', 'var'); timeout = 5; end
            if ~exist('isRandomized', 'var'); isRandomized = false; end
            if ~exist('isAlternateBit', 'var'); isAlternateBit = false; end
            
            self.VPrint('Starting collect...');
            Llt.Common.StartCollect(self.lcc, self.cid, nSamples, trigger, timeout);
            self.VPrint('done.\nReading data...');
            
            [rawData, nBytes] = self.lcc.DataReceiveUint16Values(self.cid, nSamples);
            if nBytes ~= nSamples * 2
                error('LtcControllerComm:HardwareError', 'Didn''t get all bytes.');
            end           
            self.VPrint('done.\n');
            
            data = Llt.Common.FixData(rawData, self.nBits, self.alignment, ...
                self.isBipolar, isRandomized, isAlternateBit);
            [varargout{1:nargout}] = Llt.Common.Scatter(data);
        end
               
        function SetSpiRegisters(self, registerValues)
            if ~isempty(registerValues)
                self.VPrint('Updating SPI registers...');
                for i = 1:2:length(registerValues)
                    self.lcc.SpiSendByteAtAddress(self.cid, registerValues(i), registerValues(i+1));
                end
                self.VPrint('done.\n');
            end
            % The DC1371 needs to check for FPGA load after a change in the SPI registers
            if ~self.lcc.FpgaGetIsLoaded(self.cid, self.fpgaLoad)
                self.VPrint('Loading FPGA...');
                self.lcc.FpgaLoadFile(self.cid, self.fpgaLoad);
                self.VPrint('done.\n');
            else
                self.VPrint('FPGA already loaded\n');
            end
        end
        
        function nBits = GetNBits(self)
            nBits = self.nBits;
        end
        
    end
    
    methods (Access = private)
        
       function InitController(self, demoConfig, spiRegisterValues)
            self.lcc.DataSetHighByteFirst(self.cid);
            self.SetSpiRegisters(spiRegisterValues);
            % demo-board specific information needed by the DC1371
            self.lcc.Dc1371SetDemoConfig(self.cid, demoConfig);
        end
        
        function VPrint(self, message)
            if self.isVerbose
                fprintf(message);
            end
        end
    end
    
end

