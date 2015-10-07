function Ltc2268Dc1532
    clear all;
    % Print extra information to console
    verbose = true;
    % Plot data to screen
    plot_data = true;
    %Write data out to a text file
    write_to_file = true;

    % change this to collect real or test pattern data
    use_test_data = true;
    % change this to set the output when using the test pattern
    test_data_value = 10922;

    NUM_ADC_SAMPLES = 64 * 1024;
    TOTAL_ADC_SAMPLES = 2 * NUM_ADC_SAMPLES; % two channel part
    SAMPLE_BYTES = 2;
    EEPROM_ID_SIZE = 15;
    
    % Returns the object in the class constructor
    comm = LtcControllerComm();  
    
    % find demo board with correct ID
    eeprom_id = '[0074 DEMO 10 DC1532A-A LTC2268-14 D2175';

    % find demo board with correct ID
    fprintf('Looking for a DC1371 with a DC1532A-A demoboard');
    
    deviceInfoList = comm.ListControllers(comm.TYPE_DC1371, 1);
    cId = comm.Init(deviceInfoList);
    
    for info = deviceInfoList
        if strcmp(eeprom_id(1 : EEPROM_ID_SIZE - 1), comm.EepromReadString(cId, EEPROM_ID_SIZE))
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
        fprintf('Configuring SPI registers');
    end
    
    if (use_test_data == true)
        fprintf('\nSet to read real data');
    else
        fprintf('\nSet to generate test data');
    end

    if (use_test_data)
        reg3 = int32(test_data_value);
        reg3 = int32(bitsra(test_data_value, 8));
        reg3 = bitor(bitand(reg3, 63), 128);
        reg4 = bitand(test_data_value, 255);
    else
        reg3 = 0;
        reg4 = 0;
    end
    
    comm.SpiSendByteAtAddress(cId, 0, 128);
    comm.SpiSendByteAtAddress(cId, 1, 0);
    comm.SpiSendByteAtAddress(cId, 2, 0);
    comm.SpiSendByteAtAddress(cId, 3, reg3);
    comm.SpiSendByteAtAddress(cId, 4, reg4);
    
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
        is_done = comm.DataIsCollectDone(cId);
        if(is_done)
            break;
        end
        pause(0.2);
    end
    
    if(is_done ~= true)
        error('LtcControllerComm:HardwareError', 'Data collect timed out (missing clock?)');
    end
    
    if(verbose)
        fprintf('\nData Collect done');
    end
    
    if(verbose)
        fprintf('\nReading data');
    end
    
    [data, num_bytes] = comm.DataReceiveUint16Values(cId, TOTAL_ADC_SAMPLES);
    
    if(verbose)
        fprintf('\nData Read done');
    end
    
    % Split data into two channels
    data_ch1 = zeros(1, TOTAL_ADC_SAMPLES/2);
    data_ch2 = zeros(1, TOTAL_ADC_SAMPLES/2);
    
    data_ch1(1 : TOTAL_ADC_SAMPLES/2) = data(1 : 2 : TOTAL_ADC_SAMPLES);
    data_ch2(1 : TOTAL_ADC_SAMPLES/2) = data(2 : 2 : TOTAL_ADC_SAMPLES);
    
    if(write_to_file)
        if(verbose)
            fprintf('\nWriting data to file');
        end    

        fileID = fopen('data.txt','w');

        for i = 1:NUM_ADC_SAMPLES
            fprintf(fileID,'%d\t%d\r\n', data_ch1(i), data_ch2(i));
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

        windowed_data_ch1 = data_ch1' .* blackman(NUM_ADC_SAMPLES);
        windowed_data_ch1 = windowed_data_ch1 .* windowscale; % Apply Blackman window
        freq_domain_ch1 = fft(windowed_data_ch1)/(NUM_ADC_SAMPLES); % FFT
        freq_domain_magnitude_ch1 = abs(freq_domain_ch1); % Extract magnitude
        freq_domain_magnitude_db_ch1 = 10 * log10(freq_domain_magnitude_ch1/adc_amplitude);
        
        windowed_data_ch2 = data_ch2' .* blackman(NUM_ADC_SAMPLES);
        windowed_data_ch2 = windowed_data_ch2 .* windowscale; % Apply Blackman window
        freq_domain_ch2 = fft(windowed_data_ch2)/(NUM_ADC_SAMPLES); % FFT
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
