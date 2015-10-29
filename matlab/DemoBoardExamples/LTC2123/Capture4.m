function channelData = Capture4(device, memSize, buffSize, dumpData, dumpPscopeData, verbose, data)

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