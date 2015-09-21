
% DC2085 / LTC2000 Interface Example
%
% This program demonstrates how to communicate with the LTC2000 demo board 
% using Matlab. Examples are provided for generating sinusoidal data from within
% the program, as well as writing and reading pattern data from a file.
% 
% Board setup is described in Demo Manual 2085. Follow the procedure in 
% this manual, and verify operation with the LTDACGen software. Once 
% operation is verified, exit LTDACGen and run this script.
% 
% Demo board documentation:
% http://www.linear.com/demo/2085
% http://www.linear.com/product/LTC2000#demoboards
% 
% LTC2000 product page
% http://www.linear.com/product/LTC2000
% 
% Copyright (c) 2015, Linear Technology Corp.(LTC)
% All rights reserved.
% 
% Redistribution and use in source and binary forms, with or without
% modification, are permitted provided that the following conditions are met:
% 
% 1. Redistributions of source code must retain the above copyright notice, 
%    this list of conditions and the following disclaimer.
% 2. Redistributions in binary form must reproduce the above copyright notice,
%    this list of conditions and the following disclaimer in the documentation
%    and/or other materials provided with the distribution.
% 
% THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
% ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
% WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
% DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
% ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
% (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
% LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
% ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
% (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
% SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
% 
% The views and conclusions contained in the software and documentation are those
% of the authors and should not be interpreted as representing official policies,
% either expressed or implied, of Linear Technology Corp.

function Ltc2123_dc1974_v6_core

    clear all;
    
    % Initialize script operation parameters
    bitfile_id = 190; % Bitfile ID
    continuous = false;            % Run continuously or once
    runs = 0;                      % Run counter
    runs_with_errors = 0;          % Keep track of runs with errors
    runs_with_uncaught_errors = 0; % Runs with errors that did not have SYNC~ asserted
    errorcount = 0;                % Initial error count

    % Enable Hardware initialization. This only needs to be done on the first run.
    % Can be disabled for testing purposes.
    initialize_spi = true;
    initialize_core = true;
    initialize_reset = true;

    % Display time and frequency domain plots for ADC data
    plot_data = true;
    % Display lots of debug messages
    VERBOSE = true;

    % Set up JESD204B parameters
    did=171;  %  Device ID (programmed into ADC, read back from JEDEC core)
    bid= 12;   %  Bank      (programmed into ADC, read back from JEDEC core)
    K=10;     %  Frames per multiframe (subclass 1 only)
    LIU = 2;  %  Lanes in use
    modes = 0; %  Enable FAM, LAM (Frame / Lane alignment monitorning)
    % modes = 0x18 % Disable FAM, LAM (for testing purposes)

    % patterncheck = 32 % Enable PRBS check, ADC data otherwise
    patterncheck = false; %  Zero to disable PRBS check, dumps number of samples to console for numbers >0
    dumppattern = 32; % Dump pattern analysis

    dumpdata = 32; % Set to 1 and select an option below to dump to STDOUT:
    
    dump_pscope_data = 1; % Writes data to "pscope_data.csv", append to header to open in PScope
    
    % Configure other ADC modes here to override ADC data / PRBS selection
    forcepattern = false;    % Don't override ADC data / PRBS selection
    %  Other options:
    %  0x04 = PRBS, 0x06 Test Samples test pattern, 0x07 = RPAT,
    %  0x02 = K28.7 (minimum frequency), 0x03 = D21.5 (maximum frequency)

    device = NaN;
    do_reset = true;
    % Reset FPGA once (not necessary to reset between data loads)
    
    if VERBOSE
        fprintf('Basic LTC2123 DC1974 Interface Program\n');
    end


    % Returns the object in the class constructor
    lths = LtcControllerComm();

    % Import LTC2000 definitions and support functions
    [lt2k] = ltc2123Functions(lths);

    memSize = 144;
    buffSize = 64 * 1024;
    
%     NumSamp128  = NumSamp(0, 128);
%     NumSamp256  = NumSamp(16, 256);
%     NumSamp512  = NumSamp(32, 512);
%     NumSamp1K   = NumSamp(48, 1024);
%     NumSamp2K   = NumSamp(64, 2 * 1024);
%     NumSamp4K   = NumSamp(80, 4 * 1024);
%     NumSamp8K   = NumSamp(96, 8 * 1024);
%     NumSamp16K  = NumSamp(112, 16 * 1024);
%     NumSamp32K  = NumSamp(128, 32 * 1024);
%     NumSamp64K  = NumSamp(144, 64 * 1024);
%     NumSamp128K = NumSamp(160, 128 * 1024);

    %n = NumSamp64K; % Set number of samples here.
    
    %Configure other ADC modes here to override ADC data / PRBS selection
    forcepattern = 0;    %Don't override ADC data / PRBS selection
    % Other options:
    % 0x04 = PRBS, 0x06 Test Samples test pattern, 0x07 = RPAT,
    % 0x02 = K28.7 (minimum frequency), 0x03 = D21.5 (maximum frequency)

    deviceInfoList = lths.ListControllers(lths.TYPE_HIGH_SPEED, 1);
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

    % init a device and get an id
    cId = lths.Init(deviceInfo);

    while((runs < 1 || continuous == true) && runs_with_errors < 100000)
        
        runs = runs + 1;
        fprintf('LTC2123 Interface Program');
        fprintf('Run number: %s', runs');
        fprintf('\nRuns with errors: %s\n', runs_with_errors');
        if (runs_with_uncaught_errors > 0)
            fprintf('***\n***\n***\n*** UNCAUGHT error count: %s !\n***\n***\n***\n',runs_with_uncaught_errors);
        end
        
        lths.SetBitMode(cId, lths.BIT_MODE_MPSSE);
        if do_reset
            lths.FpgaToggleReset(cId);
        end

        fprintf('FPGA ID is %X\n', lths.FpgaReadDataAtAddress(cId, lt2k.ID_REG));
        fprintf('Register 4 (capture status) is %X\n', lths.FpgaReadDataAtAddress(cId, lt2k.CAPTURE_STATUS_REG));
        fprintf('Register 6   (Clock status) is %X\n', lths.FpgaReadDataAtAddress(cId, lt2k.CLOCK_STATUS_REG));


        if VERBOSE
            fprintf('Configuring ADC over SPI\n');
        end

        if(patterncheck)
            load_ltc212x(0, VERBOSE, did, bid, LIU, K, modes, 0, 4);
        else
            load_ltc212x(0, VERBOSE, did, bid, LIU, K, modes, 0, forcepattern);
        end

        if(initialize_core)
            if(VERBOSE)
                fprintf('Configuring JESD204B core!!');
            end
            write_jesd204b_reg(8, 0, 0, 0, 1);  % Enable ILA
            write_jesd204b_reg(12, 0, 0, 0, 0);  % Scrambling - 0 to disable, 1 to enable
            write_jesd204b_reg(16, 0, 0, 0, 1);  %  Only respond to first SYSREF (Subclass 1 only)
            write_jesd204b_reg(24, 0, 0, 0, 0);  %  Normal operation (no test modes enabled)
            write_jesd204b_reg(32, 0, 0, 0, 1);  %  2 octets per frame
            write_jesd204b_reg(36, 0, 0, 0, K-1);   %  Frames per multiframe, 1 to 32 for V6 core
            write_jesd204b_reg(40, 0, 0, 0, LIU-1); %  Lanes in use - program with N-1
            write_jesd204b_reg(44, 0, 0, 0, 0);  %  Subclass 0
            write_jesd204b_reg(48, 0, 0, 0, 0);  %  RX buffer delay = 0
            write_jesd204b_reg(52, 0, 0, 0, 0);  %  Disable error counters, error reporting by SYNC~
            write_jesd204b_reg(4, 0, 0, 0, 1);  %  Reset core
        end

        data = lths.FpgaReadDataAtAddress(cId, lt2k.CLOCK_STATUS_REG);
        fprintf('Double-checking clock status after JESD204B configuration:');
        fprintf('\nRegister 6   (Clock status): 0x%s', dec2hex(data, 4));

        if(VERBOSE)
            fprintf('\nCapturing data and resetting...');
        end
        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%% FIX n, syncErr removed

        channel_data = capture2(lths, memSize, buffSize, dumpdata, dump_pscope_data, VERBOSE, data);
        if(patterncheck ~= 0)
            errorcount = pattern_checker(channel_data.data_ch0, channel_data.nSamps_per_channel, dumppattern);
            errorcount = errorcount + pattern_checker(channel_data.data_ch1, channel_data.nSamps_per_channel, dumppattern);
        end

        %%%%%%%%%%%%%%%%% error handling

        if(VERBOSE)
            read_xilinx_core_config(device, 1);
            read_xilinx_core_ilas(device, VERBOSE, 0);
            read_xilinx_core_ilas(device, VERBOSE, 1);
        end

        if((plot_data == true) && (patterncheck == false))
            figure
            subplot(2, 1, 1)
            plot(data_ch0)
            title('CH0')
            subplot(2, 1, 2)
            plot(data_ch1)
            title('CH1')


            data_ch0 = data_ch0' .* blackman(buffSize/2); % Apply Blackman window
            freq_domain_ch0 = fft(data_ch0)/(buffSize/2); % FFT
            freq_domain_magnitude_ch0 = abs(freq_domain_ch0); % Extract magnitude
            freq_domain_magnitude_db_ch0 = 10 * log(freq_domain_magnitude_ch0/8192.0);

            data_ch1 = data_ch1' .* blackman(buffSize/2); % Apply Blackman window
            freq_domain_ch1 = fft(data_ch1)/(buffSize/2); % FFT
            freq_domain_magnitude_ch1 = abs(freq_domain_ch1); % Extract magnitude
            freq_domain_magnitude_db_ch1 = 10 * log(freq_domain_magnitude_ch1/8192.0);


            figure
            subplot(2,1,1)
            plot(freq_domain_magnitude_db_ch0)
            title('CH0 FFT')
            subplot(2,1,2)
            plot(freq_domain_magnitude_db_ch1)
            title('CH1 FFT')

        end
    end

        
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    %%%    FUNCTION DEFINITIONS    
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    
    % Adding support for V6 core, with true AXI access. Need to confirm that this doesn't break anything with V4 FPGA loads,
    % as we'd be writing to undefined registers.
    function [byte3, byte2, byte1, byte0] = read_jesd204b_reg(device, address)
%         x = bitand(address, 63);
%         x = bitsra(x, 2);
%         x = bitor(x, 2);
%         fprintf('\n             address : %d', address);
%         fprintf('\n writing ro checkreg : %d', bitor(bitsll(bitand(address, 63), 2), 2));
        byte3 = lths.FpgaReadDataAtAddress(cId, lt2k.JESD204B_RB3_REG);
        byte2 = lths.FpgaReadDataAtAddress(cId, lt2k.JESD204B_RB2_REG);
        byte1 = lths.FpgaReadDataAtAddress(cId, lt2k.JESD204B_RB1_REG);
        byte0 = lths.FpgaReadDataAtAddress(cId, lt2k.JESD204B_RB0_REG); 
        lths.FpgaWriteDataAtAddress(cId, lt2k.JESD204B_R2INDEX_REG, bitsra(bitand(address,4032), 6));  % Upper 6 bits of AXI reg address
        lths.FpgaWriteDataAtAddress(cId, lt2k.JESD204B_CHECK_REG, (bitor(bitsll(bitand(address, 63), 2), 2)));  % Lower 6 bits address of JESD204B Check Register
        
%         if device.fpga_read_data() & 1 == 0
%             raise RuntimeError("Got bad FPGA status in read_jedec_reg")
%         end
       
        
    end

    function read_xilinx_core_config(device, verbose)
        fprintf('\n\nJEDEC core config registers:')  
        for i = 0 : 15
            reg = i*4;
            [byte3, byte2, byte1, byte0] = read_jesd204b_reg(device, reg);
            fprintf('\n%s : 0X %s %s %s %s', lt2k.JESD204B_XILINX_CONFIG_REG_NAMES{i + 1}, dec2hex(byte3, 2), dec2hex(byte2, 2), dec2hex(byte1, 2), dec2hex(byte0, 2));
        end
    end

    function read_xilinx_core_ilas(device, verbose, lane)
        startreg = 2048 + lane * 64;
        fprintf('\n\nILAS and stuff for lane %d :', lane);
        for i = 0 : 12
            reg = startreg + i*4;
            [byte3, byte2, byte1, byte0] = read_jesd204b_reg(device, reg)                ;
            fprintf('\n %s : 0X %s %s %s %s', lt2k.JESD204B_XILINX_LANE_REG_NAMES{i + 1}, dec2hex(byte3, 2), dec2hex(byte2, 2), dec2hex(byte1, 2), dec2hex(byte0, 2));
        end
    end
    
    function SpiWrite(address, value)
        lths.SpiSendByteAtAddress(cId, bitor(address, lt2k.SPI_WRITE), value);
    end

    function value = SpiRead(address)
        value = lths.SpiReceiveByteAtAddress(cId, bitor(address, lt2k.SPI_READ));
    end

    function dump_ADC_registers(device)
        device.SetBitMode(cId, device.BIT_MODE_MPSSE);
        fprintf('LTC2124 Register Dump: '); 
        fprintf('Register 4 (capture status) is %X\n', lths.FpgaReadDataAtAddress(cId, lt2k.CAPTURE_STATUS_REG));
        fprintf('Register 1: %X\n',SpiRead(129));
        fprintf('Register 2: %X\n',SpiRead(130));
        fprintf('Register 3: %X\n',SpiRead(131));
        fprintf('Register 4: %X\n',SpiRead(132));
        fprintf('Register 5: %X\n',SpiRead(133));
        fprintf('Register 6: %X\n',SpiRead(134));
        fprintf('Register 7: %X\n',SpiRead(135));
        fprintf('Register 8: %X\n',SpiRead(136));
        fprintf('Register 9: %X\n',SpiRead(137));
        fprintf('Register A: %X\n',SpiRead(138)); 
    end

    function load_ltc212x(cs_control, verbose, did, bid, lanes, K, modes, subclass, pattern)
        if(verbose)
            fprintf('Configuring ADCs over SPI:');
        end
        lths.FpgaWriteDataAtAddress(cId, lt2k.SPI_CONFIG_REG, cs_control);
        SpiWrite(3, cId); % Device ID to 0xAB
        SpiWrite(4, bid); % Bank ID to 0x01
        SpiWrite(5, lanes-1); % 2 lane mode (default)
        SpiWrite(6, K-1);
        SpiWrite(7, modes); % Enable FAM, LAM
        SpiWrite(8, subclass); % Subclass mode
        SpiWrite(9, pattern); % PRBS test pattern
        SpiWrite(10, 3); %  0x03 = 16mA CML current
    end 

    % Adding support for V6 core, with true AXI access. Need to confirm that this 
    % doesn't break anything with V4 FPGA loads,
    % as we'd be writing to undefined registers.
    function write_jesd204b_reg(address, b3, b2, b1, b0)
        lths.FpgaWriteDataAtAddress(cId, lt2k.JESD204B_WB3_REG, b3);
        lths.FpgaWriteDataAtAddress(cId, lt2k.JESD204B_WB2_REG, b2);
        lths.FpgaWriteDataAtAddress(cId, lt2k.JESD204B_WB1_REG, b1);
        lths.FpgaWriteDataAtAddress(cId, lt2k.JESD204B_WB0_REG, b0);
        lths.FpgaWriteDataAtAddress(cId, lt2k.JESD204B_W2INDEX_REG, (bitand(address, 4032) / 6)); % Upper 6 bits of AXI reg address
        lths.FpgaWriteDataAtAddress(cId, lt2k.JESD204B_CONFIG_REG, (bitor((bitand(address, 63) * 4), 2)));
        x = lths.FpgaReadDataAtAddress(cId, lt2k.JESD204B_CONFIG_REG);
        if (bitand(x, 1) == 0)
            error('Got bad FPGA status in write_jedec_reg');
        end
    end 

    function channel_data = capture2(device, memSize, buffSize, dumpdata, dump_pscope_data, verbose, data)
        device.SetBitMode(cId, device.BIT_MODE_MPSSE);
        dec = 0;

        device.FpgaWriteDataAtAddress(cId, lt2k.CAPTURE_CONFIG_REG, uint8(bitor(memSize, 8))); % Both Channels active

        device.FpgaWriteDataAtAddress(cId, lt2k.CAPTURE_RESET_REG, 1); % Reset
        device.FpgaWriteDataAtAddress(cId, lt2k.CAPTURE_CONTROL_REG, 1);  % Start!!
        
        pause(1);  % wait for capture

        data = device.FpgaReadDataAtAddress(cId, lt2k.CAPTURE_STATUS_REG);
        if(bitand(data, 4) ~= 0)
            syncErr = 1;
        else
            syncErr = 0;
        end
        
        if (verbose ~= 0)
            fprintf('\nReading capture status, should be 0x31 (CH0, CH1 valid, Capture done, data not fetched)');
            fprintf('\nAnd it is... 0x%s', dec2hex(data, 4));
        end
        % sleep(sleeptime)
        device.FifoSetLowByteFirst(cId); % Set endian-ness
        device.SetBitMode(cId, device.BIT_MODE_FIFO);
        
        pause(0.1);
        [data, nSampsRead] = device.FifoReceiveUint16Values(cId, buffSize + 100);

    %    extrabytecount, extrabytes = device.fifo_receive_bytes(end = 100)
        device.SetBitMode(cId, device.BIT_MODE_MPSSE);

        %sleep(sleeptime)

        if(verbose ~= 0)
            fprintf('\nRead out %d samples', nSampsRead);
        end

        % Initialize data arrays
        data_ch0 = zeros(1, buffSize/2);
        data_ch1 = zeros(1, buffSize/2);


        for i = 1 : 2 : (buffSize)/4
            % Split data for CH0, CH1
            data_ch0(i) = data(i*2 - 1);
            data_ch0(i+1) = data(i*2);
            data_ch1(i) = data(i*2 + 1);
            data_ch1(i+1) = data(i*2 + 2);
        end

        nSamps_per_channel = buffSize/2;
        channel_data = [data_ch0, data_ch1, nSamps_per_channel];
    end % end of function
    
    function errorcount = pattern_checker(data, nSamps_per_channel, dumppattern)
        printError = true;
        errorcount = nSamps_per_channel - 1; % Start big
        % periodicity = lastperiodicity = 0
        golden = next_pbrs(data(0));
        for i = 0 : (nSamps_per_channel-1)
            next = next_pbrs(data(i));
            if(i < dumppattern)
                %fprintf('data: 0x' + '{:04X}'.format(data(i)) + ', next: 0x' +'{:04X}'.format(next) + ', XOR: 0x' +'{:04X}'.format(data[i+1] ^ next) + ', golden: 0x' +'{:04X}'.format(golden));      % UN-commet for hex
                % print '0b' + '{:016b}'.format(data[i]) + ',  0x' +'{:016b}'.format(next) + ',  0x' +'{:016b}'.format(data[i] ^ next)   % UN-comment for binary
            end
            if(data(i+1) == next)
                errorcount = errorcount - 1;
            elseif(printError)
                printError = False;
                %fprintf(hexStr(data(i-1)) + "; " + hexStr(data(i)) + "; " + hexStr(data(i+1));
                
    %                print "error count = " + str(errorcount)
    %                device.Close() % End of main loop.
    %                raise Exception("BAD DATA!!!")
            end
            if(data(i) == data(0))
                % periodicity = i - lastperiodicity
                lastperiodicity = i;
            end
            golden = next_pbrs(golden);

        % print "periodicity (only valid for captures > 64k): " + str(periodicity)
        % if errorcount < 0:
        %     errorcount = 100000000
        end
    end %end of function
    
end
