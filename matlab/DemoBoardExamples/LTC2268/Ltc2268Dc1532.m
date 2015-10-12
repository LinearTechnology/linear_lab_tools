% LTC2268 - 14 bit

function Ltc2268Dc1532

    clear all;
    
    % LTC2268 Serial Programming Mode Registers
    RESET_REG = 0;
    POWER_DOWN_REG = 1;
    OUTPUT_MODE_REG = 2;
    TEST_PATTERN_MSB_REG = 3;
    TEST_PATTERN_LSB_REG = 4;
    
    % Print extra information to console
    verbose = true;
    % Plot data to screen
    plotData = true;
    % Write data out to a text file
    writeToFile = true;

    % Change this to collect real or test pattern data
    useTestData = true;
    % Change this to set the output when using the test pattern
    testDataValue = 10922;              % 14-bit data

    NUM_ADC_SAMPLES = 64 * 1024;        % WHY 64 * 1024 ????
    TOTAL_ADC_SAMPLES = 2 * NUM_ADC_SAMPLES; % Two channel part
    SAMPLE_BYTES = 2;
    
    % Returns the object in the class constructor
    comm = LtcControllerComm();  
    
    % find demo board with correct ID
    EEPROM_ID = '[0074 DEMO 10 DC1532A-A LTC2268-14 D2175]';
    eepromIdSize = length(EEPROM_ID);
    fprintf('\nLooking for a DC1371 with a DC1532A-A demoboard');
    
    deviceInfoList = comm.ListControllers(comm.TYPE_DC1371, 1);
	
	% Open communication to the device
    cId = comm.Init(deviceInfoList);
    
    for info = deviceInfoList
        if strcmp(EEPROM_ID(1 : eepromIdSize - 1), comm.EepromReadString(cId, eepromIdSize))
            break;
        end
        cId = comm.Cleanup(cId);
    end
    
    if(cId == 0)
        fprintf('\nDevice not found');
    else
        fprintf('\nDevice Found');
    end
        
    if (verbose)
        fprintf('\nConfiguring SPI registers');
    end
    
    if (useTestData == true)
        fprintf('\nSet to read real data');
    else
        fprintf('\nSet to generate test data');
    end

    if (useTestData)
        reg3 = int32(testDataValue);
        reg3 = int32(bitshift(testDataValue, -8));
        reg3 = bitor(bitand(reg3, 63), 128);
        reg4 = bitand(testDataValue, 255);
    else
        reg3 = 0;
        reg4 = 0;
    end
    
    % Software Reset
    comm.SpiSendByteAtAddress(cId, RESET_REG, 128); 
    % Enable Clock DCS, Disable Output Randomizer, Enable Binary Data Format
    comm.SpiSendByteAtAddress(cId, POWER_DOWN_REG, 0);  
    % Disable LVDS Internal Terminaion, Enable Digital Outputs, 2 Lanes, 16 - Bit
    comm.SpiSendByteAtAddress(cId, OUTPUT_MODE_REG, 0);
    % Enable Digital Output Teast Pattern, Bits D5:D0 holds TP13:TP8
    comm.SpiSendByteAtAddress(cId, TEST_PATTERN_MSB_REG, reg3);
    % Bits D7:D0 holds TP7:TP0
    comm.SpiSendByteAtAddress(cId, TEST_PATTERN_LSB_REG, reg4);
    
    if (comm.FpgaGetIsLoaded(cId, 'S2175'))
       if(verbose)
            fprintf('\nLoading FPGA');
       end 
       comm.FpgaLoadFile(cId, 'S2175');
    else
       if(verbose)
            fprintf('\nFPGA already loaded');
       end 
    end
    
    % demo-board specific information needed by the DC1371
    comm.DC1371SetDemoConfig(cId, 671088640)

    if(verbose)
        fprintf('\nStarting Data Collect');
    end 
    
    comm.DataStartCollect(cId, TOTAL_ADC_SAMPLES, comm.TRIGGER_NONE);
    
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
    
    if(verbose)
        fprintf('\nReading data');
    end
    
    [data, numBytes] = comm.DataReceiveUint16Values(cId, TOTAL_ADC_SAMPLES);
    
    if (nnz(data == 10922) == length(data))
        fprintf('\nGood data!!');
    else
        fprintf('Bad data!!');
    end
        
    if(verbose)
        fprintf('\nData Read done');
    end
    
    % Split data into two channels
    dataCh1 = zeros(1, TOTAL_ADC_SAMPLES/2);
    dataCh2 = zeros(1, TOTAL_ADC_SAMPLES/2);
    
    dataCh1(1 : TOTAL_ADC_SAMPLES/2) = data(1 : 2 : TOTAL_ADC_SAMPLES);
    dataCh2(1 : TOTAL_ADC_SAMPLES/2) = data(2 : 2 : TOTAL_ADC_SAMPLES);
    
    if(writeToFile)
        if(verbose)
            fprintf('\nWriting data to file');
        end    

        fileID = fopen('data.txt','w');

        for i = 1:NUM_ADC_SAMPLES
            fprintf(fileID,'%d\t%d\r\n', dataCh1(i), dataCh2(i));
        end

        fclose(fileID);
        fprintf('\nFile write done');
    end
    
    if(plotData == true)
        figure(1)
        subplot(2, 1, 1)
        plot(dataCh1)
        title('CH0')
        subplot(2, 1, 2)
        plot(dataCh2)
        title('CH1')

        adcAmplitude = 65536.0 / 2.0;

        windowScale = (NUM_ADC_SAMPLES/2) / sum(blackman(NUM_ADC_SAMPLES/2));
        fprintf('\nWindow scaling factor: %d', windowScale);

        windowedDataCh1 = dataCh1' .* blackman(NUM_ADC_SAMPLES);
        windowedDataCh1 = windowedDataCh1 .* windowScale; 	% Apply Blackman window
        freqDomainCh1 = fft(windowedDataCh1)/(NUM_ADC_SAMPLES); % FFT
        freqDomainMagnitudeCh1 = abs(freqDomainCh1); 		% Extract magnitude
        freqDomainMagnitudeDbCh1 = 10 * log10(freqDomainMagnitudeCh1/adcAmplitude);
        
        windowedDataCh2 = dataCh2' .* blackman(NUM_ADC_SAMPLES);
        windowedDataCh2 = windowedDataCh2 .* windowScale; 	% Apply Blackman window
        freqDomainCh2 = fft(windowedDataCh2)/(NUM_ADC_SAMPLES); % FFT
        freqDomainMagnitudeCh2 = abs(freqDomainCh2); 		% Extract magnitude
        freqDomainMagnitudeDbCh2 = 10 * log10(freqDomainMagnitudeCh2/adcAmplitude);
        
        figure(2)
        subplot(2, 1, 1)
        plot(freqDomainMagnitudeDbCh1)
        title('CH0 FFT')
        subplot(2, 1, 2)
        plot(freqDomainMagnitudeDbCh2)
        title('CH1 FFT')
        
    end
    fprintf('\nAll finished');
    
    
    
end
