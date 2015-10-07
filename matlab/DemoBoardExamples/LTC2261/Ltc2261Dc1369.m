function Ltc2261Dc1369
    
    VERBOSE = true;
    plot_data = true;
    
    % set test_data_reg to one of these constants
    DATA_REAL = 0;
    DATA_ALL_ZEROS = 8;
    DATA_ALL_ONES = 24;
    DATA_CHECKERBOARD = 40;
    DATA_ALTERNATING = 56;
    %test_data_reg = DATA_CHECKERBOARD
    test_data_reg = DATA_REAL;
    
    NUM_ADC_SAMPLES = 64 * 1024;
    NUM_ADC_SAMPLES_PER_CH = NUM_ADC_SAMPLES / 2;
    NUM_ADC_SAMPLES_X2 = NUM_ADC_SAMPLES * 2;
    sample_bytes = 2;
    EEPROM_ID_SIZE = 48;
    
    % Returns the object in the class constructor
    comm = LtcControllerComm();  
    
    eeprom_id = 'LTC2261-14,D9002,DC1369A-A,YEE232T,DLVDS,-------';
    % find demo board with correct ID
    fprintf('Looking for a DC890 with a DC1369A demoboard');
    
    deviceInfoList = comm.ListControllers(comm.TYPE_DC890, 1);
    cId = comm.Init(deviceInfoList);
    
    for info = deviceInfoList
        if strcmp(eeprom_id, comm.EepromReadString(cId, EEPROM_ID_SIZE))
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
    
    if (test_data_reg == DATA_REAL)
        fprintf('\nSet to read real data');
    else
        fprintf('\nSet to generate test data');
    end
    
    comm.SpiSendByteAtAddress(cId, 0, 128);
    comm.SpiSendByteAtAddress(cId, 1, 0);
    comm.SpiSendByteAtAddress(cId, 2, 0);
    comm.SpiSendByteAtAddress(cId, 3, 113);
    comm.SpiSendByteAtAddress(cId, 4, test_data_reg);
    
    if (comm.FpgaGetIsLoaded(cId, 'DLVDS'))
       if(VERBOSE)
            fprintf('\nLoading FPGA');
       end 
       comm.FpgaLoadFile(cId, 'DLVDS');
    else
       if(VERBOSE)
            fprintf('\nFPGA already loaded');
       end 
    end
    
    if(VERBOSE)
        fprintf('\nStarting Data Collect');
    end 
    
    comm.DataSetCharacteristics(cId, true, sample_bytes, true);
    comm.DataStartCollect(cId, NUM_ADC_SAMPLES_X2, comm.TRIGGER_NONE);
    
    for i = 1: 10
        is_done = comm.DataIsCollectDone(cId);
        if(is_done)
            break;
        end
        pause(0.2);
    end
    
    if(is_done ~= true)
        comm.ErrorOnBadStatus(cId, 1);   %HardwareError
    end
    
    if(VERBOSE)
        fprintf('\nData Collect done');
    end
    
    comm.DC890Flush(cId);
    
    if(VERBOSE)
        fprintf('\nReading data');
    end
    
    [data, num_bytes] = comm.DataReceiveUint16Values(cId, NUM_ADC_SAMPLES_X2);
    
    if(VERBOSE)
        fprintf('\nData Read done');
    end
    
    % Split data into two channels
    data_ch1 = zeros(1, NUM_ADC_SAMPLES_PER_CH);
    
    for i = 1 : NUM_ADC_SAMPLES_PER_CH
        data_ch1(i) = bitand(data(2*i - 1), 16383);
    end
    
    if(VERBOSE)
        fprintf('\nWriting data to file');
    end    
    
    fileID = fopen('data.txt','w');
    
    for i = 1:size(data)
        if(mod(i, 2) == 0)
            fprintf(fileID,'%d\r\n', data(i));
        end
    end
    
    fclose(fileID);
    fprintf('\nFile write done');
    if(plot_data == true)
        figure(1)
        plot(data_ch1)
        title('Time Domain Data')

        adc_amplitude = 16384.0 / 2.0;

        windowscale = (NUM_ADC_SAMPLES/2) / sum(blackman(NUM_ADC_SAMPLES/2));
        fprintf('\nWindow scaling factor: %d', windowscale);

        windowed_data_ch1 = data_ch1' .* blackman(NUM_ADC_SAMPLES/2);
        windowed_data_ch1 = windowed_data_ch1 .* windowscale; % Apply Blackman window
        freq_domain_ch1 = fft(windowed_data_ch1)/(NUM_ADC_SAMPLES_PER_CH); % FFT
        freq_domain_magnitude_ch1 = abs(freq_domain_ch1); % Extract magnitude
        freq_domain_magnitude_db_ch1 = 20 * log10(freq_domain_magnitude_ch1/adc_amplitude);

        figure(2)
        plot(freq_domain_magnitude_db_ch1)
        title('Frequency Domain Data')  
    end
    fprintf('\nAll finished');
end