function Ltc2123Dc2226DualClockingSolution
    
    % Initialize script operation parameters
    bitFileId = 12; % Bitfile ID
    continuous = 0; % Run continuously, or just once
    runs = 0; % Initial run count
    runsWithErrors = 0; % Runs with PRBS errors (only valid if PRBStest is enabled)
    runsWithUncaughtErrors = 0; % Runs with errors that did NOT indicate SYNC~ assertion during capture

    doReset = true; % Reset FPGA once (not necessary to reset between data loads)
    initializeAdcs = 1; % Initialize ADC registers (only need to do on first run)
    initializeClocks = 1; % Initialize onboard clocks (only need to do on first run)
    initializeCore = 1; % Initialize JEDEC core in FPGA (only need to do on first run)

    verbose = 1; % Print out extra debug information
    plotData = 1; % Plot time and frequency data after capture

    patternCheck = 0; % greater than zero to Enable PRBS check, ADC data otherwise
    dumpPattern = 16; % Dump pattern analysis

    dumpData = 16; % Set to 1 and select an option below to dump to STDOUT:
    hexDump = 1; % Data dump format, can be either hex, decimal, or both
    dec = 0; % (if both, hex is first, followed by decimal)

    dumpPscopeData = 1; % Writes data to "pscope_data.csv", append to header to open in PScope

    % n = NumSamp64K; % Set number of samples here.
    memSize = 144;
    buffSize = 64 * 1024;
    
    % Common ADC / JEDEC Core / Clock parameter(s) 
    K = 16; %Frames per multiframe - Note that not all ADC / Clock combinations
    % support all values of K.

    % ADC configuration parameters
    %Configure other ADC modes here to override ADC data / PRBS selection
    forcePattern = 0; %Don't override ADC data / PRBS selection
    %forcePattern = 0x04; %PRBS
    %forcePattern = 0x06; %Test Samples test pattern
    %forcePattern = 0x07; %RPAT test pattern
    %forcePattern = 0x02; % K28.7 (minimum frequency)
    %forcePattern = 0x03; % D21.5 (maximum frequency)

    did0=239; % JESD204B device ID for ADC 0
    did1=171; % JESD204B device ID for ADC 1
    bid=12; % Bank ID (only low nibble is significant)
    modes=0;
    %modes=0x18; %Disable FAM/LAM
    %modes=0x1A; %Disable SYSREF

    if(patternCheck ~= 0)
        pattern0=4;
        pattern1=4;
    else
        pattern0=0;
        pattern1=0;
    end

    sleepTime = 0.5;
    
    if verbose
        fprintf('LTC2123 DC2226 dual clocking solution Interface Program\n');
    end


    % Returns the object in the class constructor
    lths = LtcControllerComm();

    % Import LTC2000 definitions and support functions
    [lt2k] = Ltc2123Constants(lths);
    
    descriptions = ['LTC UFO Board', 'LTC Communication Interface', 'LTC2000 Demoboard', 'LTC2000, DC2085A-A'];
    
    deviceInfoList = lths.ListControllers(lths.TYPE_HIGH_SPEED, 1);
    deviceInfo = [];
    for info = deviceInfoList
       if (strfind(descriptions, info.description))
           deviceInfo = info;
       end
    end

    if isempty(deviceInfo)
        error('TestLtcHighSpeedComm:noDevice', 'No LTC2123 demo board detected');
    end

    fprintf('Found LTC2123 demo board:\n');
    fprintf('Description: %s\n', deviceInfo.description);
    fprintf('Serial Number: %s\n', deviceInfo.serialNumber);

    % init a device and get an id
    cId = lths.Init(deviceInfo);
    
    while((runs < 1 || continuous == true) && runsWithErrors < 100000)
        
        runs = runs + 1;
        fprintf('LTC2123 Interface Program');
        fprintf('Run number: %s', runs');
        fprintf('\nRuns with errors: %s\n', runsWithErrors');
        if (runsWithUncaughtErrors > 0)
            fprintf('***\n***\n***\n*** UNCAUGHT error count: %s !\n***\n***\n***\n',runsWithUncaughtErrors);
        end
        
        lths.HsSetBitMode(cId, lths.HS_BIT_MODE_MPSSE);
        if doReset
            lths.HsFpgaToggleReset(cId);
        end

        fprintf('FPGA ID is %x\n', lths.HsFpgaReadDataAtAddress(cId, lt2k.ID_REG));
        
%         if(verbose != 0):
%             #print "FPGA Load ID: 0x{:04X}".format(id)
%             bitfile_id_warning(bitfile_id, id)
        
        if(initializeAdcs)
            LoadLtc212x(lths, 0, verbose, dId0, bankId, LIU, K, modes, 1, pattern0);
            LoadLtc212x(lths, 1, verbose, dId1, bankId, LIU, K, modes, 1, pattern1);
            initializeAdcs = 0;
        end
        
        if(initializeClocks)
            InitializeDC2226Version2Clocks250(lths, verbose);
            initializeClocks = 0;
        end
        
        lths.HsFpgaWriteDataAtAddress(cId, lt2k.CAPTURE_RESET_REG, 1);  % Reset
        
        if(verbose)
            fprintf('Reading Clock Status register; should be 0x16 (or at least 0x04 bit set)');
            fprintf('Register 6   (Clock status) is %x\n', lths.HsFpgaReadDataAtAddress(cId, lt2k.CLOCK_STATUS_REG));
            pause(sleepTime);
        end
        
        if(initializeCore)
            if(verbose)
                fprintf('Configuring JESD204B core!!');
            end
            write_jesd204b_reg(lths, 8, 0, 0, 0, 1);  % Enable ILA
            write_jesd204b_reg(lths, 12, 0, 0, 0, 0);  % Scrambling - 0 to disable, 1 to enable
            write_jesd204b_reg(lths, 16, 0, 0, 0, 1);  %  Only respond to first SYSREF (Subclass 1 only)
            write_jesd204b_reg(lths, 24, 0, 0, 0, 0);  %  Normal operation (no test modes enabled)
            write_jesd204b_reg(lths, 32, 0, 0, 0, 1);  %  2 octets per frame
            write_jesd204b_reg(lths, 36, 0, 0, 0, K-1);   %  Frames per multiframe, 1 to 32 for V6 core
            write_jesd204b_reg(lths, 40, 0, 0, 0, LIU-1); %  Lanes in use - program with N-1
            write_jesd204b_reg(lths, 44, 0, 0, 0, 0);  %  Subclass 0
            write_jesd204b_reg(lths, 48, 0, 0, 0, 0);  %  RX buffer delay = 0
            write_jesd204b_reg(lths, 52, 0, 0, 0, 0);  %  Disable error counters, error reporting by SYNC~
            write_jesd204b_reg(lths, 4, 0, 0, 0, 1);  %  Reset core
        end
        
        if(VERBOSE)
            fprintf('\nCapturing data and resetting...');
        end
        
        channelData = Capture4(lths, memSize, buffSize, dumpData, dumpPscopeData, VERBOSE, data);
        errorCount = 0;
        if(patternCheck ~= 0)
            errorCount = PatternChecker(channelData.dataCh0, channelData.nSampsPerChannel, dumppattern);
            errorCount = errorCount + PatternChecker(channelData.dataCh1, channelData.nSampsPerChannel, dumppattern);
            errorCount = errorCount + PatternChecker(channelData.dataCh2, channelData.nSampsPerChannel, dumppattern);
            errorCount = errorCount + PatternChecker(channelData.dataCh3, channelData.nSampsPerChannel, dumppattern);
        end

        if(errorCount ~= 0)
            outFile = fopen('LTC2123_python_error_log.txt','a');
            fprintf(outFile,'Caught %d errors on run %d\n', errorCount, runs);
            fclose(outFile);
            
            runsWithErrors = runsWithErrors + 1;
            if (channelData.syncErr == false)
                 runsWithUncaughtErrors = runsWithUncaughtErrors + 1;
            end
            fprintf('Error counts: %d', errorCount);
        end
        
        % Plot data if not running pattern check
        if((plotData == true) && (patternCheck == false))
            figure
            subplot(4, 1, 1)
            plot(dataCh0)
            title('CH0')
            subplot(4, 1, 2)
            plot(dataCh1)
            title('CH1')
            subplot(4, 1, 3)
            plot(dataCh2)
            title('CH2')
            subplot(4, 1, 4)
            plot(dataCh3)
            title('CH3')

            dataCh0 = dataCh0 - mean(dataCh0);
            dataCh0 = dataCh0' .* blackman(buffSize/2); % Apply Blackman window
            freqDomainCh0 = fft(dataCh0)/(buffSize/2); % FFT
            freqDomainMagnitudeCh0 = abs(freqDomainCh0); % Extract magnitude
            freqDomainMagnitudeDbCh0 = 20 * log10(freqDomainMagnitudeCh0/(buffSize/2));

            dataCh1 = dataCh1 - mean(dataCh1);
            dataCh1 = dataCh1' .* blackman(buffSize/2); % Apply Blackman window
            freqDomainCh1 = fft(dataCh1)/(buffSize/2); % FFT
            freqDomainMagnitudeCh1 = abs(freqDomainCh1); % Extract magnitude
            freqDomainMagnitudeDbCh1 = 20 * log10(freqDomainMagnitudeCh1/(buffSize/2));
            
            dataCh2 = dataCh2 - mean(dataCh2);
            dataCh2 = dataCh2' .* blackman(buffSize/2); % Apply Blackman window
            freqDomainCh2 = fft(dataCh2)/(buffSize/2); % FFT
            freqDomainMagnitudeCh2 = abs(freqDomainCh2); % Extract magnitude
            freqDomainMagnitudeDbCh2 = 20 * log10(freqDomainMagnitudeCh2/(buffSize/2));
            
            dataCh3 = dataCh3 - mean(dataCh3);
            dataCh3 = dataCh3' .* blackman(buffSize/2); % Apply Blackman window
            freqDomainCh3 = fft(dataCh3)/(buffSize/2); % FFT
            freqDomainMagnitudeCh3 = abs(freqDomainCh3); % Extract magnitude
            freqDomainMagnitudeDbCh3 = 20 * log10(freqDomainMagnitudeCh3/(buffSize/2));

            figure
            subplot(4,1,1)
            plot(freqDomainMagnitudeDbCh0)
            title('CH0 FFT')
            subplot(4,1,2)
            plot(freqDomainMagnitudeDbCh1)
            title('CH1 FFT')
            subplot(4,1,3)
            plot(freqDomainMagnitudeDbCh2)
            title('CH2 FFT')
            subplot(4,1,4)
            plot(freqDomainMagnitudeDbCh3)
            title('CH3 FFT')
        end
        
        if(verbose)
            ReadXilinxCoreConfig(lths, verbose);
            ReadXilinxCoreIlas(lths, verbose, 0);
            ReadXilinxCoreIlas(lths, verbose, 1);
            ReadXilinxCoreIlas(lths, verbose, 2);
            ReadXilinxCoreIlas(lths, verbose, 3);
        end
    end
    
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    %%%    FUNCTION DEFINITIONS    
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    
    function InitializeDC2226Version2Clocks250(device, verbose)
        if(verbose)
            fprintf('Configuring clock generators over SPI:');
        end
        device.HsSetBitMode(cId, device.HS_BIT_MODE_MPSSE);
        fprintf('Configuring LTC6954 (REF distribution)');
        device.HsFpgaWriteDataAtAddress(cId, 0, 0);
        device.HsFpgaWriteDataAtAddress(cId, 2, 128);   % 6951-1 delay
        device.HsFpgaWriteDataAtAddress(cId, 4, 1);     % 6951-1 divider
        device.HsFpgaWriteDataAtAddress(cId, 6, 128);   % 6951-2 delay
        device.HsFpgaWriteDataAtAddress(cId, 8, 1);     % 6951-2 divider
        device.HsFpgaWriteDataAtAddress(cId, 10, 192);  % sync delay & CMSINV
        device.HsFpgaWriteDataAtAddress(cId, 12, 1);    % sync divider
        device.HsFpgaWriteDataAtAddress(cId, 14, 33);
        
        fprintf('Configuring U10 (LTC6951) cp');
        % LTC6951config
        device.HsFpgaWriteDataAtAddress(cId, lt2k.SPI_CONFIG_REG, 2);
        device.SpiSendByteAtAddress(cId, 0, 5);
        device.SpiSendByteAtAddress(cId, 2, 186);
        device.SpiSendByteAtAddress(cId, 4, 0);
        device.SpiSendByteAtAddress(cId, 6, 124);
        device.SpiSendByteAtAddress(cId, 8, 163);
        device.SpiSendByteAtAddress(cId, 10, 8);
        device.SpiSendByteAtAddress(cId, 12, 5);    % 5 for 200, 6 for 300. VCO=2GHz.
        device.SpiSendByteAtAddress(cId, 14, 7);
        device.SpiSendByteAtAddress(cId, 16, 1);
        device.SpiSendByteAtAddress(cId, 18, 19);
        device.SpiSendByteAtAddress(cId, 20, 192);
        device.SpiSendByteAtAddress(cId, 22, 155);  % ADC SYSREF 2 div, 
        device.SpiSendByteAtAddress(cId, 24, 22);   % ADC SYSREF 2 delay, - 16 for 250, 1E f0r 300
        device.SpiSendByteAtAddress(cId, 26, 149);   % FPGA CLK div, 0x95 for half of 250
        device.SpiSendByteAtAddress(cId, 28, 22);   % FPGA CLK div,  0x97 for 1/4 of 250...
        device.SpiSendByteAtAddress(cId, 30, 149);   % FPGA CLK delay, 16 for 250, 1E for 300
        device.SpiSendByteAtAddress(cId, 32, 22);   % ADC CLK 2 div,
        device.SpiSendByteAtAddress(cId, 34, 48);   % ADC CLK 2 delay ,16 for 250, 1E for 300
        device.SpiSendByteAtAddress(cId, 36, 0);
        device.SpiSendByteAtAddress(cId, 38, 17);
        device.SpiSendByteAtAddress(cId, 4, 1);     % calibrate after writing all registers
        
        fprintf('Configuring U13 (LTC6951) cp');
        
        device.HsFpgaWriteDataAtAddress(cId, lt2k.SPI_CONFIG_REG, 3);
        device.SpiSendByteAtAddress(cId, 0, 5) 
        device.SpiSendByteAtAddress(cId, 2, 186) 
        device.SpiSendByteAtAddress(cId, 4, 0) 
        device.SpiSendByteAtAddress(cId, 6, 124) 
        device.SpiSendByteAtAddress(cId, 8, 163) 
        device.SpiSendByteAtAddress(cId, 10, 8) 
        device.SpiSendByteAtAddress(cId, 12, 5) % 5 for 250, 6 for 300
        device.SpiSendByteAtAddress(cId, 14, 7) 
        device.SpiSendByteAtAddress(cId, 16, 1) 
        device.SpiSendByteAtAddress(cId, 18, 19) 
        device.SpiSendByteAtAddress(cId, 20, 192) 
        device.SpiSendByteAtAddress(cId, 22, 155) % FPGA SYSREF div, 
        device.SpiSendByteAtAddress(cId, 24, 22) % FPGA SYSREF delay, 16 for 250, 1E f0r 300
        device.SpiSendByteAtAddress(cId, 26, 149) % ADC CLK 1 div,
        device.SpiSendByteAtAddress(cId, 28, 22) % ADC CLK 1 delay, 16 for 250, 1E for 300
        device.SpiSendByteAtAddress(cId, 30, 149) % ADC SYSREF 1 div,
        device.SpiSendByteAtAddress(cId, 32, 22) % ADC SYSREF 1 delay, 16 for 250, 1E for 300
        device.SpiSendByteAtAddress(cId, 34, 48) 
        device.SpiSendByteAtAddress(cId, 36, 0) 
        device.SpiSendByteAtAddress(cId, 38, 17) 
        device.SpiSendByteAtAddress(cId, 4, 1) % calibrate after writing all registers
        
        fprintf('toggle SYNC cp\n');
        pause(sleepTime);
        device.HsFpgaWriteDataAtAddress(cId, lt2k.SPI_CONFIG_REG, 8);
        fprintf('sync high');
        pause(sleepTime);
        fprintf('sync low');
        device.HsFpgaWriteData(0)
        pause(sleepTime);

    end   


end