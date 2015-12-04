% DC1826 / LTC2389 Interface Example
% LTC2389: 16/18-Bit, 2.5Msps SAR ADC with Pin-Configurable Analog Input Range and 96dB SNR
%
% This program demonstrates how to communicate with the LTC2389 demo board 
% using Matlab. Examples are provided for reading data captured by the ADC, 
% or test data generated by the ADC.
% 
% Board setup is described in Demo Manual 1532. Follow the procedure in 
% this manual, and verify operation with the PScope software. Once 
% operation is verified, exit PScope and run this script.
% 
% Demo board documentation:
% http://www.linear.com/demo/1826
% http://www.linear.com/product/LTC2389#demoboards
% 
% LTC2389 product page
% http://www.linear.com/product/LTC2389
% 
% REVISION HISTORY
% $Revision: 4260 $
% $Date: 2015-10-19 16:45:28 -0700 (Mon, 19 Oct 2015) $
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

function Ltc2389Dc1826(arg1NumSamples, arg2Verbose, arg3DoDemo, arg4Trigger, arg5Timeout)
    if(~nargin)
        numSamples = 32 * 1024;
        % Print extra information to console
        verbose = true;
        % Plot data to screen
        plotData = true;
        % Write data out to a text file
        writeToFile = true;
        trigger = false;
        timeOut = 15;
    else
        numSamples = arg1NumSamples;
        verbose = arg2Verbose;
        plotData = doDemo;
        writeToFile = arg3DoDemo;
        trigger = arg4Trigger;
        timeOut = arg5Timeout;
    end

    SAMPLE_BYTES = 3;
    
    % Returns the object in the class constructor
    comm = LtcControllerComm();  
    
    % find demo board with correct ID
    EEPROM_ID = 'LTC2389,D2389,DC1826A-A,YII101Q,NONE,-----------';
    eepromIdSize = length(EEPROM_ID);
    fprintf('Looking for a DC718 with a DC1826A demoboard\n');
    
    deviceInfoList = comm.ListControllers(comm.TYPE_DC718, 1);
	
	% Open communication to the device
    cId = comm.Init(deviceInfoList);
    
    for info = deviceInfoList
        % if strcmp(EEPROM_ID(1 : eepromIdSize - 1), comm.EepromReadString(cId, eepromIdSize))
		if(~isempty(strfind(comm.EepromReadString(cId, eepromIdSize), 'DC1826')))
            break;
        end
        cId = comm.Cleanup(cId);
    end
    
    if(cId == 0)
        fprintf('Device not found\n');
    else
        fprintf('Device Found\n');
    end
    
    if(verbose)
        fprintf('Starting data collect\n');
    end
    
    comm.DataSetCharacteristics(cId, false, SAMPLE_BYTES, false);
    
    if(trigger)
        comm.DataStartCollect(cId, numSamples, comm.TRIGGER_START_POSITIVE_EDGE);
        for i = 1:timeOut
            isDone = comm.DataIsCollectDone(cId);
            if(isDone)
                break;
            end
            pause(0.1);
            fprintf('Waiting up to %d seconds...%d\n', timeOut, i);
        end
    else
        comm.DataStartCollect(cId, numSamples, comm.TRIGGER_NONE);
        for i = 1:10
            isDone = comm.DataIsCollectDone();
            if(isDone)
                break;
            end
            pause(0.2);
        end
    end
    
    if(isDone ~= true)
        error('LtcControllerComm:HardwareError', ...
            'Data collect timed out (missing clock?)\n');
    end
    
    if(verbose)
        fprintf('Data collect done\n.');
        fprintf('Reading data\n');
    end
    dataBytes = comm.DataReceiveBytes(cId, numSamples * SAMPLE_BYTES);
    if(verbose)
        fprintf('Data read done, parsing done...\n');
    end

    data = zeros(1, numSamples);
    for i = 1:numSamples
        d1 = bitand(uint32(dataBytes(i * 3 - 2)), 255) * 65536;
        d1 = bitshift(d1, -16);
        d1 = bitand(d1, 255);
        d1 = bitshift(d1, 16);
        % d1 = bitand((uint8(dataBytes(i * 3 - 2)) * 65536), 16711680);
        d2 = bitand(uint32(dataBytes(i * 3 - 1)), 255) * 256;
        d2 = bitshift(d2, -8);
        d2 = bitand(d2, 255);
        d2 = bitshift(d2, 8);
        % d2 = bitand((uint8(dataBytes(i * 3 - 1)) * 256), 65280);
        d3 = bitand(uint32(dataBytes(i * 3)), 255);
        data(i) = bitor(bitor(d1, d2), d3);
        if(data(i) > 131072)
            data(i) = data(i) - 262144;
        end
    end

    if(writeToFile)
        if(verbose)
            fprintf('Writing data to file\n');
        end    

        fileID = fopen('data.txt','w');

        for i = 1:numSamples
            fprintf(fileID,'%d\n', data(i));
        end

        fclose(fileID);
        fprintf('File write done\n');
    end
    
    if(plotData)
        figure(1)
        plot(data)
        title('Time Domain Data')

        adcAmplitude = 262144.0 / 2.0;

        windowScale = (numSamples) / sum(blackman(numSamples));
        fprintf('Window scaling factor: %d\n', windowScale);
        
        data = data - mean(data);
        windowedData = data' .* blackman(numSamples);
        windowedData = windowedData .* windowScale; % Apply Blackman window
        freqDomain = fft(windowedData)/(numSamples); % FFT
        freqDomainMagnitude = abs(freqDomain); % Extract magnitude
        freqDomainMagnitudeDb = 20 * log10(freqDomainMagnitude/adcAmplitude);

        figure(2)
        plot(freqDomainMagnitudeDb)
        title('Frequency Domain')
    end
end