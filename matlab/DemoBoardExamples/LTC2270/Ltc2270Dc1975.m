function Ltc2270Dc1975
    
    % Print extra information to console
    VERBOSE = true;
    % Plot data to screen
    plot_data = true;
    % Write data out to a text file
    write_to_file = true;

    % set test_data_reg to one of these constants
    DATA_REAL = 0;
    DATA_ALL_ZEROS = 8;
    DATA_ALL_ONES = 24;
    DATA_CHECKERBOARD = 40;
    DATA_ALTERNATING = 56;
    % test_data_reg = DATA_ALTERNATING
    test_data_reg = DATA_REAL;

    NUM_ADC_SAMPLES = 64 * 1024;
    NUM_ADC_SAMPLES_PER_CH = NUM_ADC_SAMPLES / 2;
    SAMPLE_BYTES = 2;
    EEPROM_ID_SIZE = 48;
        
    % Returns the object in the class constructor
    comm = LtcControllerComm();  
    
    eeprom_id = 'LTC2270,D9002,DC1975A-A,YGG200T,CMOS,-----------';
    % find demo board with correct ID
    fprintf('Looking for a DC890 with a DC1975A-A demoboard');
    
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
    
    [data, num_bytes] = comm.DataReceiveUint16Values(cId, NUM_ADC_SAMPLES);
    
    if(VERBOSE)
        fprintf('\nData Read done');
    end
    
    % Split data into two channels
    data_ch1 = zeros(1, NUM_ADC_SAMPLES_PER_CH);
    data_ch2 = zeros(1, NUM_ADC_SAMPLES_PER_CH);
    
    for i = 1 : NUM_ADC_SAMPLES_PER_CH
        data_ch1(i) = bitand(data(2*i - 1), 65535);
        data_ch2(i) = bitand(data(2*i), 65535);
    end
    
    if(write_to_file)
        if(VERBOSE)
            fprintf('\nWriting data to file');
        end    

        fileID = fopen('data.txt','w');

        for i = 1:NUM_ADC_SAMPLES_PER_CH
            if(mod(i, 2) == 0)
                fprintf(fileID,'%d\t%d\r\n', data_ch1(i), data_ch2(i));
            end
        end

        fclose(fileID);
        fprintf('\nFile write done');
    end
    
    if(plot_data == true)
        figure(1)
        subplot(2, 1, 1)
        plot(data_ch1)
        title('CH0')
        subplot(2, 1, 2)
        plot(data_ch2)
        title('CH1')

        adc_amplitude = 65536.0 / 2.0;

        windowscale = (NUM_ADC_SAMPLES/2) / sum(blackman(NUM_ADC_SAMPLES/2));
        fprintf('\nWindow scaling factor: %d', windowscale);

        windowed_data_ch1 = data_ch1' .* blackman(NUM_ADC_SAMPLES/2);
        windowed_data_ch1 = windowed_data_ch1 .* windowscale; % Apply Blackman window
        freq_domain_ch1 = fft(windowed_data_ch1)/(NUM_ADC_SAMPLES_PER_CH); % FFT
        freq_domain_magnitude_ch1 = abs(freq_domain_ch1); % Extract magnitude
        freq_domain_magnitude_db_ch1 = 10 * log10(freq_domain_magnitude_ch1/adc_amplitude);
        
        windowed_data_ch2 = data_ch2' .* blackman(NUM_ADC_SAMPLES/2);
        windowed_data_ch2 = windowed_data_ch2 .* windowscale; % Apply Blackman window
        freq_domain_ch2 = fft(windowed_data_ch2)/(NUM_ADC_SAMPLES_PER_CH); % FFT
        freq_domain_magnitude_ch2 = abs(freq_domain_ch2); % Extract magnitude
        freq_domain_magnitude_db_ch2 = 10 * log10(freq_domain_magnitude_ch2/adc_amplitude);
        
        figure(2)
        subplot(2, 1, 1)
        plot(freq_domain_magnitude_db_ch1)
        title('CH0 FFT')
        subplot(2, 1, 2)
        plot(freq_domain_magnitude_db_ch2)
        title('CH1 FFT')
        
    end
    fprintf('\nAll finished');
    
end