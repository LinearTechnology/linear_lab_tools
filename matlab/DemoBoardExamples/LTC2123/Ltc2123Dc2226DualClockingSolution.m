function Ltc2123Dc2226DualClockingSolution
    
    % Initialize script operation parameters
    bitFileId = 192; % Bitfile ID
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

    LIU = 2;
    dId0 = 239; % JESD204B device ID for ADC 0
    dId1 = 171; % JESD204B device ID for ADC 1
    bankId = 12; % Bank ID (only low nibble is significant)
    modes = 0;
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
        fprintf('LTC2123 Interface Program\n');
        fprintf('Run number: %s\n', runs');
        fprintf('Runs with errors: %s\n', runsWithErrors');
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
            fprintf('Reading Clock Status register; should be 0x16 (or at least 0x04 bit set)\n');
            fprintf('Register 6   (Clock status) is %x\n', lths.HsFpgaReadDataAtAddress(cId, lt2k.CLOCK_STATUS_REG));
            pause(sleepTime);
        end
        
        if(initializeCore)
            if(verbose)
                fprintf('Configuring JESD204B core!!\n');
            end
            WriteJesd204bReg(lths, 8, 0, 0, 0, 1);  % Enable ILA
            WriteJesd204bReg(lths, 12, 0, 0, 0, 0);  % Scrambling - 0 to disable, 1 to enable
            WriteJesd204bReg(lths, 16, 0, 0, 0, 1);  %  Only respond to first SYSREF (Subclass 1 only)
            WriteJesd204bReg(lths, 24, 0, 0, 0, 0);  %  Normal operation (no test modes enabled)
            WriteJesd204bReg(lths, 32, 0, 0, 0, 1);  %  2 octets per frame
            WriteJesd204bReg(lths, 36, 0, 0, 0, K-1);   %  Frames per multiframe, 1 to 32 for V6 core
            WriteJesd204bReg(lths, 40, 0, 0, 0, LIU-1); %  Lanes in use - program with N-1
            WriteJesd204bReg(lths, 44, 0, 0, 0, 0);  %  Subclass 0
            WriteJesd204bReg(lths, 48, 0, 0, 0, 0);  %  RX buffer delay = 0
            WriteJesd204bReg(lths, 52, 0, 0, 0, 0);  %  Disable error counters, error reporting by SYNC~
            WriteJesd204bReg(lths, 4, 0, 0, 0, 1);  %  Reset core
        end
        
        if(verbose)
            fprintf('Capturing data and resetting...\n');
        end
        
        channelData = Capture4(lths, memSize, buffSize, dumpData, dumpPscopeData, verbose);
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
            fprintf('Configuring clock generators over SPI:\n');
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
        device.HsFpgaWriteData(cId, 0)
        pause(sleepTime);

    end   

    function SpiWrite(device, address, value)
        device.SpiSendByteAtAddress(cId, bitor(address, lt2k.SPI_WRITE), value);
    end

    function LoadLtc212x(device, csControl, verbose, dId, bankId, lanes, K, modes, subClass, pattern)
        if(verbose)
            fprintf('Configuring ADCs over SPI:');
        end
        device.HsFpgaWriteDataAtAddress(cId, lt2k.SPI_CONFIG_REG, csControl);
        SpiWrite(device, 3, dId); % Device ID to 0xAB
        SpiWrite(device, 4, bankId); % Bank ID to 0x01
        SpiWrite(device, 5, lanes-1); % 2 lane mode (default)
        SpiWrite(device, 6, K-1);
        SpiWrite(device, 7, modes); % Enable FAM, LAM
        SpiWrite(device, 8, subClass); % Subclass mode
        SpiWrite(device, 9, pattern); % PRBS test pattern
        SpiWrite(device, 10, 3); %  0x03 = 16mA CML current
    end 

    function ReadXilinxCoreConfig(device, verbose)
        fprintf('\n\nJEDEC core config registers:')  
        for i = 0 : 15
            reg = i*4;
            [byte3, byte2, byte1, byte0] = ReadJesd204bReg(device, reg);
            fprintf('\n%s : 0X %s %s %s %s', lt2k.JESD204B_XILINX_CONFIG_REG_NAMES{i + 1}, dec2hex(byte3, 2), dec2hex(byte2, 2), dec2hex(byte1, 2), dec2hex(byte0, 2));
        end
    end

    function ReadXilinxCoreIlas(device, verbose, lane)
        startreg = 2048 + lane * 64;
        fprintf('\n\nILAS and stuff for lane %d :', lane);
        for i = 0 : 12
            reg = startreg + i*4;
            [byte3, byte2, byte1, byte0] = ReadJesd204bReg(device, reg);
            fprintf('\n %s : 0X %s %s %s %s', lt2k.JESD204B_XILINX_LANE_REG_NAMES{i + 1}, dec2hex(byte3, 2), dec2hex(byte2, 2), dec2hex(byte1, 2), dec2hex(byte0, 2));
        end
    end

    % Adding support for V6 core, with true AXI access. Need to confirm that this doesn't break anything with V4 FPGA loads,
    % as we'd be writing to undefined registers.
    function [byte3, byte2, byte1, byte0] = ReadJesd204bReg(device, address)
        device.HsFpgaWriteDataAtAddress(cId, lt2k.JESD204B_R2INDEX_REG, bitshift(bitand(address,4032), -6));  % Upper 6 bits of AXI reg address
        device.HsFpgaWriteDataAtAddress(cId, lt2k.JESD204B_CHECK_REG, (bitor(bitshift(bitand(address, 63), 2), 2)));  % Lower 6 bits address of JESD204B Check Register
        
        if (bitand(device.HsFpgaReadData(cId), 1) == 0)
            error('Got bad FPGA status in read_jedec_reg');
        end
        
        byte3 = device.HsFpgaReadDataAtAddress(cId, lt2k.JESD204B_RB3_REG);
        byte2 = device.HsFpgaReadDataAtAddress(cId, lt2k.JESD204B_RB2_REG);
        byte1 = device.HsFpgaReadDataAtAddress(cId, lt2k.JESD204B_RB1_REG);
        byte0 = device.HsFpgaReadDataAtAddress(cId, lt2k.JESD204B_RB0_REG);        
    end

    % Adding support for V6 core, with true AXI access. Need to confirm that this 
    % doesn't break anything with V4 FPGA loads,
    % as we'd be writing to undefined registers.
    function WriteJesd204bReg(device, address, b3, b2, b1, b0)
        device.HsFpgaWriteDataAtAddress(cId, lt2k.JESD204B_WB3_REG, b3);
        device.HsFpgaWriteDataAtAddress(cId, lt2k.JESD204B_WB2_REG, b2);
        device.HsFpgaWriteDataAtAddress(cId, lt2k.JESD204B_WB1_REG, b1);
        device.HsFpgaWriteDataAtAddress(cId, lt2k.JESD204B_WB0_REG, b0);
        device.HsFpgaWriteDataAtAddress(cId, lt2k.JESD204B_W2INDEX_REG, (bitand(address, 4032) / 6)); % Upper 6 bits of AXI reg address
        device.HsFpgaWriteDataAtAddress(cId, lt2k.JESD204B_CONFIG_REG, (bitor((bitand(address, 63) * 4), 2)));
        x = device.HsFpgaReadDataAtAddress(cId, lt2k.JESD204B_CONFIG_REG);
        if (bitand(x, 1) == 0)
            error('Got bad FPGA status in write_jedec_reg');
        end
    end 

    function channelData = Capture4(device, memSize, buffSize, dumpData, dumpPscopeData, verbose)

        clockStatus = device.HsFpgaReadDataAtAddress(cId, lt2k.CLOCK_STATUS_REG);

        if(verbose)
            fprintf('Reading Clock Status register; should be 0x16 (or at least 0x04 bit set)');
            fprintf('Register 6   (Clock status) is %x\n', lths.HsFpgaReadDataAtAddress(cId, lt2k.CLOCK_STATUS_REG));
        end

        captureStatus = device.HsFpgaReadDataAtAddress(cId, lt2k.CAPTURE_STATUS_REG);

        if(bitand(captureStatus, 4) ~= 0)
            syncErr = 1;
        else
            syncErr = 0;
        end

        if (verbose ~= 0)
            fprintf('\nReading capture status, should be 0xF0 or 0xF4 (CH0, CH1 valid, Capture NOT done, data not fetched)');
            fprintf('\nAnd it is... 0x%s', dec2hex(captureStatus, 4));
        end

        device.HsFpgaWriteDataAtAddress(cId, lt2k.CAPTURE_CONFIG_REG, uint8(bitor(memSize, 8))); % Both Channels active

        device.HsFpgaWriteDataAtAddress(cId, lt2k.CAPTURE_CONTROL_REG, 0);
        device.HsFpgaWriteDataAtAddress(cId, lt2k.CAPTURE_CONTROL_REG, 1);  % Start!!

        pause(1);  % wait for capture

        captureStatus = device.HsFpgaReadDataAtAddress(cId, lt2k.CAPTURE_STATUS_REG);
        if(bitand(captureStatus, 4) ~= 0)
            syncErr = 1;
        else
            syncErr = 0;
        end

        if (verbose ~= 0)
            fprintf('\nReading capture status, should be 0xF1 (CH0, CH1, CH2, CH3 valid, Capture  IS done, data not fetched)');
            fprintf('\nAnd it is... 0x%s', dec2hex(captureStatus, 4));
        end

        device.DataSetLowByteFirst(cId); % Set endian-ness
        device.HsSetBitMode(cId, device.HS_BIT_MODE_FIFO);
        pause(0.1);

        throwAway = 3;

        [data01, nSampsRead] = device.DataReceiveUint16Values(cId, buffSize);

        if(throwAway ~= 0)
            device.DataReceiveBytes(cId, throwAway);
        end

        device.HsSetBitMode(cId, device.HS_BIT_MODE_MPSSE);

        if(verbose ~= 0)
            fprintf('\nRead out %d samples for CH0, 1', nSampsRead);
        end

        % Okay, now get CH2, CH3 data...

        device.HsSetBitMode(cId, device.HS_BIT_MODE_MPSSE);
        pause(0.1);

        device.HsFpgaWriteDataAtAddress(cId, lt2k.CAPTURE_RESET_REG, 1); % Reset

        device.HsFpgaWriteDataAtAddress(cId, lt2k.CAPTURE_CONFIG_REG, uint8(bitor(memSize, 10))); % CH2 and CH3

        device.HsFpgaWriteDataAtAddress(cId, lt2k.CAPTURE_CONTROL_REG, 2);
        device.HsFpgaWriteDataAtAddress(cId, lt2k.CAPTURE_CONTROL_REG, 3);

        captureStatus = device.HsFpgaReadDataAtAddress(cId, lt2k.CAPTURE_STATUS_REG);
        if(bitand(captureStatus, 4) ~= 0)
            syncErr = 1;
        else
            syncErr = 0;
        end

        if (verbose ~= 0)
            fprintf('\nReading capture status, should be 0xF1 (CH0, CH1, CH2, CH3 valid, Capture  IS done, data not fetched)');
            fprintf('\nAnd it is... 0x%s', dec2hex(captureStatus, 4));
        end

        device.HsSetBitMode(cId, device.HS_BIT_MODE_FIFO);
        pause(0.1);

        [data23, nSampsRead] = device.DataReceiveUint16Values(cId, buffSize);

        if(throwAway ~= 0)
            device.DataReceiveBytes(cId, throwAway);
        end

        device.HsSetBitMode(cId, device.HS_BIT_MODE_MPSSE);
        pause(0.1);

        if(verbose ~= 0)
            fprintf('\nRead out %d samples for CH2, 3', nSampsRead);
        end

        % Initialize data arrays
        dataCh0 = zeros(1, buffSize/2);
        dataCh1 = zeros(1, buffSize/2);
        dataCh2 = zeros(1, buffSize/2);
        dataCh3 = zeros(1, buffSize/2);

        for i = 1 : 2 : (buffSize)/2
            % Split data for CH0, CH1
            dataCh0(i) = data01(i*2 - 1);
            dataCh0(i+1) = data01(i*2);
            dataCh1(i) = data01(i*2 + 1);
            dataCh1(i+1) = data01(i*2 + 2);

            % Split data for CH2, CH3
            dataCh2(i) = data23(i*2 - 1);
            dataCh2(i+1) = data23(i*2);
            dataCh3(i) = data23(i*2 + 1);
            dataCh3(i+1) = data23(i*2 + 2);
        end
        nSampsPerChannel = nSampsRead/2;
        channelData = [dataCh0, dataCh1, dataCh2, dataCh3, nSampsPerChannel, syncErr];
    end % end of function
end