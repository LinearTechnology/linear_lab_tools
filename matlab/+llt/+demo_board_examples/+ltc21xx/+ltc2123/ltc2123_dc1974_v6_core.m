% DC1974 / LTC2123 Interface Example
% LTC2123: Dual 14-Bit 250Msps ADC with JESD204B Serial Outputs
%
% This program demonstrates how to communicate with the LTC2123 demo board using MATLAB.
% 
% Board setup is described in Demo Manual 1974. Follow the procedure in this manual, and
% verify operation with PScope software. Once operation is verified, exit PScope
% and run this script.
% 
% Demo board documentation:
% http://www.linear.com/demo/1974
% http://www.linear.com/product/LTC2123#demoboards
%
% LTC2123 product page
% http://www.linear.com/product/LTC2123
%  
% REVISION HISTORY
% $Revision$
% $Date$
%
% Copyright (c) 2015, Linear Technology Corp.(LTC)
% All rights reserved.
% 
% Redistribution and use in source and binary forms, with or without
% modification, are permitted provided that the following conditions are met:
% 
% 1. Redistributions of source code must retain the above copyright notice, this
%    list of conditions and the following disclaimer.
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

% NOTE:
% 	ADD THE ABSOLUTE PATH TO "linear_lab_tools\matlab" FOLDER BEFORE RUNNING THE SCRIPT.
%   RUN "mex -setup" TO SET UP COMPILER AND CHOSE THE OPTION "Lcc-win32 C".

