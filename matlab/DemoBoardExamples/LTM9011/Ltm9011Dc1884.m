function Ltm9011Dc1884(arg1NumSamples, arg2Verbose, arg3DoDemo)
    if(~nargin)
        numAdcSamples = 8 * 1024;
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
    
    % LTM9011 Serial Programming Mode Registers
    RESET_REG = 0;
    POWER_DOWN_REG = 1;
    OUTPUT_MODE_REG = 2;
    TEST_PATTERN_MSB_REG = 3;
    TEST_PATTERN_LSB_REG = 4;
    
    totalAdcSamples = 8 * numAdcSamples;    % two channel part
    %change this to collect real or test pattern data
    useTestData = False;
    % change this to set the output when using the test pattern
    testDataValue = 10922;
    
    % Returns the object in the class constructor
    comm = LtcControllerComm();  
    
    % find demo board with correct ID
    EEPROM_ID = '[0071 DEMO 10 DC1884A-F LTM9006 D9011\r\n + \
    ADC 14 14 8 0000 00 00 00 00\r\n + \
    DBFLG 0003 28 32 10 00\r\n + \
    FPGA S9011 T4\r\n + \
    A94E]';
    eepromIdSize = length(EEPROM_ID);
    fprintf('Looking for a DC1371 with a DC1884 demoboard');
 
    deviceInfoList = comm.ListControllers(comm.TYPE_DC1371, 1);
    
	% Open communication to the device
    cId = comm.Init(deviceInfoList);
    
    for info = deviceInfoList
        % if strcmp(EEPROM_ID(1 : eepromIdSize - 1), comm.EepromReadString(cId, eepromIdSize))
		if ~isempty(strfind(comm.EepromReadString(cId, eepromIdSize), 'DC1884'))
            fprintf('\nFound a DC1884-x demoboard');
            break;
        end
        if ~isempty(strfind(comm.EepromReadString(cId, eepromIdSize), 'DC1751'))
            fprintf('\nFound a DC1751-x demoboard');
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
        fprintf('\nConfiguring SPI registers');
    end
    
    if (useTestData)
        if(verbose)
            fprintf('\nSet to generate test data');
        end
        reg3 = int32(testDataValue);
        reg3 = int32(bitshift(testDataValue, -8));
        reg3 = bitor(bitand(reg3, 63), 128);
        reg4 = bitand(testDataValue, 255);
    else
        if(verbose)
            fprintf('\nSet to read real data');
        end
        reg3 = 0;
        reg4 = 0;
    end
    
    % First bank of 4 channels
    comm.DC1371SpiChooseChipSelect(cId, 1); 
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
    
    % Second bank of 4 channels
    comm.DC1371SpiChooseChipSelect(cId, 2); 
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
    
    if (comm.FpgaGetIsLoaded(cId, 'S9011'))
       if(verbose)
            fprintf('Loading FPGA\n');
       end 
       comm.FpgaLoadFile(cId, 'S9011');
    else
       if(verbose)
            fprintf('FPGA already loaded\n');
       end 
    end
    
    % demo-board specific information needed by the DC1371 (0x28321000)
    comm.DC1371SetDemoConfig(cId, 674369536)

    if(verbose)
        fprintf('Starting Data Collect\n');
    end 
    
    comm.DataStartCollect(cId, totalAdcSamples, comm.TRIGGER_NONE);
    
    for i = 1: 10
        isDone = comm.DataIsCollectDone(cId);
        if(isDone)
            break;
        end
        pause(0.2);
    end
    
    if(isDone ~= true)
        error('LtcControllerComm:HardwareError', ...
            'Data collect timed out (missing clock?)');
    end
    
    if(verbose)
        fprintf('Data Collect done\n');
    end
    
    if(verbose)
        fprintf('Reading data\n');
    end
    
    [data, numBytes] = comm.DataReceiveUint16Values(cId, totalAdcSamples);
    
    if(verbose)
        fprintf('Data Read done\n');
    end
    
    % Split data into 8 channels
    dataCh1 = zeros(1, numAdcSamples);
    dataCh2 = zeros(1, numAdcSamples);
    dataCh3 = zeros(1, numAdcSamples);
    dataCh4 = zeros(1, numAdcSamples);
    dataCh5 = zeros(1, numAdcSamples);
    dataCh6 = zeros(1, numAdcSamples);
    dataCh7 = zeros(1, numAdcSamples);
    dataCh8 = zeros(1, numAdcSamples);
    
    dataCh1(1 : numAdcSamples) = data(1 : 8 : totalAdcSamples);
    dataCh2(1 : numAdcSamples) = data(2 : 2 : totalAdcSamples);
    dataCh3(1 : numAdcSamples) = data(3 : 8 : totalAdcSamples);
    dataCh4(1 : numAdcSamples) = data(4 : 8 : totalAdcSamples);
    dataCh5(1 : numAdcSamples) = data(5 : 8 : totalAdcSamples);
    dataCh6(1 : numAdcSamples) = data(6 : 8 : totalAdcSamples);
    dataCh7(1 : numAdcSamples) = data(7 : 8 : totalAdcSamples);
    dataCh8(1 : numAdcSamples) = data(8 : 8 : totalAdcSamples);
    
    if(writeToFile)
        if(verbose)
            fprintf('Writing data to file\n');
        end    

        fileID = fopen('data.txt','w');

        for i = 1:numAdcSamples
            fprintf(fileID,'%d, %d, %d, %d, %d, %d, %d, %d\n', ...
                dataCh1(i), dataCh2(i), dataCh3(i), dataCh4(i), ...
                dataCh5(i), dataCh6(i), dataCh7(i), dataCh8(i));
        end

        fclose(fileID);
        fprintf('File write done\n');
    end
    
    if(plotData == true)
        figure(1)
        subplot(2, 4, 1)
        plot(dataCh1)
        title('CH1')
        
        subplot(2, 4, 2)
        plot(dataCh2)
        title('CH2')
        
        subplot(2, 4, 3)
        plot(dataCh3)
        title('CH3')
        
        subplot(2, 4, 4)
        plot(dataCh4)
        title('CH4')
        
        subplot(2, 4, 5)
        plot(dataCh5)
        title('CH5')
        
        subplot(2, 4, 6)
        plot(dataCh6)
        title('CH6')
        
        subplot(2, 4, 7)
        plot(dataCh7)
        title('CH7')
        
        subplot(2, 4, 8)
        plot(dataCh8)
        title('CH8')
        

        adcAmplitude = 16384.0 / 2.0;

        windowScale = (numAdcSamples) / sum(blackman(numAdcSamples));
        fprintf('Window scaling factor: %d\n', windowScale);

        dataCh1 = dataCh1 - mean(dataCh1);
        windowedDataCh1 = dataCh1' .* blackman(numAdcSamples);
        windowedDataCh1 = windowedDataCh1 .* windowScale; 	% Apply Blackman window
        freqDomainCh1 = fft(windowedDataCh1)/(numAdcSamples); % FFT
        freqDomainMagnitudeCh1 = abs(freqDomainCh1); 		% Extract magnitude
        freqDomainMagnitudeDbCh1 = 20 * log10(freqDomainMagnitudeCh1/adcAmplitude);
        
        dataCh2 = dataCh2 - mean(dataCh2);
        windowedDataCh2 = dataCh2' .* blackman(numAdcSamples);
        windowedDataCh2 = windowedDataCh2 .* windowScale; 	% Apply Blackman window
        freqDomainCh2 = fft(windowedDataCh2)/(numAdcSamples); % FFT
        freqDomainMagnitudeCh2 = abs(freqDomainCh2); 		% Extract magnitude
        freqDomainMagnitudeDbCh2 = 20 * log10(freqDomainMagnitudeCh2/adcAmplitude);
        
        dataCh3 = dataCh3 - mean(dataCh3);
        windowedDataCh3 = dataCh3' .* blackman(numAdcSamples);
        windowedDataCh3 = windowedDataCh3 .* windowScale; 	% Apply Blackman window
        freqDomainCh3 = fft(windowedDataCh3)/(numAdcSamples); % FFT
        freqDomainMagnitudeCh3 = abs(freqDomainCh3); 		% Extract magnitude
        freqDomainMagnitudeDbCh3 = 20 * log10(freqDomainMagnitudeCh3/adcAmplitude);
        
        dataCh4 = dataCh4 - mean(dataCh4);
        windowedDataCh4 = dataCh4' .* blackman(numAdcSamples);
        windowedDataCh4 = windowedDataCh4 .* windowScale; 	% Apply Blackman window
        freqDomainCh4 = fft(windowedDataCh4)/(numAdcSamples); % FFT
        freqDomainMagnitudeCh4 = abs(freqDomainCh4); 		% Extract magnitude
        freqDomainMagnitudeDbCh4 = 20 * log10(freqDomainMagnitudeCh4/adcAmplitude);
        
        dataCh5 = dataCh5 - mean(dataCh5);
        windowedDataCh5 = dataCh5' .* blackman(numAdcSamples);
        windowedDataCh5 = windowedDataCh5 .* windowScale; 	% Apply Blackman window
        freqDomainCh5 = fft(windowedDataCh5)/(numAdcSamples); % FFT
        freqDomainMagnitudeCh5 = abs(freqDomainCh5); 		% Extract magnitude
        freqDomainMagnitudeDbCh5 = 20 * log10(freqDomainMagnitudeCh5/adcAmplitude);
        
        dataCh6 = dataCh6 - mean(dataCh6);
        windowedDataCh6 = dataCh6' .* blackman(numAdcSamples);
        windowedDataCh6 = windowedDataCh6 .* windowScale; 	% Apply Blackman window
        freqDomainCh6 = fft(windowedDataCh6)/(numAdcSamples); % FFT
        freqDomainMagnitudeCh6 = abs(freqDomainCh6); 		% Extract magnitude
        freqDomainMagnitudeDbCh6 = 20 * log10(freqDomainMagnitudeCh6/adcAmplitude);
        
        dataCh7 = dataCh7 - mean(dataCh7);
        windowedDataCh7 = dataCh7' .* blackman(numAdcSamples);
        windowedDataCh7 = windowedDataCh7 .* windowScale; 	% Apply Blackman window
        freqDomainCh7 = fft(windowedDataCh7)/(numAdcSamples); % FFT
        freqDomainMagnitudeCh7 = abs(freqDomainCh7); 		% Extract magnitude
        freqDomainMagnitudeDbCh7 = 20 * log10(freqDomainMagnitudeCh7/adcAmplitude);
        
        dataCh8 = dataCh8 - mean(dataCh8);
        windowedDataCh8 = dataCh8' .* blackman(numAdcSamples);
        windowedDataCh8 = windowedDataCh8 .* windowScale; 	% Apply Blackman window
        freqDomainCh8 = fft(windowedDataCh8)/(numAdcSamples); % FFT
        freqDomainMagnitudeCh8 = abs(freqDomainCh8); 		% Extract magnitude
        freqDomainMagnitudeDbCh8 = 20 * log10(freqDomainMagnitudeCh8/adcAmplitude);
        
        figure(2)
        subplot(2, 4, 1)
        plot(freqDomainMagnitudeDbCh1)
        title('CH1 FFT')
        
        subplot(2, 4, 2)
        plot(freqDomainMagnitudeDbCh2)
        title('CH2 FFT')
        
        subplot(2, 4, 3)
        plot(freqDomainMagnitudeDbCh3)
        title('CH3 FFT')
        
        subplot(2, 4, 4)
        plot(freqDomainMagnitudeDbCh4)
        title('CH4 FFT')
        
        subplot(2, 4, 5)
        plot(freqDomainMagnitudeDbCh5)
        title('CH5 FFT')
        
        subplot(2, 4, 6)
        plot(freqDomainMagnitudeDbCh6)
        title('CH6 FFT')
        
        subplot(2, 4, 7)
        plot(freqDomainMagnitudeDbCh7)
        title('CH7 FFT')
        
        subplot(2, 4, 8)
        plot(freqDomainMagnitudeDbCh8)
        title('CH8 FFT')
        
    end
    fprintf('All finished\n');
    
end

    