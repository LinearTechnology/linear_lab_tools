% DC2135 or DC1925 / LTC2378-20 Interface Example
% LTC2378: 20-Bit, 1Msps, Low Power SAR ADC
%
% This program demonstrates how to communicate with the LTC2378-20 demo board 
% using Matlab.
% 
% Board setup is described in Demo Manual 1925 or 2135. Follow the procedure in 
% the manual, and verify operation with the PScope software. Once 
% operation is verified, exit PScope and run this script.
% 
% Demo board documentation:
% http://www.linear.com/demo/1925
% http://www.linear.com/demo/2135
% http://www.linear.com/product/LTC2378-20#demoboards
% 
% LTC2378-20 product page
% http://www.linear.com/product/LTC2378-20
%  
% REVISION HISTORY
% $Revision: 4272 $
% $Date: 2015-10-20 10:33:43 -0700 (Tue, 20 Oct 2015) $
%
% Copyright (c) 2015, Linear Technology Corp.(LTC)
% All rights reserved.
% 
% Redistribution and use in source and binary forms, with or without
% modification, are permitted provided that the following conditions are met:
% 
% 1. Redistributions of source code must retain the above copyright notice, 
%    this list of conditions and the following disclaimer.
% 2. Redistributions in binary form must reproduce the above copyright notice,
%    this list of conditions and the following disclaimer in the documentation
%    and/or other materials provided with the distribution.
% 
% THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
% ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
% WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
% DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
% ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
% (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
% LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
% ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
% (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
% SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
% 
% The views and conclusions contained in the software and documentation are those
% of the authors and should not be interpreted as representing official policies,
% either expressed or implied, of Linear Technology Corp.

% NOTE:
% 	ADD THE ABSOLUTE PATH TO "linear_lab_tools\matlab" FOLDER BEFORE RUNNING THE SCRIPT.
%   RUN "mex -setup" TO SET UP COMPILER AND CHOSE THE OPTION "Lcc-win32 C".

function Ltc2378Dc2135(arg1NumSamples, arg2Verbose, doDemo)
    if(~nargin)
        % Valid number of samples are 1024 to 65536 (powers of two)
        numAdcSamples = 64 * 1024;
        % Print extra information to console
        verbose = true;
        % Plot data to screen
        plotData = true;
        % Write data out to a text file
        writeToFile = true;
    else
        numAdcSamples = arg1NumSamples;
        verbose = arg2Verbose;
        plotData = doDemo;
        writeToFile = doDemo;
    end
      
    SAMPLE_BYTES = 4; % for 32-bit reads
        
    % Returns the object in the class constructor
    comm = LtcControllerComm();  
     
    deviceInfoList = comm.ListControllers(comm.TYPE_DC890, 1);
    
	% Open communication to the device
    cId = comm.Init(deviceInfoList);
    
    % find demo board with correct ID
    eepromIdSize = 50;
    fprintf('\nLooking for a DC890 with a DC2135A-A demoboard');
	
    for info = deviceInfoList
        % if strcmp(EEPROM_ID, comm.EepromReadString(cId, eepromIdSize))
        if(~isempty(strfind(comm.EepromReadString(cId, eepromIdSize), 'DC2135'))...
            || ~isempty(strfind(comm.EepromReadString(cId, eepromIdSize), 'DC1925')));
            break;
        end
		
        cId = comm.Cleanup(cId);
    end
    
    if(cId == 0)
        fprintf('\nDevice not found');
    else
        fprintf('\nDevice Found');
    end
     
    if (~comm.FpgaGetIsLoaded(cId, 'CMOS'))
       if(verbose)
            fprintf('\nLoading FPGA');
       end 
       comm.FpgaLoadFile(cId, 'CMOS');
    else
       if(verbose)
            fprintf('\nFPGA already loaded');
       end 
    end
    
    if(verbose)
        fprintf('\nStarting Data Collect');
    end 
 
    comm.DataSetHighByteFirst(cId);
    
    comm.DataSetCharacteristics(cId, true, SAMPLE_BYTES, true);
    comm.DataStartCollect(cId, numAdcSamples, comm.TRIGGER_NONE);
    
    for i = 1: 10
        isDone = comm.DataIsCollectDone(cId);
        if(isDone)
            break;
        end
        pause(0.2);
    end
    
    if(isDone ~= true)
        error('LtcControllerComm:HardwareError', 'Data collect timed out (missing clock?)');
    end
    
    if(verbose)
        fprintf('\nData Collect done');
    end
    
    comm.DC890Flush(cId);
    
    if(verbose)
        fprintf('\nReading data');
    end
    
    [rawData, numBytes] = comm.DataReceiveUint32Values(cId, numAdcSamples);
    
    if(verbose)
        fprintf('\nData Read done');
    end
       
    for i = 1 : numAdcSamples
        rawData(i) = bitand(rawData(i), 1048575);
    end
    data = zeros(1,numAdcSamples);
    for i = 1 : numAdcSamples
        if(rawData(i) > 524287)
            data(i) = int32(1048576 - rawData(i));
            data(i) = (-1) * int32(data(i));
        else
            data(i) = int32(rawData(i));
        end
    end


    if(writeToFile)
        if(verbose)
            fprintf('\nWriting data to file');
        end    

        fileID = fopen('data.txt','w');

        for i = 1:numAdcSamples
            fprintf(fileID,'%d\r\n', data(i));
        end

        fclose(fileID);
        fprintf('\nFile write done');
    end
    
	% Plot data if not running pattern check
    if(plotData == true)
        figure(1)
        plot(data)
        title('Time Domain Samples')
        
        adcAmplitude = 1048576.0 / 2.0;

        windowScale = (numAdcSamples) / sum(blackman(numAdcSamples));
        fprintf('\nWindow scaling factor: %d', windowScale);

        data_no_dc = data - mean(data);      % Remove DC to avoid leakage when windowing
        windowedData = data_no_dc .* (blackman(numAdcSamples))';
        windowedData = windowedData .* windowScale; 	% Apply Blackman window
        freqDomainData = fft(windowedData)/(numAdcSamples); % FFT
        freqDomainMagnitudeData = abs(freqDomainData); 		% Extract magnitude
        freqDomainMagnitudeDbData = 20 * log10(freqDomainMagnitudeData/adcAmplitude);
        
        figure(2)
        plot(freqDomainMagnitudeDbData)
        title('FFT')
                
    end
    fprintf('\nAll finished');
    
end