function test_ltc_controller_comm

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
    
    device_info_list = lths.ListControllers();
    device_info = [];
    for info = device_info_list
       if strcmp(info.description(1:7), 'LTC2000')
           device_info = info;
       end
    end

    if isempty(device_info)
        error('TestLtcHighSpeedComm:noDevice', 'No LTC200 demo board detected');
    end

    fprintf('Found LTC2000 demo board:\n');
    fprintf('Description: %s\n', device_info.description);
    fprintf('Serial Number: %s\n', device_info.serial_number);

    % init a device and get an id
    did = lths.init(device_info);
    
    lths.hs_set_bit_mode(did, lths.HS_BIT_MODE_MPSSE);
    lths.hs_fpga_toggle_reset(did);

    fprintf('FPGA ID is %X\n', lths.hs_fpga_read_data_at_address(did, FPGA_ID_REG));

    lths.hs_fpga_write_data_at_address(did, FPGA_DAC_PD, 1);

    spi_write(REG_RESET_PD, 0);
    spi_write(REG_CLK_PHASE, 5);
    spi_write(REG_PORT_EN, 11);
    spi_write(REG_SYNC_PHASE, 0);
    spi_write(REG_LINEAR_GAIN, 0);
    spi_write(REG_LINEARIZATION, 8);
    spi_write(REG_DAC_GAIN, 32);
    spi_write(REG_LVDS_MUX, 0);
    spi_write(REG_TEMP_SELECT, 0);
    spi_write(REG_PATTERN_ENABLE, 0);

    if bitand(spi_read(REG_RESET_PD), 207) ~= 0
        error('TestLtcHighSpeedComm:badRegResetPd', 'Bad REG_RESET_PD value');
    end

    if spi_read(REG_CLK_PHASE) ~= 7
        error('TestLtcHighSpeedComm:badRegClkPhase', 'Expected a 7');
    end    

    if spi_read(REG_PORT_EN) ~= 11
        error('TestLtcHighSpeedComm:badRegPortEn', 'Expected an 11');
    end 

    if bitand(spi_read(REG_SYNC_PHASE), 252) ~= 0
        error('TestLtcHighSpeedComm:badRegSyncPhase', 'Bad value');
    end

    if (spi_read(REG_LINEAR_GAIN) ~= 0)
        error('TestLtcHighSpeedComm:badRegLinearGain', 'Expected a 0');
    end

    if (spi_read(REG_LINEARIZATION) ~= 8)
        error('TestLtcHighSpeedComm:badRegLinearization', 'Expected an 8');
    end

    if (spi_read(REG_DAC_GAIN) ~= 32)
        error('TestLtcHighSpeedComm:badRegDacGain', 'Expected a 32');
    end

    lths.hs_fpga_write_data_at_address(did, FPGA_CONTROL_REG, 32);

    time = 1:NUM_DAC_SAMPLES;
    data = floor(AMPLITUDE * sin((NUM_CYCLES_1 * TWO_PI * time) / NUM_DAC_SAMPLES));

    lths.hs_set_bit_mode(did, lths.BIT_MODE_FIFO);

    lths.fifo_send_uint16_values(did, data);

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
    reset_fpga();
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
    reset_fpga();
    pause(0.1);
    data = swapbytes(int16(floor( ...
        AMPLITUDE * sin((NUM_CYCLES_3 * TWO_PI * time) / NUM_DAC_SAMPLES))));
    data32 = swapbytes(typecast(data, 'uint32'));
    lths.data_send_uint32_values(did, data32);

    fprintf('Basic test finished, do you see a sine wave in the scope with ');
    fprintf('frequency = clockFrequency / %f?\n', NUM_DAC_SAMPLES / NUM_CYCLES_3);
    response = input('(y = yes, n = no)\n', 's');
    if response(1) ~= 'y'
        error('TestLtcHighSpeedComm:basicTest', 'User indicates output is invalid');
    end
    fprintf('FifoSendUint32Values is OK\n');

    lths.hs_set_bit_mode(did, lths.HS_BIT_MODE_MPSSE);

    WRITE_LINEAR_GAIN = bitor(REG_LINEAR_GAIN, SPI_WRITE_BIT);
    READ_LINEAR_GAIN = bitor(REG_LINEAR_GAIN, SPI_READ_BIT);

    lths.hs_spi_send_bytes(did, [WRITE_LINEAR_GAIN, 2]);    
    if spi_read(REG_LINEAR_GAIN) ~= 2
       error('TestLtcHighSpeedComm:SpiSendBytes', ...
           'SpiSendBytes didn''t seem to work'); 
    end

    fprintf('SpiSendBytes is OK\n');

    lths.spi_transceive_bytes(did, [WRITE_LINEAR_GAIN, 4]);
    values = lths.spi_transceive_bytes(did, [READ_LINEAR_GAIN, 0]);
    if (values(2) ~= 4)
        error('TestLtcHighSpeedComm:SpiTransceiveBytes', ...
            'SpiTransceiveBytes didn''t seem to work'); 
    end
    fprintf('SpiTransceiveBytes is OK\n');

    lths.spi_send_bytes_at_address(did, WRITE_LINEAR_GAIN, 6);
    if spi_read(REG_LINEAR_GAIN) ~= 6
        error('TestLtcHighSpeedComm:SpiSendBytesAtAddress', ...
            'SpiSendBytesAtAddress didn''t seem to work'); 
    end
    fprintf('SpiSendBytesAtAddress is OK\n');

    if lths.spi_receive_bytes_at_address(did, READ_LINEAR_GAIN, 1) ~= 6
        error('TestLtcHighSpeedComm:SpiReceiveBytesAtAddress', ...
            'SpiReceiveBytesAtAdderss didn''t seem to work');
    end

    lths.spi_set_chip_select(did, lths.SPI_CHIP_SELECT_LOW);
    lths.spi_send_no_chip_select(did, [WRITE_LINEAR_GAIN, 8]);
    lths.spi_set_chip_select(did, lths.SPI_CHIP_SELECT_HIGH);
    if spi_read(REG_LINEAR_GAIN) ~= 8
        error('TestLtcHighSpeedComm:SpiSendNoChipSelect', ...
            'SpiSetChipSelect or SpiSendNoChipSelect didn''t seem to work');
    end
    fprintf('SpiSetChipSelect is OK\n');
    fprintf('SpiSendNoChipSelect is OK\n');

    lths.spi_set_chip_select(did, lths.SPI_CHIP_SELECT_LOW);
    lths.spi_send_no_chip_select(did, READ_LINEAR_GAIN);
    ok = lths.spi_receive_no_chip_select(did, 1) == 8;
    lths.spi_set_chip_select(did, lths.SPI_CHIP_SELECT_HIGH);
    if (~ok)
        error('TestLtcHighSpeedComm:SpiReceiveNoChipSelect', ...
            'SpiReceiveNoChipSelect didn''t seem to work');
    end
    fprintf('SpiReceiveNoChipSelect is OK\n');

    lths.spi_set_chip_select(did, lths.SPI_CHIP_SELECT_LOW);
    lths.spi_transceive_no_chip_select(did, [WRITE_LINEAR_GAIN, 10]);
    lths.spi_set_chip_select(did, lths.SPI_CHIP_SELECT_HIGH);
    lths.spi_set_chip_select(did, lths.SPI_CHIP_SELECT_LOW);
    values = lths.spi_transceive_no_chip_select(did, [READ_LINEAR_GAIN, 0]);
    lths.spi_set_chip_select(did, lths.SPI_CHIP_SELECT_HIGH);
    if values(2) ~= 10
        error('TestLtcHighSpeedComm:SpiTransceiveNoChipSelect', ...
            'SpiTransceiveNoChipSelect didn''t seem to work');
    end
    fprintf('SpiTransceiveNoChipSelect is OK\n');

    lths.hs_fpga_write_address(did, FPGA_ID_REG);
    lths.hs_fpga_write_data(did, 92);
    if lths.hs_fpga_read_data_at_address(did, FPGA_ID_REG) ~= 92
        error('TestLtcHighSpeedComm:FpgaWriteData', ...
            'FpgaWriteAddress or FpgaWriteData didn''t seem to work');
    end
    fprintf('FpgaWriteAddress is OK\n');
    fprintf('FpgaWriteData is OK\n');

    lths.hs_fpga_write_data(did, 37);
    if lths.hs_fpga_read_data(did) ~= 37
        error('TestLtcHighSpeedComm:FpgaReadData', 'FpgaReadData didn''t seem to work');
    end
    fprintf('FpgaReadData is OK\n');

    lths.hs_fpga_write_address(did, FPGA_ID_REG);

    lths.hs_gpio_write_low_byte(did, GPIO_LOW_BASE);
    lths.hs_gpio_write_high_byte(did, 56);
    lths.hs_gpio_write_low_byte(did, bitor(GPIO_LOW_BASE, FPGA_ACTION_BIT));
    lths.hs_gpio_write_low_byte(did, GPIO_LOW_BASE);
    if lths.hs_fpga_read_data(did) ~= 56
        error('TestLtcHighSpeedComm:GpioWriteHighByte', ...
            'GpioWriteHighByte or GpioWriteLow byte didn''t seem to work');
    end
    fprintf('GpioWriteHighByte is OK\n');
    fprintf('GpioWriteLowByte is OK\n');

    lths.hs_fpga_write_data(did, 72);

    lths.hs_gpio_write_low_byte(did, bitor(GPIO_LOW_BASE, FPGA_READ_WRITE_BIT));
    lths.hs_gpio_write_low_byte(did, bitor(bitor(GPIO_LOW_BASE, FPGA_READ_WRITE_BIT), FPGA_ACTION_BIT));
    ok = lths.hs_gpio_read_high_byte(did) == 72;
    lths.hs_gpio_write_low_byte(did, GPIO_LOW_BASE);
    if ~ok
        error('TestLtcHighSpeedComm:GpioReadHighByte', 'GpioReadHighByte didn''t seem to work');
    end
    fprintf('GpioReadHighByte is OK\n');

    if ~strcmp(device_info.description, lths.get_description(did))
        error('TestLtcHighSpeedComm:GetDescription', 'GetDescription didn''t seem to work');
    end
    fprintf('GetDescription is OK\n');

    if ~strcmp(device_info.serialNumber, lths.get_serial_number(did))
        error('TestLtcHighSpeedComm:GetSerialNumber', 'GetSerialNumber didn''t seem to work');
    end
    fprintf('GetSerialNumber is OK\n');

    lths.set_timeouts(did, 500, 500);
    tic;
    lths.data_receive_bytes(did, 1);
    elapsed = toc;
    if elapsed < 0.450 || elapsed > 0.550
        error('TestLtcHighSpeedComm:SetTimeouts', 'SetTimeouts didn''t seem to work');
    end

    lths.set_timeouts(did, 3000, 3000);
    tic;
    lths.data_receive_bytes(did, 1);
    elapsed = toc;
    if elapsed < 2.75 || elapsed > 3.25
        error('TestLtcHighSpeedComm:SetTimeouts', 'SetTimeouts didn''t seem to work');
    end
    fprintf('SetTimeouts is OK\n');

    lths.fifo_send_bytes(did, 128);
    lths.hs_purge_io(did);
    result = lths.data_receive_bytes(did, 1);
    if ~isempty(result)
        error('TestLtcHighSpeedComm:PurgeIo', 'PurgeIo didn''t seem to work');
    end
    fprintf('PurgeIo is OK\n');

    lths.close(did);
    stolen_id = lths.init(device_info);

    lths.hs_fpga_read_data_at_address(stolen_id, FPGA_ID_REG);
    close_ok = false;
    error_info_ok = false;
    try
        lths.HsFpgaReadDataAtAddress(did, FPGA_ID_REG);
    catch ex
        close_ok = true;
        if strcmp(ex.message, 'Error opening the device.')
            error_info_ok = true;
        end
    end
    if ~close_ok
        error('TestLtcHighSpeedComm:Close', 'Close didn''t seem to work');
    end
    fprintf('Close is OK\n');
    if ~error_info_ok
        error('TestLtcHighSpeedComm:GetErrorInfo', 'GetErrorInfo didn''t seem to work');
    end
    fprintf('GetErrorInfo is OK\n');
    lths.cleanup(stolen_id);
    clear stolen_id;

    lths.hs_fpga_read_data_at_address(did, FPGA_ID_REG);

    fprintf('Cleanup is OK\n');
    
    lths.cleanup(did);
    clear did

    input('Test battery 2\nUse an LTC2123 setup.\nPress enter when ready.\n');

    device_info_list = lths.list_devices();
    device_info = [];
    for info = device_info_list
       if strcmp(info.description, 'LTC Communication Interface')
           device_info = info;
       end
    end

    if isempty(device_info)
        error('TestLtcHighSpeedComm:noDevice', 'No LTC2123 demo board detected');
    end

    fprintf('Found LTC2123 demo board:\n');
    fprintf('Description: %s\n', device_info.description);
    fprintf('Serial Number: %s\n', device_info.serial_number);

    did = lths.init(device_info);
    lths.hs_set_bit_mode(did, lths.HS_BIT_MODE_MPSSE);
    lths.hs_fpga_toggle_reset(did);
    lths.data_set_low_byte_first(did);

    init_adc();

    lths.hs_set_bit_mode(did, lths.BIT_MODE_FIFO);
    [data16, num_bytes] = lths.data_receive_uint16_values(did, NUM_ADC_SAMPLES);
    if (num_bytes ~= NUM_ADC_SAMPLES * 2)
        error('TestHighSpeedComm:FifoReceiveUint16Values', ...
            'FifoReceiveUint16Values didn''t seem to work');
    end
    channel_a = zeros(length(data16)/2, 1);
    channel_b = channel_a;
    channel_a(1:2:end) = data16(1:4:end);
    channel_a(2:2:end) = data16(2:4:end);
    channel_b(1:2:end) = data16(3:4:end);
    channel_b(2:2:end) = data16(4:4:end);

    if ~check_prbs(channel_a)
        error('TestHighSpeedComm:FifoReceiveUint16Values', ...
            'FifoReceiveUint16Values didn''t seem to work');
    end
    if ~check_prbs(channel_b)
        error('TestHighSpeedComm:FifoReceiveUint16Values', ...
            'FifoReceiveUint16Values didn''t seem to work');
    end

    fprintf('FifoReceiveUint16Values is OK\n');

    init_adc();
    lths.hs_set_bit_mode(did, lths.BIT_MODE_FIFO);
    [data32, num_bytes] = lths.data_receive_uint32_values(did, NUM_ADC_SAMPLES / 2);

    if (num_bytes ~= NUM_ADC_SAMPLES * 2)
        error('TestHighSpeedComm:FifoReceiveUint32Values', ...
            'FifoReceiveUint32Values didn''t seem to work');
    end
    channel_a = typecast(data32(1:2:end), 'uint16');
    channel_b = typecast(data32(2:2:end), 'uint16');

    if ~check_prbs(channel_a)
        error('TestHighSpeedComm:FifoReceiveUint32Values', ...
            'FifoReceiveUint32Values didn''t seem to work');
    end
    if ~check_prbs(channel_b)
        error('TestHighSpeedComm:FifoReceiveUint32Values', ...
            'FifoReceiveUint32Values didn''t seem to work');
    end
    fprintf('FifoReceiveUint32Values is OK\n');

    init_adc();
    lths.hs_set_bit_mode(did, lths.BIT_MODE_FIFO);
    data8 = uint8(lths.data_receive_bytes(did, NUM_ADC_SAMPLES * 2));
    data16 = typecast(data8, 'uint16');
    channel_a(1:2:end) = data16(1:4:end);
    channel_a(2:2:end) = data16(2:4:end);
    channel_b(1:2:end) = data16(3:4:end);
    channel_b(2:2:end) = data16(4:4:end);
    if ~check_prbs(channel_a)
        error('TestHighSpeedComm:FifoReceiveBytes', ...
            'FifoReceiveBytes didn''t seem to work');
    end
    if ~check_prbs(channel_b)
        error('TestHighSpeedComm:FifoReceiveBytes', ...
            'FifoReceiveBytes didn''t seem to work');
    end
    fprintf('FifoReceiveBytes is OK\n');

    lths.hs_set_bit_mode(did, lths.HS_BIT_MODE_MPSSE);
    lths.hs_fpga_toggle_reset(did);

    string = lths.eeprom_read_string(did, MAX_EEPROM_CHARS);

    if ~strncmp(LTC2123_ID_STRING, string, length(LTC2123_ID_STRING))
        error('TestLtcHighSpeedComm:FpgaEepromReceiveString', ...
            'FpgaEepromReceiveString didn''t seem to work.');
    end
    fprintf('FpgaEepromReceiveString is OK\n');

    lths.hs_fpga_write_data_at_address(did, 0, 0);
    lths.hs_fpga_eeprom_set_bit_bang_register(did, 0);
    try
        lths.eeprom_read_string(did, 1);
    catch % we are just checking that an error gets thrown
        % errors out because there is no lths to ACK
    end
    if lths.hs_fpga_read_data_at_address(did, 0) == 0
        error('TestLtcHighSpeedComm:FpgaI2cSetBitBangRegister', ...
            'FpgaEepromSetBitBangRegister didn''t seem to work');
    end
    fprintf('FpgaEepromSetBitBangRegister is OK\n');

    fprintf('Test Battery 3\n Use an FT2232H mini-module with:\n');
    fprintf('CN2-5 connected to CN2-11\n');
    fprintf('CN3-1 connected to CN3-3\n');
    fprintf('CN3-17 connected to CN3-24\n');
    input('Press enter when ready\n.');

    device_info_list = lths.list_devices();
    device_info = [];
    for info = device_info_list
       if strcmp(info.description, 'LTC Communication Interface')
           device_info = info;
       end
    end

    if isempty(device_info)
        error('TestLtcHighSpeedComm:noDevice', 'No Mini module board detected');
    end

    fprintf('Found mini-module:\n');
    fprintf('Description: %s\n', device_info.description);
    fprintf('Serial Number: %s\n', device_info.serial_number);

    did = lths.init(device_info);

    lths.hs_set_bit_mode(did, lths.HS_BIT_MODE_MPSSE);
    lths.hs_gpio_write_high_byte(did, 1);
    if lths.spi_receive_bytes(did, 1) ~= 255
        error('TestLtcHighSpeedComm:SpiReciveBytes', ...
            'SpiReceiveBytes didn''t seem to work');
    end  
    lths.hs_gpio_write_high_byte(did, 0);
    if lths.spi_receive_bytes(did, 1) ~= 0
        error('TestLtcHighSpeedComm:SpiReciveBytes', ...
            'SpiReceiveBytes didn''t seem to work');
    end 
    fprintf('SpiReceiveBytes is OK\n');

    lths.hs_gpio_write_high_byte(did, 1);
    if bitand(lths.hs_gpio_read_low_byte(did), 4) == 0
        error('TestLtcHighSpeedComm:GpioReadLowByte', ...
            'GpioReadLowByte didn''t seem to work');
    end
    lths.hs_gpio_write_high_byte(did, 0);
    if bitand(lths.hs_gpio_read_low_byte(did), 4) ~= 0
        error('TestLtcHighSpeedComm:GpioReadLowByte', ...
            'GpioReadLowByte didn''t seem to work');
    end
    fprintf('GpioReadLowByte is OK\n');

    fprintf('All tests passed!\n');

    function reset_fpga
       lths.hs_set_bit_mode(did, lths.HS_BIT_MODE_MPSSE);
       lths.hs_fpga_toggle_reset(did);
       pause(0.01);
       lths.hs_fpga_write_data_at_address(did, FPGA_DAC_PD, 1);
       pause(0.01);
       lths.hs_fpga_write_data_at_address(did, FPGA_CONTROL_REG, 32);
       pause(0.01);
       lths.hs_set_bit_mode(did, lths.BIT_MODE_FIFO);
    end

    function spi_write(address, value)
        lths.spi_send_byte_at_address(did, bitor(address, SPI_WRITE_BIT), value);
    end

    function value = spi_read(address)
        value = lths.spi_receive_byte_at_address(did, bitor(address, SPI_READ_BIT));
    end

    function write_jedec_reg(address, b3, b2, b1, b0)
       lths.hs_fpga_write_data_at_address(did, JESD204B_WB3_REG, b3); 
       lths.hs_fpga_write_data_at_address(did, JESD204B_WB2_REG, b2);
       lths.hs_fpga_write_data_at_address(did, JESD204B_WB1_REG, b1);
       lths.hs_fpga_write_data_at_address(did, JESD204B_WB0_REG, b0);
       lths.hs_fpga_write_data_at_address(did, JESD204B_CONFIG_REG, ...
           bitor(bitshift(address, 2), 2));
       if bitand(lths.hs_fpga_read_data(did), 1) == 0
           error('TestLtcHighSpeedComm:WriteJedecReg', 'Got bad status');
       end
    end

    function init_adc()
        lths.close(did);
        lths.hs_set_bit_mode(did, lths.HS_BIT_MODE_MPSSE);
        lths.hs_fpga_toggle_reset(did);
        spi_write(1, 0);
        spi_write(2, 0);
        spi_write(3, 171);
        spi_write(4, 12);
        spi_write(5, 1);
        spi_write(6, 23);
        spi_write(7, 0);
        spi_write(8, 0);
        spi_write(9, 4);

        write_jedec_reg(1, 0, 0, 0, 1);
        write_jedec_reg(2, 0, 0, 0, 0);
        write_jedec_reg(3, 0, 0, 0, 23);
        write_jedec_reg(0, 0, 0, 1, 2);

        if lths.hs_fpga_read_data_at_address(did, CLOCK_STATUS_REG) ~= 30
            error('TestLtcHighSpeedComm:InitDac', 'Bad clock status');
        end

        lths.hs_fpga_write_data_at_address(did, CAPTURE_CONFIG_REG, 120);
        lths.hs_fpga_write_data_at_address(did, CAPTURE_RESET_REG, 1);
        lths.hs_fpga_write_data_at_address(did, CAPTURE_CONTROL_REG, 1);
        pause(0.05);
        if bitand(lths.hs_fpga_read_data_at_address(did, CAPTURE_STATUS_REG), 49) ~= 49
            error('TestLtcHighSpeedComm:initDac', 'Bad capture status');
        end
    end

    function next = next_prbs(current_value)
       next = bitand(bitxor(bitshift(current_value, 1, 'uint16'), ...
           bitshift(current_value, 2, 'uint16')), 65532);
       next = bitor(next, bitand(bitxor(bitshift(next, -15, 'uint16'), ...
           bitshift(next, -14, 'uint16')), 1));
       next = bitor(next, bitand(bitxor(bitshift(next, -14, 'uint16'), ...
           bitshift(current_value, 1, 'uint16')), 2));
    end

    function ok = check_prbs(data)
       if data(1) == 0
           ok = false;
           return;
       end

       for i = 2:length(data)
           next = next_prbs(data(i - 1));
           if data(i) ~= next
               ok = false;
               return;
           end
       end
       ok = true;
    end
end
