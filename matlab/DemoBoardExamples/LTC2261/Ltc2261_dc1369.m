function Ltc2261_dc1369
    
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
    
    % Returns the object in the class constructor
    comm = LtcControllerComm();
    
    % find demo board with correct ID
    eeprom_id = 'LTC2261-14,D9002,DC1369A-A,YEE232T,DLVDS,-------';
    deviceInfoList = comm.ListControllers(comm.TYPE_DC890, 2);

    deviceInfo = [];
    for info = deviceInfoList
        deviceInfo = info;
        % init a device and get an id
        cId = comm.Init(deviceInfo);
    %     if strcmp(eeprom_id, comm.EepromReadString(cId, (length(eeprom_id) - 1)))
    %         break;
    %     end
    %     cId = comm.Cleanup(cId);
        if strcmp(info.description, 'DC890 FastDAACS CNTLR')
            deviceInfo = info;
        end

    end

    if isempty(deviceInfo)
        error('TestLtcHighSpeedComm:noDevice', 'No LTC2261 demo board detected');
    end

    comm.DC890GpioSetByte(cId, 248);
    comm.DC890GpioSpiSetBits(cId, 3, 0, 1);
    
    if (VERBOSE)
        fprintf('Configuring SPI registers\n');
    end
    
    if (test_data_reg == DATA_REAL)
        fprintf('Set to read real data');
    else
        fprintf('Set to generate test data');
    end
    
    comm.SpiSendByteAtAddress(cId, 0, 128);
    comm.SpiSendByteAtAddress(cId, 1, 0);
    comm.SpiSendByteAtAddress(cId, 2, 0);
    comm.SpiSendByteAtAddress(cId, 3, 113);
    comm.SpiSendByteAtAddress(cId, 4, test_data_reg);
    
    
    %%%%%%%%%%%% load fpga file
    
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
        fprintf('Data Collect done');
    end
    
    comm.DC890Flush(cId);
    
    if(VERBOSE)
        fprintf('Reading data');
    end
    
    [data, num_bytes] = comm.DataReceiveUint16Values(NUM_ADC_SAMPLES_X2);
    
    if(VERBOSE)
        fprintf('Data Read done');
    end
    
    % Split data into two channels
    data_ch1 = zeros(1, NUM_ADC_SAMPLES_PER_CH);
    
    for i = 1 : NUM_ADC_SAMPLES_PER_CH
        data_ch1(i) = bitand(data(2*i), 16383);
    end
    
    if(VERBOSE)
        fprintf('Writing data to file');
    end    
    
    %%%%%%%%%%%%%% write to file
    
    if(plot_data == true)
            figure(1)
            plot(data_ch1)
            title('Time Domain Data')
            
            adc_amplitude = 16384.0 / 2.0;
            
            windowscale = (NUM_ADC_SAMPLES/2) / sum(blackman(NUM_ADC_SAMPLES/2));
            fprintf('Window scaling factor: %d', windowscale);
            
            windowed_data_ch1 = data_ch1 * blackman(NUM_ADC_SAMPLES/2) * windowscale; % Apply Blackman window
            freq_domain_ch1 = fft(windowed_data_ch1)/(NUM_ADC_SAMPLES_PER_CH); % FFT
            freq_domain_magnitude_ch1 = abs(freq_domain_ch1); % Extract magnitude
            freq_domain_magnitude_db_ch1 = 20 * log10(freq_domain_magnitude_ch1/adc_amplitude);

            figure(2)
            plot(freq_domain_magnitude_db_ch1)
            title('Frequency Domain Data')
            
    end
    fprintf('All finished');
end