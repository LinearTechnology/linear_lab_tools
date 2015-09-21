function TestLtcHighSpeedComm

    NUM_DAC_SAMPLES = 64 * 1024;
    NUM_CYCLES_1 = 489;
    NUM_CYCLES_2 = 2 * NUM_CYCLES_1;
    NUM_CYCLES_3 = 2 * NUM_CYCLES_2;
    AMPLITUDE = 32000;
    TWO_PI = 2 * pi;

    REG_RESET_PD = 1;
    REG_CLK_PHASE = 3;
    REG_PORT_EN = 4;
    REG_SYNC_PHASE = 5;
    REG_LINEAR_GAIN = 7;
    REG_LINEARIZATION = 8;
    REG_DAC_GAIN = 9;
    REG_LVDS_MUX = 24;
    REG_TEMP_SELECT = 25;
    REG_PATTERN_ENABLE = 30;

    FPGA_ID_REG = 0;
    FPGA_CONTROL_REG = 1;
    FPGA_DAC_PD = 3;

    NUM_ADC_SAMPLES = 16384;

    CAPTURE_CONFIG_REG = 1;
    CAPTURE_CONTROL_REG = 2;
    CAPTURE_RESET_REG = 3;
    CAPTURE_STATUS_REG = 4;
    CLOCK_STATUS_REG = 6;

    MAX_EEPROM_CHARS = 240;

    JESD204B_WB0_REG    = 7;
    JESD204B_WB1_REG    = 8;
    JESD204B_WB2_REG    = 9;
    JESD204B_WB3_REG    = 10;
    JESD204B_CONFIG_REG = 11;

    SPI_READ_BIT = 128;
    SPI_WRITE_BIT = 0;

    GPIO_LOW_BASE = 138;
    FPGA_ACTION_BIT = 16;
    FPGA_READ_WRITE_BIT = 32;

    NL = sprintf('\r\n');
    LTC2123_ID_STRING = ['[0074 DEMO 10 DC1974A-A LTC2124-14 D2124', NL, ...
                         'ADC 14 16 2 0000 00 00 00 00', NL, ...
                         'DBFLG 0003 00 00 00 00', NL, ...
                         'FPGA S0000 T0', NL, ...
                         '187F]'];

    input('Test battery 1\nUse an LTC2000 setup and a scope.\nPress enter when ready.\n');

    % loads library and lets user init devices to get an id
    lths = LtcControllerComm();
    
    deviceInfoList = lths.ListControllers();
    deviceInfo = [];
    for info = deviceInfoList
       if strcmp(info.description(1:7), 'LTC2000')
           deviceInfo = info;
       end
    end

    if isempty(deviceInfo)
        error('TestLtcHighSpeedComm:noDevice', 'No LTC200 demo board detected');
    end

    fprintf('Found LTC2000 demo board:\n');
    fprintf('Description: %s\n', deviceInfo.description);
    fprintf('Serial Number: %s\n', deviceInfo.serialNumber);

    % init a device and get an id
    did = lths.Init(deviceInfo);
    
    lths.HsSetBitMode(did, lths.HS_BIT_MODE_MPSSE);
    lths.HsFpgaToggleReset(did);

    fprintf('FPGA ID is %X\n', lths.HsFpgaReadDataAtAddress(did, FPGA_ID_REG));

    lths.HsFpgaWriteDataAtAddress(did, FPGA_DAC_PD, 1);

    SpiWrite(REG_RESET_PD, 0);
    SpiWrite(REG_CLK_PHASE, 5);
    SpiWrite(REG_PORT_EN, 11);
    SpiWrite(REG_SYNC_PHASE, 0);
    SpiWrite(REG_LINEAR_GAIN, 0);
    SpiWrite(REG_LINEARIZATION, 8);
    SpiWrite(REG_DAC_GAIN, 32);
    SpiWrite(REG_LVDS_MUX, 0);
    SpiWrite(REG_TEMP_SELECT, 0);
    SpiWrite(REG_PATTERN_ENABLE, 0);

    if bitand(SpiRead(REG_RESET_PD), 207) ~= 0
        error('TestLtcHighSpeedComm:badRegResetPd', 'Bad REG_RESET_PD value');
    end

    if SpiRead(REG_CLK_PHASE) ~= 7
        error('TestLtcHighSpeedComm:badRegClkPhase', 'Expected a 7');
    end    

    if SpiRead(REG_PORT_EN) ~= 11
        error('TestLtcHighSpeedComm:badRegPortEn', 'Expected an 11');
    end 

    if bitand(SpiRead(REG_SYNC_PHASE), 252) ~= 0
        error('TestLtcHighSpeedComm:badRegSyncPhase', 'Bad value');
    end

    if (SpiRead(REG_LINEAR_GAIN) ~= 0)
        error('TestLtcHighSpeedComm:badRegLinearGain', 'Expected a 0');
    end

    if (SpiRead(REG_LINEARIZATION) ~= 8)
        error('TestLtcHighSpeedComm:badRegLinearization', 'Expected an 8');
    end

    if (SpiRead(REG_DAC_GAIN) ~= 32)
        error('TestLtcHighSpeedComm:badRegDacGain', 'Expected a 32');
    end

    lths.HsFpgaWriteDataAtAddress(did, FPGA_CONTROL_REG, 32);

    time = 1:NUM_DAC_SAMPLES;
    data = floor(AMPLITUDE * sin((NUM_CYCLES_1 * TWO_PI * time) / NUM_DAC_SAMPLES));

    lths.HsSetBitMode(did, lths.BIT_MODE_FIFO);

    lths.FifoSendUint16Values(did, data);

    fprintf('Basic test finished, do you see a sine wave in the scope with ');
    fprintf('frequency = clockFrequency / %f?\n', NUM_DAC_SAMPLES / NUM_CYCLES_1);
    response = input('(y = yes, n = no)\n', 's');
    if response(1) ~= 'y'
        error('TestLtcHighSpeedComm:basicTest', 'User indicates output is invalid');
    end

    fprintf('lths.ListDevices is OK\n');
    fprintf('SetBitMode is OK\n');
    fprintf('SetReset is OK\n');
    fprintf('FpgaReadDataAtAddress is OK\n');
    fprintf('FpgaWriteDataAtAddress is OK\n');
    fprintf('SpiWriteByteAtAddress is OK\n');
    fprintf('SpiReadByteAtAddress is OK\n');
    fprintf('FifoSendUint16Values is OK\n');

    pause(0.1);
    ResetFpga();
    pause(0.1);
    data = floor(AMPLITUDE * sin((NUM_CYCLES_2 * TWO_PI * time) / NUM_DAC_SAMPLES));
    data8 = typecast(swapbytes(int16(data)), 'uint8');
    lths.FifoSendBytes(did, data8);

    fprintf('Basic test finished, do you see a sine wave in the scope with ');
    fprintf('frequency = clockFrequency / %f?\n', NUM_DAC_SAMPLES / NUM_CYCLES_2);
    response = input('(y = yes, n = no)\n', 's');
    if response(1) ~= 'y'
        error('TestLtcHighSpeedComm:basicTest', 'User indicates output is invalid');
    end
    fprintf('FifoSendBytes is OK\n');

    pause(0.1);
    ResetFpga();
    pause(0.1);
    data = swapbytes(int16(floor(AMPLITUDE * sin((NUM_CYCLES_3 * TWO_PI * time) / NUM_DAC_SAMPLES))));
    data32 = swapbytes(typecast(data, 'uint32'));
    lths.DataSendUint32Values(did, data32);

    fprintf('Basic test finished, do you see a sine wave in the scope with ');
    fprintf('frequency = clockFrequency / %f?\n', NUM_DAC_SAMPLES / NUM_CYCLES_3);
    response = input('(y = yes, n = no)\n', 's');
    if response(1) ~= 'y'
        error('TestLtcHighSpeedComm:basicTest', 'User indicates output is invalid');
    end
    fprintf('FifoSenUint32Values is OK\n');

    lths.HsSetBitMode(did, lths.HS_BIT_MODE_MPSSE);

    WRITE_LINEAR_GAIN = bitor(REG_LINEAR_GAIN, SPI_WRITE_BIT);
    READ_LINEAR_GAIN = bitor(REG_LINEAR_GAIN, SPI_READ_BIT);

    lths.HsSpiSendBytes(did, [WRITE_LINEAR_GAIN, 2]);    
    if SpiRead(REG_LINEAR_GAIN) ~= 2
       error('TestLtcHighSpeedComm:SpiSendBytes', 'SpiSendBytes didn''t seem to work'); 
    end

    fprintf('SpiSendBytes is OK\n');

    lths.SpiTransceiveBytes(did, [WRITE_LINEAR_GAIN, 4]);
    values = lths.SpiTransceiveBytes(did, [READ_LINEAR_GAIN, 0]);
    if (values(2) ~= 4)
        error('TestLtcHighSpeedComm:SpiTransceiveBytes', 'SpiTransceiveBytes didn''t seem to work'); 
    end
    fprintf('SpiTransceiveBytes is OK\n');

    lths.SpiSendBytesAtAddress(did, WRITE_LINEAR_GAIN, 6);
    if SpiRead(REG_LINEAR_GAIN) ~= 6
        error('TestLtcHighSpeedComm:SpiSendBytesAtAddress', 'SpiSendBytesAtAddress didn''t seem to work'); 
    end
    fprintf('SpiSendBytesAtAddress is OK\n');

    if lths.SpiReceiveBytesAtAddress(did, READ_LINEAR_GAIN, 1) ~= 6
        error('TestLtcHighSpeedComm:SpiReceiveBytesAtAddress', 'SpiReceiveBytesAtAdderss didn''t seem to work');
    end

    lths.SpiSetChipSelect(did, lths.SPI_CHIP_SELECT_LOW);
    lths.SpiSendNoChipSelect(did, [WRITE_LINEAR_GAIN, 8]);
    lths.SpiSetChipSelect(did, lths.SPI_CHIP_SELECT_HIGH);
    if SpiRead(REG_LINEAR_GAIN) ~= 8
        error('TestLtcHighSpeedComm:SpiSendNoChipSelect', 'SpiSetChipSelect or SpiSendNoChipSelect didn''t seem to work');
    end
    fprintf('SpiSetChipSelect is OK\n');
    fprintf('SpiSendNoChipSelect is OK\n');

    lths.SpiSetChipSelect(did, lths.SPI_CHIP_SELECT_LOW);
    lths.SpiSendNoChipSelect(did, READ_LINEAR_GAIN);
    ok = lths.SpiReceiveNoChipSelect(did, 1) == 8;
    lths.SpiSetChipSelect(did, lths.SPI_CHIP_SELECT_HIGH);
    if (~ok)
        error('TestLtcHighSpeedComm:SpiReceiveNoChipSelect', 'SpiReceiveNoChipSelect didn''t seem to work');
    end
    fprintf('SpiReceiveNoChipSelect is OK\n');

    lths.SpiSetChipSelect(did, lths.SPI_CHIP_SELECT_LOW);
    lths.SpiTransceiveNoChipSelect(did, [WRITE_LINEAR_GAIN, 10]);
    lths.SpiSetChipSelect(did, lths.SPI_CHIP_SELECT_HIGH);
    lths.SpiSetChipSelect(did, lths.SPI_CHIP_SELECT_LOW);
    values = lths.SpiTransceiveNoChipSelect(did, [READ_LINEAR_GAIN, 0]);
    lths.SpiSetChipSelect(did, lths.SPI_CHIP_SELECT_HIGH);
    if values(2) ~= 10
        error('TestLtcHighSpeedComm:SpiTransceiveNoChipSelect', 'SpiTransceiveNoChipSelect didn''t seem to work');
    end
    fprintf('SpiTransceiveNoChipSelect is OK\n');

    lths.HsFpgaWriteAddress(did, FPGA_ID_REG);
    lths.HsFpgaWriteData(did, 92);
    if lths.HsFpgaReadDataAtAddress(did, FPGA_ID_REG) ~= 92
        error('TestLtcHighSpeedComm:FpgaWriteData', 'FpgaWriteAddress or FpgaWriteData didn''t seem to work');
    end
    fprintf('FpgaWriteAddress is OK\n');
    fprintf('FpgaWriteData is OK\n');

    lths.HsFpgaWriteData(did, 37);
    if lths.HsFpgaReadData(did) ~= 37
        error('TestLtcHighSpeedComm:FpgaReadData', 'FpgaReadData didn''t seem to work');
    end
    fprintf('FpgaReadData is OK\n');

    lths.HsFpgaWriteAddress(did, FPGA_ID_REG);

    lths.HsGpioWriteLowByte(did, GPIO_LOW_BASE);
    lths.HsGpioWriteHighByte(did, 56);
    lths.HsGpioWriteLowByte(did, bitor(GPIO_LOW_BASE, FPGA_ACTION_BIT));
    lths.HsGpioWriteLowByte(did, GPIO_LOW_BASE);
    if lths.HsFpgaReadData(did) ~= 56
        error('TestLtcHighSpeedComm:GpioWriteHighByte', 'GpioWriteHighByte or GpioWriteLow byte didn''t seem to work');
    end
    fprintf('GpioWriteHighByte is OK\n');
    fprintf('GpioWriteLowByte is OK\n');

    lths.HsFpgaWriteData(did, 72);

    lths.HsGpioWriteLowByte(did, bitor(GPIO_LOW_BASE, FPGA_READ_WRITE_BIT));
    lths.HsGpioWriteLowByte(did, bitor(bitor(GPIO_LOW_BASE, FPGA_READ_WRITE_BIT), FPGA_ACTION_BIT));
    ok = lths.HsGpioReadHighByte(did) == 72;
    lths.HsGpioWriteLowByte(did, GPIO_LOW_BASE);
    if ~ok
        error('TestLtcHighSpeedComm:GpioReadHighByte', 'GpioReadHighByte didn''t seem to work');
    end
    fprintf('GpioReadHighByte is OK\n');

    if ~strcmp(deviceInfo.description, lths.GetDescription(did))
        error('TestLtcHighSpeedComm:GetDescription', 'GetDescription didn''t seem to work');
    end
    fprintf('GetDescription is OK\n');

    if ~strcmp(deviceInfo.serialNumber, lths.GetSerialNumber(did))
        error('TestLtcHighSpeedComm:GetSerialNumber', 'GetSerialNumber didn''t seem to work');
    end
    fprintf('GetSerialNumber is OK\n');

    lths.SetTimeouts(did, 500, 500);
    tic;
    lths.DataReceiveBytes(did, 1);
    elapsed = toc;
    if elapsed < 0.450 || elapsed > 0.550
        error('TestLtcHighSpeedComm:SetTimeouts', 'SetTimeouts didn''t seem to work');
    end

    lths.SetTimeouts(did, 3000, 3000);
    tic;
    lths.DataReceiveBytes(did, 1);
    elapsed = toc;
    if elapsed < 2.75 || elapsed > 3.25
        error('TestLtcHighSpeedComm:SetTimeouts', 'SetTimeouts didn''t seem to work');
    end
    fprintf('SetTimeouts is OK\n');

    lths.FifoSendBytes(did, 128);
    lths.HsPurgeIo(did);
    result = lths.DataReceiveBytes(did, 1);
    if ~isempty(result)
        error('TestLtcHighSpeedComm:PurgeIo', 'PurgeIo didn''t seem to work');
    end
    fprintf('PurgeIo is OK\n');

    lths.Close(did);
    stolenId = lths.Init(deviceInfo);

    lths.HsFpgaReadDataAtAddress(stolenId, FPGA_ID_REG);
    closeOk = false;
    errorInfoOk = false;
    try
        lths.HsFpgaReadDataAtAddress(did, FPGA_ID_REG);
    catch ex
        closeOk = true;
        if strcmp(ex.message, 'Error opening the device.')
            errorInfoOk = true;
        end
    end
    if ~closeOk
        error('TestLtcHighSpeedComm:Close', 'Close didn''t seem to work');
    end
    fprintf('Close is OK\n');
    if ~errorInfoOk
        error('TestLtcHighSpeedComm:GetErrorInfo', 'GetErrorInfo didn''t seem to work');
    end
    fprintf('GetErrorInfo is OK\n');
    lths.Cleanup(stolenId);
    clear stolenId;

    lths.HsFpgaReadDataAtAddress(did, FPGA_ID_REG);

    fprintf('Cleanup is OK\n');
    
    lths.Cleanup(did);
    clear did

    input('Test battery 2\nUse an LTC2123 setup.\nPress enter when ready.\n');

    deviceInfoList = lths.ListDevices();
    deviceInfo = [];
    for info = deviceInfoList
       if strcmp(info.description, 'LTC Communication Interface')
           deviceInfo = info;
       end
    end

    if isempty(deviceInfo)
        error('TestLtcHighSpeedComm:noDevice', 'No LTC2123 demo board detected');
    end

    fprintf('Found LTC2123 demo board:\n');
    fprintf('Description: %s\n', deviceInfo.description);
    fprintf('Serial Number: %s\n', deviceInfo.serialNumber);

    did = lths.Init(deviceInfo);
    lths.HsSetBitMode(did, lths.HS_BIT_MODE_MPSSE);
    lths.HsFpgaToggleReset(did);
    lths.DataSetLowByteFirst(did);

    InitAdc();

    lths.HsSetBitMode(did, lths.BIT_MODE_FIFO);
    [data16, nBytes] = lths.DataReceiveUint16Values(did, NUM_ADC_SAMPLES);
    if (nBytes ~= NUM_ADC_SAMPLES * 2)
        error('TestHighSpeedComm:FifoReceiveUint16Values', ...
            'FifoReceiveUint16Values didn''t seem to work');
    end
    channelA = zeros(length(data16)/2, 1);
    channelB = channelA;
    channelA(1:2:end) = data16(1:4:end);
    channelA(2:2:end) = data16(2:4:end);
    channelB(1:2:end) = data16(3:4:end);
    channelB(2:2:end) = data16(4:4:end);

    if ~CheckPrbs(channelA)
        error('TestHighSpeedComm:FifoReceiveUint16Values', ...
            'FifoReceiveUint16Values didn''t seem to work');
    end
    if ~CheckPrbs(channelB)
        error('TestHighSpeedComm:FifoReceiveUint16Values', ...
            'FifoReceiveUint16Values didn''t seem to work');
    end

    fprintf('FifoReceiveUint16Values is OK\n');

    InitAdc();
    lths.HsSetBitMode(did, lths.BIT_MODE_FIFO);
    [data32, nBytes] = lths.DataReceiveUint32Values(did, NUM_ADC_SAMPLES / 2);

    if (nBytes ~= NUM_ADC_SAMPLES * 2)
        error('TestHighSpeedComm:FifoReceiveUint32Values', ...
            'FifoReceiveUint32Values didn''t seem to work');
    end
    channelA = typecast(data32(1:2:end), 'uint16');
    channelB = typecast(data32(2:2:end), 'uint16');

    if ~CheckPrbs(channelA)
        error('TestHighSpeedComm:FifoReceiveUint32Values', ...
            'FifoReceiveUint32Values didn''t seem to work');
    end
    if ~CheckPrbs(channelB)
        error('TestHighSpeedComm:FifoReceiveUint32Values', ...
            'FifoReceiveUint32Values didn''t seem to work');
    end
    fprintf('FifoReceiveUint32Values is OK\n');

    InitAdc();
    lths.HsSetBitMode(did, lths.BIT_MODE_FIFO);
    data8 = uint8(lths.DataReceiveBytes(did, NUM_ADC_SAMPLES * 2));
    data16 = typecast(data8, 'uint16');
    channelA(1:2:end) = data16(1:4:end);
    channelA(2:2:end) = data16(2:4:end);
    channelB(1:2:end) = data16(3:4:end);
    channelB(2:2:end) = data16(4:4:end);
    if ~CheckPrbs(channelA)
        error('TestHighSpeedComm:FifoReceiveBytes', ...
            'FifoReceiveBytes didn''t seem to work');
    end
    if ~CheckPrbs(channelB)
        error('TestHighSpeedComm:FifoReceiveBytes', ...
            'FifoReceiveBytes didn''t seem to work');
    end
    fprintf('FifoReceiveBytes is OK\n');

    lths.HsSetBitMode(did, lths.HS_BIT_MODE_MPSSE);
    lths.HsFpgaToggleReset(did);

    string = lths.EepromReadString(did, MAX_EEPROM_CHARS);

    if ~strncmp(LTC2123_ID_STRING, string, length(LTC2123_ID_STRING))
        error('TestLtcHighSpeedComm:FpgaEepromReceiveString', ...
            'FpgaEepromReceiveString didn''t seem to work.');
    end
    fprintf('FpgaEepromReceiveString is OK\n');

    lths.HsFpgaWriteDataAtAddress(did, 0, 0);
    lths.HsFpgaEepromSetBitBangRegister(did, 0);
    try
        lths.EepromReadString(did, 1);
    catch %#ok we are just checking that an error gets thrown
        % errors out because there is no lths to ACK
    end
    if lths.HsFpgaReadDataAtAddress(did, 0) == 0
        error('TestLtcHighSpeedComm:FpgaI2cSetBitBangRegister', ...
            'FpgaEepromSetBitBangRegister didn''t seem to work');
    end
    fprintf('FpgaEepromSetBitBangRegister is OK\n');

    fprintf('Test Battery 3\n Use an FT2232H mini-module with:\n');
    fprintf('CN2-5 connected to CN2-11\n');
    fprintf('CN3-1 connected to CN3-3\n');
    fprintf('CN3-17 connected to CN3-24\n');
    input('Press enter when ready\n.');

    deviceInfoList = lths.ListDevices();
    deviceInfo = [];
    for info = deviceInfoList
       if strcmp(info.description, 'LTC Communication Interface')
           deviceInfo = info;
       end
    end

    if isempty(deviceInfo)
        error('TestLtcHighSpeedComm:noDevice', 'No Mini module board detected');
    end

    fprintf('Found mini-module:\n');
    fprintf('Description: %s\n', deviceInfo.description);
    fprintf('Serial Number: %s\n', deviceInfo.serialNumber);

    did = lths.Init(deviceInfo);

    lths.HsSetBitMode(did, lths.HS_BIT_MODE_MPSSE);
    lths.HsGpioWriteHighByte(did, 1);
    if lths.SpiReceiveBytes(did, 1) ~= 255
        error('TestLtcHighSpeedComm:SpiReciveBytes', ...
            'SpiReceiveBytes didn''t seem to work');
    end  
    lths.HsGpioWriteHighByte(did, 0);
    if lths.SpiReceiveBytes(did, 1) ~= 0
        error('TestLtcHighSpeedComm:SpiReciveBytes', ...
            'SpiReceiveBytes didn''t seem to work');
    end 
    fprintf('SpiReceiveBytes is OK\n');

    lths.HsGpioWriteHighByte(did, 1);
    if bitand(lths.HsGpioReadLowByte(did), 4) == 0
        error('TestLtcHighSpeedComm:GpioReadLowByte', ...
            'GpioReadLowByte didn''t seem to work');
    end
    lths.HsGpioWriteHighByte(did, 0);
    if bitand(lths.HsGpioReadLowByte(did), 4) ~= 0
        error('TestLtcHighSpeedComm:GpioReadLowByte', ...
            'GpioReadLowByte didn''t seem to work');
    end
    fprintf('GpioReadLowByte is OK\n');

    fprintf('All tests passed!\n');

    function ResetFpga
       lths.HsSetBitMode(did, lths.HS_BIT_MODE_MPSSE);
       lths.HsFpgaToggleReset(did);
       pause(0.01);
       lths.HsFpgaWriteDataAtAddress(did, FPGA_DAC_PD, 1);
       pause(0.01);
       lths.HsFpgaWriteDataAtAddress(did, FPGA_CONTROL_REG, 32);
       pause(0.01);
       lths.HsSetBitMode(did, lths.BIT_MODE_FIFO);
    end

    function SpiWrite(address, value)
        lths.SpiSendByteAtAddress(did, bitor(address, SPI_WRITE_BIT), value);
    end

    function value = SpiRead(address)
        value = lths.SpiReceiveByteAtAddress(did, bitor(address, SPI_READ_BIT));
    end

    function WriteJedecReg(address, b3, b2, b1, b0)
       lths.HsFpgaWriteDataAtAddress(did, JESD204B_WB3_REG, b3); 
       lths.HsFpgaWriteDataAtAddress(did, JESD204B_WB2_REG, b2);
       lths.HsFpgaWriteDataAtAddress(did, JESD204B_WB1_REG, b1);
       lths.HsFpgaWriteDataAtAddress(did, JESD204B_WB0_REG, b0);
       lths.HsFpgaWriteDataAtAddress(did, JESD204B_CONFIG_REG, ...
           bitor(bitshift(address, 2), 2));
       if bitand(lths.HsFpgaReadData(did), 1) == 0
           error('TestLtcHighSpeedComm:WriteJedecReg', 'Got bad status');
       end
    end

    function InitAdc()
        lths.Close(did);
        lths.HsSetBitMode(did, lths.HS_BIT_MODE_MPSSE);
        lths.HsFpgaToggleReset(did);
        SpiWrite(1, 0);
        SpiWrite(2, 0);
        SpiWrite(3, 171);
        SpiWrite(4, 12);
        SpiWrite(5, 1);
        SpiWrite(6, 23);
        SpiWrite(7, 0);
        SpiWrite(8, 0);
        SpiWrite(9, 4);

        WriteJedecReg(1, 0, 0, 0, 1);
        WriteJedecReg(2, 0, 0, 0, 0);
        WriteJedecReg(3, 0, 0, 0, 23);
        WriteJedecReg(0, 0, 0, 1, 2);

        if lths.HsFpgaReadDataAtAddress(did, CLOCK_STATUS_REG) ~= 30
            error('TestLtcHighSpeedComm:InitDac', 'Bad clock status');
        end

        lths.HsFpgaWriteDataAtAddress(did, CAPTURE_CONFIG_REG, 120);
        lths.HsFpgaWriteDataAtAddress(did, CAPTURE_RESET_REG, 1);
        lths.HsFpgaWriteDataAtAddress(did, CAPTURE_CONTROL_REG, 1);
        pause(0.05);
        if bitand(lths.HsFpgaReadDataAtAddress(did, CAPTURE_STATUS_REG), 49) ~= 49
            error('TestLtcHighSpeedComm:initDac', 'Bad capture status');
        end
    end

    function next = NextPrbs(currentValue)
       next = bitand(bitxor(bitshift(currentValue, 1, 'uint16'), bitshift(currentValue, 2, 'uint16')), 65532);
       next = bitor(next, bitand(bitxor(bitshift(next, -15, 'uint16'), bitshift(next, -14, 'uint16')), 1));
       next = bitor(next, bitand(bitxor(bitshift(next, -14, 'uint16'), bitshift(currentValue, 1, 'uint16')), 2));
    end

    function ok = CheckPrbs(data)
       if data(1) == 0
           ok = false;
           return;
       end

       for i = 2:length(data)
           next = NextPrbs(data(i - 1));
           if data(i) ~= next
               ok = false;
               return;
           end
       end
       ok = true;
    end
end
