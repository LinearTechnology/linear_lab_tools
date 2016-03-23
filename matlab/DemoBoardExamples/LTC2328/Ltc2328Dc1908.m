function Ltc2328Dc1908(arg1NumSamples, arg2Verbose, arg3DoDemo)
    if(~nargin)
        numAdcSamples = 32 * 1024;
        % Print extra information to console
        verbose = true;
        % Plot data to screen
        plotData = true;
        % Write data out to a text file
        writeToFile = true;
    else
        numAdcSamples = arg1NumSamples;
        verbose = arg2Verbose;
        plotData = arg3DoDemo;
        writeToFile = arg3DoDemo;
    end
    
    SAMPLE_BYTES = 3;
    EEPROM_ID_SIZE = 50;
  
    % Returns the object in the class constructor
    comm = LtcControllerComm();  
    
    % find demo board with correct ID
    EEPROM_ID = 'LTC2328-18,D2315,DC1908A-D,YII101Q,NONE,--------';
    eepromIdSize = length(EEPROM_ID);
    fprintf('Looking for a DC718 with a DC1826A demoboard');
 
    deviceInfoList = comm.ListControllers(comm.TYPE_DC718, 1);
    
	% Open communication to the device
    cId = comm.Init(deviceInfoList);
    
    for info = deviceInfoList
        % if strcmp(EEPROM_ID(1 : eepromIdSize - 1), comm.EepromReadString(cId, eepromIdSize))
		if(~isempty(strfind(comm.EepromReadString(cId, eepromIdSize), 'DC1908')))
            break;
        end
        cId = comm.Cleanup(cId);
    end
    
    if(cId == 0)
        fprintf('\nDevice not found');
    else
        fprintf('\nDevice Found');
    end

    if(verbose)
        fprintf('\nStarting Data Collect');
    end 
 
    comm.DataSetCharacteristics(cId, false, SAMPLE_BYTES, false);
    
    if(trigger == true)
        comm.DataStartCollect(cId, numAdcSamples, comm.TRIGGER_START_POSITIVE_EDGE);
        for i = 1: timeout
            isDone = comm.DataIsCollectDone(cId);
            if(isDone)
                break;
            end
            pause(1.0);
            fprintf('\nWaiting up to %d seconds... %d', timeout, i);
        end
    else
        comm.DataStartCollect(cId, numAdcSamples, comm.TRIGGER_NONE);
        for i = 1: 10
            isDone = comm.DataIsCollectDone(cId);
            if(isDone)
                break;
            end
            pause(0.2);
        end
    end
    
    if(isDone ~= true)
        comm.DataCancelCollect(cId);
        error('LtcControllerComm:HardwareError', 'Data collect timed out (missing clock?)');
    end
    
    if(verbose)
        fprintf('\nData Collect done');
    end
    
    if(verbose)
        fprintf('\nReading data');
    end

    dataBytes = comm.DataReceiveBytes(cId, numAdcSamples * SAMPLE_BYTES);
    
    if(verbose)
        fprintf('\nData read done, parsing data...');
    end
    
    data = zeros(1, numAdcSamples);
    for i = 1:numAdcSamples
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
            fprintf('\nWriting data to file');
        end    

        fileID = fopen('data.txt','w');

        for i = 1:numAdcSamples
            fprintf(fileID,'%d\r\n', data(i));
        end

        fclose(fileID);
        fprintf('\nFile write done');
    end
    
    if(plotData == true)
        figure(1)
        plot(data)
        title('Time Domain Data')

        adcAmplitude = 262144.0 / 2.0;

        windowScale = (numAdcSamples/2) / sum(blackman(numAdcSamples));
        fprintf('Window scaling factor: %d\n', windowScale);
        
        data = data - mean(data);
        windowedDataCh1 = data' .* blackman(numAdcSamples);
        windowedDataCh1 = windowedDataCh1 .* windowScale; % Apply Blackman window
        freqDomainCh1 = fft(windowedDataCh1)/(numAdcSamples); % FFT
        freqDomainMagnitudeCh1 = abs(freqDomainCh1); % Extract magnitude
        freqDomainMagnitudeDbCh1 = 20 * log10(freqDomainMagnitudeCh1/adcAmplitude);

        figure(2)
        plot(freqDomainMagnitudeDbCh1)
        title('Frequency Domain')
    end
    
end