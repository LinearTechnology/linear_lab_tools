classdef Dc718
    %UNTITLED2 Summary of this class goes here
    %   Detailed explanation goes here
    
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

