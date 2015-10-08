function Ltc2270Dc1975
    
    % Print extra information to console
    VERBOSE = true;
    % Plot data to screen
    plotData = true;
    % Write data out to a text file
    writeToFile = true;

    % set testDataReg to one of these constants
    DATA_REAL = 0;
    DATA_ALL_ZEROS = 8;
    DATA_ALL_ONES = 24;
    DATA_CHECKERBOARD = 40;
    DATA_ALTERNATING = 56;
    % testDataReg = DATA_ALTERNATING
    testDataReg = DATA_REAL;

    NUM_ADC_SAMPLES = 64 * 1024;
    NUM_ADC_SAMPLES_PER_CH = NUM_ADC_SAMPLES / 2;
    SAMPLE_BYTES = 2;
    EEPROM_ID_SIZE = 48;
        
    % Returns the object in the class constructor
    comm = LtcControllerComm();  
    
    eepromId = 'LTC2270,D9002,DC1975A-A,YGG200T,CMOS,-----------';
    % find demo board with correct ID
    fprintf('Looking for a DC890 with a DC1975A-A demoboard');
    
    deviceInfoList = comm.ListControllers(comm.TYPE_DC890, 1);
    
    cId = comm.Init(deviceInfoList);
    
    for info = deviceInfoList
        if strcmp(eepromId, comm.EepromReadString(cId, EEPROM_ID_SIZE))
            break;
        end
        cId = comm.Cleanup(cId);
    end
    
    if(cId == 0)
        fprintf('\nDevice not found');
    else
        fprintf('\nDevice Found');
    end
    
    comm.DC890GpioSetByte(cId, 248);
    comm.DC890GpioSpiSetBits(cId, 3, 0, 1);
    
    if (VERBOSE)
        fprintf('Configuring SPI registers');
    end
    
    if (testDataReg == DATA_REAL)
        fprintf('\nSet to read real data');
    else
        fprintf('\nSet to generate test data');
    end
    
    comm.SpiSendByteAtAddress(cId, 0, 128);
    comm.SpiSendByteAtAddress(cId, 1, 0);
    comm.SpiSendByteAtAddress(cId, 2, 0);
    comm.SpiSendByteAtAddress(cId, 3, 113);
    comm.SpiSendByteAtAddress(cId, 4, testDataReg);
    
    if (comm.FpgaGetIsLoaded(cId, 'CMOS'))
       if(VERBOSE)
            fprintf('\nLoading FPGA');
       end 
       comm.FpgaLoadFile(cId, 'CMOS');
    else
       if(VERBOSE)
            fprintf('\nFPGA already loaded');
       end 
    end
    
    if(VERBOSE)
        fprintf('\nStarting Data Collect');
    end 
 
    comm.DataSetHighByteFirst(cId);
    
    comm.DataSetCharacteristics(cId, true, SAMPLE_BYTES, true);
    comm.DataStartCollect(cId, NUM_ADC_SAMPLES, comm.TRIGGER_NONE);
    
    for i = 1: 10
        isDone = comm.DataIsCollectDone(cId);
        if(isDone)
            break;
        end
        pause(0.2);
    end
    
    if(isDone ~= true)
        comm.ErrorOnBadStatus(cId, 1);   %HardwareError
    end
    
    if(VERBOSE)
        fprintf('\nData Collect done');
    end
    
    comm.DC890Flush(cId);
    
    if(VERBOSE)
        fprintf('\nReading data');
    end
    
    [data, numBytes] = comm.DataReceiveUint16Values(cId, NUM_ADC_SAMPLES);
    
    if(VERBOSE)
        fprintf('\nData Read done');
    end
    
    % Split data into two channels
    dataCh1 = zeros(1, NUM_ADC_SAMPLES_PER_CH);
    dataCh2 = zeros(1, NUM_ADC_SAMPLES_PER_CH);
    
    for i = 1 : NUM_ADC_SAMPLES_PER_CH
        dataCh1(i) = bitand(data(2*i - 1), 65535);
        dataCh2(i) = bitand(data(2*i), 65535);
    end
    
    if(writeToFile)
        if(VERBOSE)
            fprintf('\nWriting data to file');
        end    

        fileID = fopen('data.txt','w');

        for i = 1:NUM_ADC_SAMPLES_PER_CH
            if(mod(i, 2) == 0)
                fprintf(fileID,'%d\t%d\r\n', dataCh1(i), dataCh2(i));
            end
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

        windowedDataCh1 = data_ch1' .* blackman(NUM_ADC_SAMPLES/2);
        windowedDataCh1 = windowedDataCh1 .* windowScale; % Apply Blackman window
        freqDomainCh1 = fft(windowedDataCh1)/(NUM_ADC_SAMPLES_PER_CH); % FFT
        freqDomainMagnitudeCh1 = abs(freqDomainCh1); % Extract magnitude
        freqDomainMagnitudeDbCh1 = 10 * log10(freqDomainMagnitudeCh1/adcAmplitude);
        
        windowedDataCh2 = data_ch2' .* blackman(NUM_ADC_SAMPLES/2);
        windowedDataCh2 = windowedDataCh2 .* windowScale; % Apply Blackman window
        freqDomainCh2 = fft(windowedDataCh2)/(NUM_ADC_SAMPLES_PER_CH); % FFT
        freqDomainMagnitudeCh2 = abs(freqDomainCh2); % Extract magnitude
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