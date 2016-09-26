classdef Dc1371
    %UNTITLED2 Summary of this class goes here
    %   Detailed explanation goes here
    
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
            self.lcc.Dc1371SetDemoConfig(self.cid, demoConfig);
        end
        
        function VPrint(self, message)
            if self.isVerbose
                fprintf(message);
            end
        end
    end
    
end