function ltc2123_dc1974_v6_core

    % Initialize script operation parameters
    bit_file_id = 190; % Bitfile ID
    continuous = false;            % Run continuously or once
    runs = 0;                      % Run counter
    runs_with_errors = 0;          % Keep track of runs with errors
    runs_with_uncaught_errors = 0; % Runs with errors that did not have SYNC~ asserted
    error_count = 0;                % Initial error count

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
    dev_id = 171;  %  Device ID (programmed into ADC, read back from JEDEC core)
    bank_id = 12;   %  Bank      (programmed into ADC, read back from JEDEC core)
    k = 10;     %  Frames per multiframe (subClass 1 only)
    liu = 2;  %  Lanes in use
    modes = 0; %  Enable FAM, LAM (Frame / Lane alignment monitorning)
    % modes = 0x18 % Disable FAM, LAM (for testing purposes)

    % patternCheck = 32 % Enable PRBS check, ADC data otherwise
    pattern_check = false; %  Zero to disable PRBS check, dumps number of samples to console for numbers >0
    dump_pattern = 32; % Dump pattern analysis

    dump_data = 32; % Set to 1 and select an option below to dump to STDOUT:
    
    dump_pscope_data = 1; % Writes data to "pscope_data.csv", append to header to open in PScope
    
    do_reset = true;
    % Reset FPGA once (not necessary to reset between data loads)
    
    if VERBOSE
        fprintf('Basic LTC2123 DC1974 Interface Program\n');
    end


    % Returns the object in the class constructor
    lths = llt.Common.LtcControllerComm();

    % Import LTC2000 definitions and support functions
    ltc2123 = llt.demo_board_examples.ltc23xx.ltc2123.ltc2123_constants();
    
    buff_size = 64 * 1024;
    mem_size = ltc2123.mem_size_byte(buff_size);
    
    %Configure other ADC modes here to override ADC data / PRBS selection
    force_pattern = 0;    %Don't override ADC data / PRBS selection
    % Other options:
    % 0x04 = PRBS, 0x06 Test Samples test pattern, 0x07 = RPAT,
    % 0x02 = K28.7 (minimum frequency), 0x03 = D21.5 (maximum frequency)

    device_info_list = lths.list_controllers(lths.TYPE_HIGH_SPEED);
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

    % init a device and get an id
    cid = lths.init(device_info);

    while (runs < 1 || continuous == true) && runs_with_errors < 100000
        
        runs = runs + 1;
        fprintf('LTC2123 Interface Program');
        fprintf('Run number: %s', runs');
        fprintf('\nRuns with errors: %s\n', runs_with_errors');
        if (runs_with_uncaught_errors > 0)
            fprintf('***\n***\n***\n*** UNCAUGHT error count: %s !\n***\n***\n***\n', ...
                runs_with_uncaught_errors);
        end
        
        lths.hs_set_bit_mode(cid, lths.HS_BIT_MODE_MPSSE);
        if do_reset
            lths.hs_fpga_toggle_reset(cid);
        end

        fprintf('FPGA ID is %x\n', lths.hs_fpga_read_data_at_address(cid, ltc2123.ID_REG));
        fprintf('Register 4 (capture status) is %x\n', lths.hs_fpga_read_data_at_address(cid, ltc2123.CAPTURE_STATUS_REG));
        fprintf('Register 6   (Clock status) is %x\n', lths.hs_fpga_read_data_at_address(cid, ltc2123.CLOCK_STATUS_REG));


        if VERBOSE
            fprintf('Configuring ADC over SPI\n');
        end

        if(pattern_check)
            load_ltc212x(lths, 0, VERBOSE, dev_id, bank_id, liu, k, modes, 0, 4);
        else
            load_ltc212x(lths, 0, VERBOSE, dev_id, bank_id, liu, k, modes, 0, force_pattern);
        end

        if(initialize_core)
            if(VERBOSE)
                fprintf('Configuring JESD204B core!!');
            end
            write_jesd204b_reg(lths, 8, 0, 0, 0, 1);  % Enable ILA
            write_jesd204b_reg(lths, 12, 0, 0, 0, 0);  % Scrambling - 0 to disable, 1 to enable
            write_jesd204b_reg(lths, 16, 0, 0, 0, 1);  %  Only respond to first SYSREF (Subclass 1 only)
            write_jesd204b_reg(lths, 24, 0, 0, 0, 0);  %  Normal operation (no test modes enabled)
            write_jesd204b_reg(lths, 32, 0, 0, 0, 1);  %  2 octets per frame
            write_jesd204b_reg(lths, 36, 0, 0, 0, k-1);   %  Frames per multiframe, 1 to 32 for V6 core
            write_jesd204b_reg(lths, 40, 0, 0, 0, liu-1); %  Lanes in use - program with N-1
            write_jesd204b_reg(lths, 44, 0, 0, 0, 0);  %  Subclass 0
            write_jesd204b_reg(lths, 48, 0, 0, 0, 0);  %  RX buffer delay = 0
            write_jesd204b_reg(lths, 52, 0, 0, 0, 0);  %  Disable error counters, error reporting by SYNC~
            write_jesd204b_reg(lths, 4, 0, 0, 0, 1);  %  Reset core
        end

        clockStatus = lths.HsFpgaReadDataAtAddress(cid, ltc2123.CLOCK_STATUS_REG);
        fprintf('Double-checking clock status after JESD204B configuration:');
        fprintf('\nRegister 6   (Clock status): 0x%s', dec2hex(clockStatus, 4));

        if(VERBOSE)
            fprintf('\nCapturing data and resetting...');
        end
        
        channelData = capture_2_channels(lths, mem_size, buff_size, dump_data, dump_pscope_data, VERBOSE);
        if(pattern_check ~= 0)
            error_count = pattern_checker(channelData.dataCh0, channelData.nSampsPerChannel, dump_pattern);
            error_count = error_count + pattern_checker(channelData.dataCh1, channelData.nSampsPerChannel, dump_pattern);
        end

        if(error_count ~= 0)
            outFile = fopen('LTC2123_python_error_log.txt','a');
            fprintf(outFile,'Caught %d errors on run %d\n', error_count, runs);
            fclose(outFile);
            
            runs_with_errors = runs_with_errors + 1;
            if (channelData.syncErr == false)
                 runs_with_uncaught_errors = runs_with_uncaught_errors + 1;
            end
            fprintf('Error counts: %d', error_count);
        end
        
        if(VERBOSE)
            read_xilinx_core_config(lths, 1);
            read_xilinx_core_ilas(lths, VERBOSE, 0);
            read_xilinx_core_ilas(lths, VERBOSE, 1);
        end

        % Plot data if not running pattern check
        if((plot_data == true) && (pattern_check == false))
            figure
            subplot(2, 1, 1)
            plot(data_ch0)
            title('CH0')
            subplot(2, 1, 2)
            plot(data_ch1)
            title('CH1')

            data_ch0 = data_ch0 - mean(data_ch0);
            data_ch0 = data_ch0' .* llt.common.fft_window(buff_size/2); % Apply BlackmanHarris92 window
            freqDomainCh0 = fft(data_ch0)/(buff_size/2); % FFT
            freqDomainMagnitudeCh0 = abs(freqDomainCh0); % Extract magnitude
            freqDomainMagnitudeDbCh0 = 20 * log10(freqDomainMagnitudeCh0/8192.0);

            data_ch1 = data_ch1 - mean(data_ch1);
            data_ch1 = data_ch1' .* llt.common.fft_window(buff_size/2); % Apply BlackmanHarris92 window
            freqDomainCh1 = fft(data_ch1)/(buff_size/2); % FFT
            freqDomainMagnitudeCh1 = abs(freqDomainCh1); % Extract magnitude
            freqDomainMagnitudeDbCh1 = 20 * log10(freqDomainMagnitudeCh1/8192.0);

            figure
            subplot(2,1,1)
            plot(freqDomainMagnitudeDbCh0)
            title('CH0 FFT')
            subplot(2,1,2)
            plot(freqDomainMagnitudeDbCh1)
            title('CH1 FFT')

        end
    end

        
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    %%%    FUNCTION DEFINITIONS    
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    
    function reset_fpga(device)
        device.hs_set_bit_mode(cid, device.HS_BIT_MODE_MPSSE);
        device.hs_fpga_toggle_reset(cid);
        pause(0.01);
    end   
    
    % Adding support for V6 core, with true AXI access. Need to confirm that this doesn't
    % break anything with V4 FPGA loads, as we'd be writing to undefined registers.
    function [byte3, byte2, byte1, byte0] = read_jesd204b_reg(device, address)
        device.hs_fpga_write_data_at_address(cid, ltc2123.JESD204B_R2INDEX_REG, ...
            bitshift(bitand(address,4032), -6));  % Upper 6 bits of AXI reg address
        device.hs_fpga_write_data_at_address(cid, ltc2123.JESD204B_CHECK_REG, ...
            (bitor(bitshift(bitand(address, 63), 2), 2)));  % Lower 6 bits address of Register
        
        if (bitand(device.hs_fpga_read_data(cid), 1) == 0)
            error('Got bad FPGA status in read_jedec_reg');
        end
        
        byte3 = device.hs_fpga_read_data_at_address(cid, ltc2123.JESD204B_RB3_REG);
        byte2 = device.hs_fpga_read_data_at_address(cid, ltc2123.JESD204B_RB2_REG);
        byte1 = device.hs_fpga_read_data_at_address(cid, ltc2123.JESD204B_RB1_REG);
        byte0 = device.hs_fpga_read_data_at_address(cid, ltc2123.JESD204B_RB0_REG);        
    end
    
    function load_ltc212x(device, cs_control, verbose, dev_id, bank_id, lanes, k, modes, ...
            sub_class, pattern)
        if(verbose)
            fprintf('Configuring ADCs over SPI:');
        end
        device.hs_fpga_write_data_at_address(cid, ltc2123.SPI_CONFIG_REG, cs_control);
        spi_write(device, 3, dev_id); % Device ID to 0xAB
        spi_write(device, 4, bank_id); % Bank ID to 0x01
        spi_write(device, 5, lanes-1); % 2 lane mode (default)
        spi_write(device, 6, k-1);
        spi_write(device, 7, modes); % Enable FAM, LAM
        spi_write(device, 8, sub_class); % Subclass mode
        spi_write(device, 9, pattern); % PRBS test pattern
        spi_write(device, 10, 3); %  0x03 = 16mA CML current
    end 

    function read_xilinx_core_config(device, verbose)
        fprintf('\n\nJEDEC core config registers:')  
        for i = 0 : 15
            reg = i*4;
            [byte3, byte2, byte1, byte0] = read_jesd204b_reg(device, reg);
            fprintf('\n%s : 0X %s %s %s %s', ltc2123.JESD204B_XILINX_CONFIG_REG_NAMES{i + 1}, ...
                dec2hex(byte3, 2), dec2hex(byte2, 2), dec2hex(byte1, 2), dec2hex(byte0, 2));
        end
    end

    function read_xilinx_core_ilas(device, verbose, lane)
        startreg = 2048 + lane * 64;
        fprintf('\n\nILAS and stuff for lane %d :', lane);
        for i = 0 : 12
            reg = startreg + i*4;
            [byte3, byte2, byte1, byte0] = read_jesd204b_reg(device, reg);
            fprintf('\n %s : 0X %s %s %s %s', ltc2123.JESD204B_XILINX_LANE_REG_NAMES{i + 1}, ...
                dec2hex(byte3, 2), dec2hex(byte2, 2), dec2hex(byte1, 2), dec2hex(byte0, 2));
        end
    end
    
    function spi_write(device, address, value)
        device.spi_send_byte_at_address(cid, bitor(address, ltc2123.SPI_WRITE), value);
    end

    function value = spi_read(device, address)
        value = device.spi_receive_byte_at_address(cid, bitor(address, ltc2123.SPI_READ));
    end

    function dump_adc_registers(device)
        device.hs_set_bit_mode(cid, device.HS_BIT_MODE_MPSSE);
        fprintf('LTC2124 Register Dump: '); 
        fprintf('Register 4 (capture status) is %x\n', device.hs_fpga_read_data_at_address(cid, ...
            ltc2123.CAPTURE_STATUS_REG));
        fprintf('Register 1: %x\n',spi_read(device, 129));
        fprintf('Register 2: %x\n',spi_read(device, 130));
        fprintf('Register 3: %x\n',spi_read(device, 131));
        fprintf('Register 4: %x\n',spi_read(device, 132));
        fprintf('Register 5: %x\n',spi_read(device, 133));
        fprintf('Register 6: %x\n',spi_read(device, 134));
        fprintf('Register 7: %x\n',spi_read(device, 135));
        fprintf('Register 8: %x\n',spi_read(device, 136));
        fprintf('Register 9: %x\n',spi_read(device, 137));
        fprintf('Register A: %x\n',spi_read(device, 138)); 
    end

    % Adding support for V6 core, with true AXI access. Need to confirm that this 
    % doesn't break anything with V4 FPGA loads,
    % as we'd be writing to undefined registers.
    function write_jesd204b_reg(device, address, b3, b2, b1, b0)
        device.hs_fpga_write_data_at_address(cid, ltc2123.JESD204B_WB3_REG, b3);
        device.hs_fpga_write_data_at_address(cid, ltc2123.JESD204B_WB2_REG, b2);
        device.hs_fpga_write_data_at_address(cid, ltc2123.JESD204B_WB1_REG, b1);
        device.hs_fpga_write_data_at_address(cid, ltc2123.JESD204B_WB0_REG, b0);
        device.hs_fpga_write_data_at_address(cid, ltc2123.JESD204B_W2INDEX_REG, ...
            (bitand(address, 4032) / 6)); % Upper 6 bits of AXI reg address
        device.hs_fpga_write_data_at_address(cid, ltc2123.JESD204B_CONFIG_REG, ...
            (bitor((bitand(address, 63) * 4), 2)));
        x = device.hs_fpga_write_data_at_address(cid, ltc2123.JESD204B_CONFIG_REG);
        if (bitand(x, 1) == 0)
            error('Got bad FPGA status in write_jedec_reg');
        end
    end 

    function channel_data = capture_2_channels(device, mem_size, buff_size, dump_data, ...
            dump_pscope_data, verbose)
        device.hs_set_bit_mode(cid, device.HS_BIT_MODE_MPSSE);
        dec = 0;

        device.hs_fpga_write_data_at_address(cid, ltc2123.CAPTURE_CONFIG_REG, uint8(bitor(mem_size, 8))); % Both Channels active

        device.hs_fpga_write_data_at_address(cid, ltc2123.CAPTURE_RESET_REG, 1); % Reset
        device.hs_fpga_write_data_at_address(cid, ltc2123.CAPTURE_CONTROL_REG, 1);  % Start!!
        
        pause(1);  % wait for capture

        data = device.hs_fpga_read_data_at_address(cid, ltc2123.CAPTURE_STATUS_REG);
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
        device.data_set_low_byte_first(cid); % Set endian-ness
        device.hs_set_bit_mode(cid, device.HS_BIT_MODE_FIFO);
        
        pause(0.1);
        [data, num_samps_read] = device.data_receive_uint16_values(cid, buff_size + 100);

    %    extrabytecount, extrabytes = device.fifo_receive_bytes(end = 100)
        device.hs_set_bit_mode(cid, device.HS_BIT_MODE_MPSSE);

        %sleep(sleeptime)

        if(verbose ~= 0)
            fprintf('\nRead out %d samples', num_samps_read);
        end

        % Initialize data arrays
        data_ch0 = zeros(1, buff_size/2);
        data_ch1 = zeros(1, buff_size/2);


        for i = 1 : 2 : (buff_size)/2
            % Split data for CH0, CH1
            data_ch0(i) = data(i*2 - 1);
            data_ch0(i+1) = data(i*2);
            data_ch1(i) = data(i*2 + 1);
            data_ch1(i+1) = data(i*2 + 2);
        end

        nSampsPerChannel = buff_size/2;
        channel_data = [data_ch0, data_ch1, nSampsPerChannel, syncErr];
    end % end of function
    
    function error_count = pattern_checker(data, num_samps_per_channel, dump_pattern)
        print_error = true;
        error_count = num_samps_per_channel - 1; % Start big
        % periodicity = lastperiodicity = 0
        golden = next_pbrs(data(0));
        for i = 0 : (num_samps_per_channel-1)
            next = next_pbrs(data(i));
            if(i < dump_pattern)
                %fprintf('data: 0x' + '{:04X}'.format(data(i)) + ', next: 0x' +'{:04X}'.format(next) + ', XOR: 0x' +'{:04X}'.format(data[i+1] ^ next) + ', golden: 0x' +'{:04X}'.format(golden));      % UN-commet for hex
                % print '0b' + '{:016b}'.format(data[i]) + ',  0x' +'{:016b}'.format(next) + ',  0x' +'{:016b}'.format(data[i] ^ next)   % UN-comment for binary
            end
            if(data(i+1) == next)
                error_count = error_count - 1;
            elseif(print_error)
                print_error = False;
                %fprintf(hexStr(data(i-1)) + "; " + hexStr(data(i)) + "; " + hexStr(data(i+1));
                
    %                print "error count = " + str(errorCount)
    %                device.Close() % End of main loop.
    %                raise Exception("BAD DATA!!!")
            end
            if(data(i) == data(0))
                % periodicity = i - lastperiodicity
                lastperiodicity = i;
            end
            golden = next_pbrs(golden);

        % print "periodicity (only valid for captures > 64k): " + str(periodicity)
        % if errorCount < 0:
        %     errorCount = 100000000
        end
    end %end of function
    
end
