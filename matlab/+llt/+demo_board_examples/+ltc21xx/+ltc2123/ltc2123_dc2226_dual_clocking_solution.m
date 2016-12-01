% DC2226 / dual LTC2123 with LTC6951 clocking solution Example
% LTC2123: Dual 14-Bit 250Msps ADC with JESD204B Serial Outputs
%
% This program demonstrates a dual LTC2123 JESD204B interface clocked by
% LTC6951 PLL with integrated VCO and clock distribution.
% 
% Demo board documentation:
% http://www.linear.com/demo/2226
% http://www.linear.com/product/LTC2123#demoboards
% 
% LTC2261 product page
% http://www.linear.com/product/LTC2123
% 
% REVISION HISTORY
% $Revision: 4260 $
% $Date: 2015-10-19 16:45:28 -0700 (Mon, 19 Oct 2015) $
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

% NOTE:
% 	ADD THE ABSOLUTE PATH TO "linear_lab_tools\matlab" FOLDER BEFORE RUNNING THE SCRIPT.
%   RUN "mex -setup" TO SET UP COMPILER AND CHOSE THE OPTION "Lcc-win32 C".

function ltc2123_dc2226_dual_clocking_solution
    
    % Import LTC2000 definitions and support functions
    ltc2123 = llt.demo_board_examples.ltc2123.ltc2123_constants(lths);

    % Initialize script operation parameters
    bit_file_id = 192; % Bitfile ID
    continuous = 0; % Run continuously, or just once
    runs = 0; % Initial run count
    runs_with_errors = 0; % Runs with PRBS errors (only valid if PRBStest is enabled)
    runs_with_uncaught_errors = 0; % Runs with errors that did NOT indicate SYNC~ assertion during capture

    do_reset = true; % Reset FPGA once (not necessary to reset between data loads)
    initialize_adcs = 1; % Initialize ADC registers (only need to do on first run)
    initialize_clocks = 1; % Initialize onboard clocks (only need to do on first run)
    initialize_core = 1; % Initialize JEDEC core in FPGA (only need to do on first run)

    verbose = 1; % Print out extra debug information
    plot_data = 1; % Plot time and frequency data after capture

    pattern_check = 0; % greater than zero to Enable PRBS check, ADC data otherwise
    dump_pattern = 16; % Dump pattern analysis

    dump_data = 16; % Set to 1 and select an option below to dump to STDOUT:
    hex_dump = 1; % Data dump format, can be either hex, decimal, or both
    dec = 0; % (if both, hex is first, followed by decimal)

    dump_pscope_data = 1; % Writes data to "pscope_data.csv", append to header to open in PScope
    
    buff_size = 64 * 1024;
    mem_size = ltc2123.mem_size_byte(buff_size);
    
    % Common ADC / JEDEC Core / Clock parameter(s) 
    k = 16; %Frames per multiframe - Note that not all ADC / Clock combinations
    % support all values of K.

    % ADC configuration parameters
    %Configure other ADC modes here to override ADC data / PRBS selection
    force_pattern = 0; %Don't override ADC data / PRBS selection
    %force_pattern = 0x04; %PRBS
    %force_pattern = 0x06; %Test Samples test pattern
    %force_pattern = 0x07; %RPAT test pattern
    %force_pattern = 0x02; % K28.7 (minimum frequency)
    %force_pattern = 0x03; % D21.5 (maximum frequency)

    liu = 2;
    dev_id0 = 239; % JESD204B device ID for ADC 0
    dev_id1 = 171; % JESD204B device ID for ADC 1
    bank_id = 12; % Bank ID (only low nibble is significant)
    modes = 0;
    %modes=0x18; %Disable FAM/LAM
    %modes=0x1A; %Disable SYSREF

    if(pattern_check ~= 0)
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
    lths = llt.common.LtcControllerComm();
    
    descriptions = ['LTC UFO Board', 'LTC Communication Interface', 'LTC2000 Demoboard', 'LTC2000, DC2085A-A'];
    
    device_info_list = lths.list_controllers(lths.TYPE_HIGH_SPEED);
    device_info = [];
    for info = device_info_list
       if (strfind(descriptions, info.description))
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
  
    while((runs < 1 || continuous == true) && runs_with_errors < 100000)
        
        runs = runs + 1;
        fprintf('LTC2123 Interface Program\n');
        fprintf('Run number: %d\n', runs');
        fprintf('Runs with errors: %d\n', runs_with_errors');
        if (runs_with_uncaught_errors > 0)
            fprintf('***\n***\n***\n*** UNCAUGHT error count: %s !\n***\n***\n***\n',runs_with_uncaught_errors);
        end
        
		%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
		% Configuration Flow Steps 4, 5: 
		% MPSSE Mode, Issue Reset Pulse
		%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        lths.hs_set_bit_mode(cid, lths.HS_BIT_MODE_MPSSE);
        if do_reset
            lths.hs_fpga_toggle_reset(cid);
        end

		%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        % Configuration Flow Step 6:
        % Check ID register
        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        id = lths.hs_fpga_read_data_at_address(cid, ltc2123.ID_REG);
        % fprintf('FPGA ID is %x\n', lths.HsFpgaReadDataAtAddress(cId, lt2k.ID_REG));
        
        if(verbose)
            if(bit_file_id ~= id)
                frpintf('***********************************\n');
                fprintf('Warning!!! Bitfile ID should be 0x%d \n', dec2hex(bit_file_id, 2));
                fprintf('Make sure you know what you are doing...\n');
                fprintf('***********************************\n');
            else
                %frpintf('***********************************\n');
                fprintf('Bitfile ID is 0x%d \n', dec2hex(id, 2));
                fprintf('All good!!\n');
                fprintf('***********************************\n');
            end
        end
        
		%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        % Configuration Flow Step 9, 10: Configure ADC
        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        if(initialize_adcs)
            load_ltc212x(lths, 0, verbose, dev_id0, bank_id, liu, k, modes, 1, pattern0);
            load_ltc212x(lths, 1, verbose, dev_id1, bank_id, liu, k, modes, 1, pattern1);
            initialize_adcs = 0;		% Only initialize on first run
        end
        
        if(initialize_clocks)
            initialize_dc2226_version_2_clocks_250(lths, verbose);
            initialize_clocks = 0;
        end
        
		%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        % Configuration Flow Step 11: Reset Capture Engine
        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        lths.hs_fpga_write_data_at_address(cid, ltc2123.CAPTURE_RESET_REG, 1);  % Reset
        
		%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        % Configuration Flow Step 19: Check Clock Status
        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        if(verbose)
            fprintf('Reading Clock Status register; should be 0x16 (or at least 0x04 bit set)\n');
            fprintf('Register 6   (Clock status) is %x\n', lths.HsFpgaReadDataAtAddress(cid, ltc2123.CLOCK_STATUS_REG));
            pause(sleepTime);
        end
        
		%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        % Configuration Flow Step 11: configure JEDEC Core
        % Refer to Xilinx user manual for detailed register descriptioins
        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        if(initialize_core)
            if(verbose)
                fprintf('Configuring JESD204B core!!\n');
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
        
        if(verbose)
            fprintf('Capturing data and resetting...\n');
        end
        
        channel_data = capture_4_channels(lths, mem_size, buff_size, ...
            dump_data, dump_pscope_data, verbose);
        error_count = 0;
        if(pattern_check ~= 0)
            error_count = pattern_checker(channel_data.data_ch0, ...
                channel_data.num_samps_per_channel, dump_pattern);
            error_count = error_count + pattern_checker(channel_data.data_ch1, ...
                channel_data.num_samps_per_channel, dump_pattern);
            error_count = error_count + pattern_checker(channel_data.data_ch2, ...
                channel_data.num_samps_per_channel, dump_pattern);
            error_count = error_count + pattern_checker(channel_data.data_ch3, ...
                channel_data.num_samps_per_channel, dump_pattern);
            fprintf('error count: %d! \n', error_count);
        end

        if(error_count ~= 0)
            out_file = fopen('LTC2123_python_error_log.txt','a');
            fprintf(out_file,'Caught %d errors on run %d\n', error_count, runs);
            fclose(out_file);
            
            runs_with_errors = runs_with_errors + 1;
            if (channel_data.syncErr == false)
                 runs_with_uncaught_errors = runs_with_uncaught_errors + 1;
            end
            
        end
        
        % Plot data if not running pattern check
        if((plot_data == true) && (pattern_check == false))
            figure
            subplot(4, 1, 1)
            plot(data_ch0)
            title('CH0')
            subplot(4, 1, 2)
            plot(data_ch1)
            title('CH1')
            subplot(4, 1, 3)
            plot(data_ch2)
            title('CH2')
            subplot(4, 1, 4)
            plot(data_ch3)
            title('CH3')

            data_ch0 = data_ch0 - mean(data_ch0);
            data_ch0 = data_ch0' .* llt.common.fft_window(buff_size/2); % Apply BlackmanHarris92 window
            freq_domain_ch0 = fft(data_ch0)/(buff_size/2); % FFT
            freq_domain_magnitude_ch0 = abs(freq_domain_ch0); % Extract magnitude
            freq_domain_magnitude_db_ch0 = 20 * log10(freq_domain_magnitude_ch0/(buff_size/2));

            data_ch1 = data_ch1 - mean(data_ch1);
            data_ch1 = data_ch1' .* llt.common.fft_window(buff_size/2); % Apply BlackmanHarris92 window
            freq_domain_ch1 = fft(data_ch1)/(buff_size/2); % FFT
            freq_domain_magnitude_ch1 = abs(freq_domain_ch1); % Extract magnitude
            freq_domain_magnitude_db_ch1 = 20 * log10(freq_domain_magnitude_ch1/(buff_size/2));
            
            data_ch2 = data_ch2 - mean(data_ch2);
            data_ch2 = data_ch2' .* llt.common.fft_window(buff_size/2); % Apply BlackmanHarris92 window
            freq_domain_ch2 = fft(data_ch2)/(buff_size/2); % FFT
            freq_domain_magnitude_ch2 = abs(freq_domain_ch2); % Extract magnitude
            freq_domain_magnitude_db_ch2 = 20 * log10(freq_domain_magnitude_ch2/(buff_size/2));
            
            data_ch3 = data_ch3 - mean(data_ch3);
            data_ch3 = data_ch3' .* llt.common.fft_window(buff_size/2); % Apply BlackmanHarris92 window
            freq_domain_ch3 = fft(data_ch3)/(buff_size/2); % FFT
            freq_domain_magnitude_ch3 = abs(freq_domain_ch3); % Extract magnitude
            freq_domain_magnitude_db_ch3 = 20 * log10(freq_domain_magnitude_ch3/(buff_size/2));

            figure
            subplot(4,1,1)
            plot(freq_domain_magnitude_db_ch0)
            title('CH0 FFT')
            subplot(4,1,2)
            plot(freq_domain_magnitude_db_ch1)
            title('CH1 FFT')
            subplot(4,1,3)
            plot(freq_domain_magnitude_db_ch2)
            title('CH2 FFT')
            subplot(4,1,4)
            plot(freq_domain_magnitude_db_ch3)
            title('CH3 FFT')
        end
        
        search_start = 5;
        
        [peak0 peak_index0] = max(freq_domain_magnitude_ch3(search_start:buff_size/4));
        [peak1 peak_index1] = max(freq_domain_magnitude_ch1(search_start:buff_size/4));
        [peak2 peak_index2] = max(freq_domain_magnitude_ch2(search_start:buff_size/4));
        [peak3 peak_index3] = max(freq_domain_magnitude_ch3(search_start:buff_size/4));
        
        fprintf('\nFound peaks in these bins:\n');
        fprintf('%d\n', peak_index0 + search_start);
        fprintf('%d\n', peak_index1 + search_start);
        fprintf('%d\n', peak_index2 + search_start);
        fprintf('%d\n', peak_index3 + search_start);
        
        fprintf('\with these phases:\n');
        fprintf('%d\n', angle(freq_domain_ch0(peak_index0 + search_start)));
        fprintf('%d\n', angle(freq_domain_ch0(peak_index1 + search_start)));
        fprintf('%d\n', angle(freq_domain_ch0(peak_index2 + search_start)));
        fprintf('%d\n', angle(freq_domain_ch0(peak_index3 + search_start)));
        
		% Read out JESD204B core registers
        if(verbose)
            read_xilinx_core_config(lths, verbose);
            read_xilinx_core_ilas(lths, verbose, 0);
            read_xilinx_core_ilas(lths, verbose, 1);
            read_xilinx_core_ilas(lths, verbose, 2);
            read_xilinx_core_ilas(lths, verbose, 3);
        end
    end
    
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    %%%    FUNCTION DEFINITIONS    
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    
    function initialize_dc2226_version_2_clocks_250(device, verbose)
        if(verbose)
            fprintf('Configuring clock generators over SPI:\n');
        end
        device.hs_set_bit_mode(cid, device.HS_BIT_MODE_MPSSE);
        fprintf('Configuring LTC6954 (REF distribution)\n');
        device.hs_fpga_write_data_at_address(cid, ltc2123.SPI_CONFIG_REG, 4);
        
		% LTC6954 config
        device.hs_fpga_write_data_at_address(cid, 0, 0);
        device.hs_fpga_write_data_at_address(cid, 2, 128);   % 6951-1 delay
        device.hs_fpga_write_data_at_address(cid, 4, 1);     % 6951-1 divider
        device.hs_fpga_write_data_at_address(cid, 6, 128);   % 6951-2 delay
        device.hs_fpga_write_data_at_address(cid, 8, 1);     % 6951-2 divider
        device.hs_fpga_write_data_at_address(cid, 10, 192);  % sync delay & CMSINV
        device.hs_fpga_write_data_at_address(cid, 12, 1);    % sync divider
        device.hs_fpga_write_data_at_address(cid, 14, 33);
        
        fprintf('Configuring U10 (LTC6951) cp\n');
        % LTC6951config
        device.hs_fpga_write_data_at_address(cid, ltc2123.SPI_CONFIG_REG, 2);
        device.SpiSendByteAtAddress(cid, 0, 5);
        device.SpiSendByteAtAddress(cid, 2, 186);
        device.SpiSendByteAtAddress(cid, 4, 0);
        device.SpiSendByteAtAddress(cid, 6, 124);
        device.SpiSendByteAtAddress(cid, 8, 163);
        device.SpiSendByteAtAddress(cid, 10, 8);
        device.SpiSendByteAtAddress(cid, 12, 5);    % 5 for 200, 6 for 300. VCO=2GHz.
        device.SpiSendByteAtAddress(cid, 14, 7);
        device.SpiSendByteAtAddress(cid, 16, 1);
        device.SpiSendByteAtAddress(cid, 18, 19);
        device.SpiSendByteAtAddress(cid, 20, 192);
        device.SpiSendByteAtAddress(cid, 22, 155);  % ADC SYSREF 2 div, 
        device.SpiSendByteAtAddress(cid, 24, 22);   % ADC SYSREF 2 delay, - 16 for 250, 1E f0r 300
        % device.SpiSendByteAtAddress(cId, 26, 147);   % FFPGA CLK div, 
        device.SpiSendByteAtAddress(cid, 26, 149);   % FPGA CLK div, 0x95 for half of 250
        % device.SpiSendByteAtAddress(cId, 26, 151);   % FPGA CLK div,  0x97 for 1/4 of 250...
        device.SpiSendByteAtAddress(cid, 28, 22);   % FPGA CLK delay, 16 for 250, 1E for 300
        device.SpiSendByteAtAddress(cid, 30, 147);   % ADC CLK 2 div,
        device.SpiSendByteAtAddress(cid, 32, 22);   % ADC CLK 2 delay ,16 for 250, 1E for 300 
        device.SpiSendByteAtAddress(cid, 34, 48);   
        device.SpiSendByteAtAddress(cid, 36, 0);
        device.SpiSendByteAtAddress(cid, 38, 17);
        device.SpiSendByteAtAddress(cid, 4, 1);     % calibrate after writing all registers
        
        fprintf('Configuring U13 (LTC6951) cp\n');
        
        device.hs_fpga_write_data_at_address(cid, ltc2123.SPI_CONFIG_REG, 3);
        device.spi_send_byte_at_address(cid, 0, 5) 
        device.spi_send_byte_at_address(cid, 2, 186) 
        device.spi_send_byte_at_address(cid, 4, 0) 
        device.spi_send_byte_at_address(cid, 6, 124) 
        device.spi_send_byte_at_address(cid, 8, 163) 
        device.spi_send_byte_at_address(cid, 10, 8) 
        device.spi_send_byte_at_address(cid, 12, 5) % 5 for 250, 6 for 300
        device.spi_send_byte_at_address(cid, 14, 7) 
        device.spi_send_byte_at_address(cid, 16, 1) 
        device.spi_send_byte_at_address(cid, 18, 19) 
        device.spi_send_byte_at_address(cid, 20, 192) 
        device.spi_send_byte_at_address(cid, 22, 155) % FPGA SYSREF div, 
        device.spi_send_byte_at_address(cid, 24, 22) % FPGA SYSREF delay, 16 for 250, 1E f0r 300
        device.spi_send_byte_at_address(cid, 26, 147) % ADC CLK 1 div,
        device.spi_send_byte_at_address(cid, 28, 22) % ADC CLK 1 delay, 16 for 250, 1E for 300
        device.spi_send_byte_at_address(cid, 30, 155) % ADC SYSREF 1 div,
        device.spi_send_byte_at_address(cid, 32, 22) % ADC SYSREF 1 delay, 16 for 250, 1E for 300
        device.spi_send_byte_at_address(cid, 34, 48) 
        device.spi_send_byte_at_address(cid, 36, 0) 
        device.spi_send_byte_at_address(cid, 38, 17) 
        device.spi_send_byte_at_address(cid, 4, 1) % calibrate after writing all registers
        
        fprintf('toggle SYNC cp\n');
		% only toggle LTC6951 sync (LTC6954 does not need a sync with DIV=1)
        pause(sleepTime);
        device.hs_fpga_write_data_at_address(cid, ltc2123.SPI_CONFIG_REG, 8);
        fprintf('sync high\n');
        pause(sleepTime);
        fprintf('sync low\n');
        device.hs_fpga_write_data(cid, 0)
        pause(sleepTime);

    end   

    function spi_write(device, address, value)
        device.spi_send_byte_at_address(cid, bitor(address, ltc2123.SPI_WRITE), value);
    end

    function load_ltc212x(device, cs_control, verbose, dev_id, bank_id, ...
            lanes, k, modes, sub_class, pattern)
        if(verbose)
            fprintf('Configuring ADCs over SPI:\n');
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
        
        if(verbose)
            fprintf('ADC %d configuration:\n', cs_control);
            
            device.hs_set_bit_mode(cid, lths.HS_BIT_MODE_MPSSE);
            fprintf('LTC2124 Register Dump: \n');
            fprintf('Register 1: 0x%x\n', device.spi_receive_byte_at_address(cid, 129));
            fprintf('Register 2: 0x%x\n', device.spi_receive_byte_at_address(cid, 130));
            fprintf('Register 3: 0x%x\n', device.spi_receive_byte_at_address(cid, 131));
            fprintf('Register 4: 0x%x\n', device.spi_receive_byte_at_address(cid, 132));
            fprintf('Register 5: 0x%x\n', device.spi_receive_byte_at_address(cid, 133));
            fprintf('Register 6: 0x%x\n', device.spi_receive_byte_at_address(cid, 134));
            fprintf('Register 7: 0x%x\n', device.spi_receive_byte_at_address(cid, 135));
            fprintf('Register 8: 0x%x\n', device.spi_receive_byte_at_address(cid, 136));
            fprintf('Register 9: 0x%x\n', device.spi_receive_byte_at_address(cid, 137));
            fprintf('Register A: 0x%x\n', device.spi_receive_byte_at_address(cid, 138));  
        end

    end 

    function read_xilinx_core_config(device, verbose)
        fprintf('\n\nJEDEC core config registers:')  
        for i = 0 : 15
            reg = i*4;
            [byte3, byte2, byte1, byte0] = read_jesd204b_reg(device, reg);
            fprintf('\n%s : 0x %s %s %s %s', ltc2123.JESD204B_XILINX_CONFIG_REG_NAMES{i + 1}, ...
                dec2hex(byte3, 2), dec2hex(byte2, 2), dec2hex(byte1, 2), dec2hex(byte0, 2));
        end
    end

    function read_xilinx_core_ilas(device, verbose, lane)
        startreg = 2048 + lane * 64;
        fprintf('\n\nILAS and stuff for lane %d :', lane);
        for i = 0 : 12
            reg = startreg + i*4;
            [byte3, byte2, byte1, byte0] = read_jesd204b_reg(device, reg);
            fprintf('\n%s : 0x %s %s %s %s', ltc2123.JESD204B_XILINX_LANE_REG_NAMES{i + 1}, ...
                dec2hex(byte3, 2), dec2hex(byte2, 2), dec2hex(byte1, 2), dec2hex(byte0, 2));
        end
    end

    % Adding support for V6 core, with true AXI access. Need to confirm that this
    % doesn't break anything with V4 FPGA loads,
    % as we'd be writing to undefined registers.
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
    

    % Adding support for V6 core, with true AXI access. Need to confirm that this 
    % doesn't break anything with V4 FPGA loads,
    % as we'd be writing to undefined registers.
    function write_jesd204b_reg(device, address, b3, b2, b1, b0)
        device.hs_fpga_write_data_at_address(cid, ltc2123.JESD204B_WB3_REG, b3);
        device.hs_fpga_write_data_at_address(cid, ltc2123.JESD204B_WB2_REG, b2);
        device.hs_fpga_write_data_at_address(cid, ltc2123.JESD204B_WB1_REG, b1);
        device.hs_fpga_write_data_at_address(cid, ltc2123.JESD204B_WB0_REG, b0);
        device.hs_fpga_write_data_at_address(cid, ltc2123.JESD204B_W2INDEX_REG, (bitand(address, 4032) / 6)); % Upper 6 bits of AXI reg address
        device.hs_fpga_write_data_at_address(cid, ltc2123.JESD204B_CONFIG_REG, (bitor((bitand(address, 63) * 4), 2)));
        x = device.hs_fpga_read_data_at_address(cid, ltc2123.JESD204B_CONFIG_REG);
        if (bitand(x, 1) == 0)
            error('Got bad FPGA status in write_jedec_reg');
        end
    end 

    function channel_data = capture_4_channels(device, mem_size, buff_size, dump_data, ...
            dump_pscope_data, verbose)
		% Configuration Flow Step 11: Reset Capture Engine
		%    device.SetMode(device.ModeMPSSE)
		%    device.FPGAWriteAddress(CAPTURE_RESET_REG) 
		%    device.FPGAWriteData(0x01)  %Reset
		% Step 24
        clockStatus = device.hs_fpga_read_data_at_address(cid, ltc2123.CLOCK_STATUS_REG);

        if(verbose)
            fprintf('Reading Clock Status register; should be 0x16 (or at least 0x04 bit set)\n');
            % fprintf('Register 6   (Clock status) is %x\n', lths.hs_fpga_read_data_at_address(cid, lt2k.CLOCK_STATUS_REG));
            fprintf('Register 6   (Clock status) is %x\n', lths.hs_fpga_read_data_at_address(cid, clockStatus));
        end
		
		% Step 25
        capture_status = device.hs_fpga_read_data_at_address(cid, ltc2123.CAPTURE_STATUS_REG);

        if(bitand(capture_status, 4) ~= 0)
            sync_err = 1;
        else
            sync_err = 0;
        end

        if (verbose ~= 0)
            fprintf('\nReading capture status, should be 0xF0 or 0xF4 (CH0, CH1 valid, Capture NOT done, data not fetched)');
            fprintf('\nAnd it is... 0x%s', dec2hex(capture_status, 4));
        end
		
		% Step 26 in config flow
        device.hs_fpga_write_data_at_address(cid, ltc2123.CAPTURE_CONFIG_REG, uint8(bitor(mem_size, 8))); % Both Channels active
		
		% Step 27
        device.hs_fpga_write_data_at_address(cid, ltc2123.CAPTURE_CONTROL_REG, 0);
        device.hs_fpga_write_data_at_address(cid, ltc2123.CAPTURE_CONTROL_REG, 1);  % Start!!

        pause(1);  % wait for capture

		% Step 28
        capture_status = device.hs_fpga_read_data_at_address(cid, ltc2123.CAPTURE_STATUS_REG);
        if(bitand(capture_status, 4) ~= 0)
            sync_err = 1;
        else
            sync_err = 0;
        end

        if (verbose ~= 0)
            fprintf('\nReading capture status, should be 0xF1 (CH0, CH1, CH2, CH3 valid, Capture  IS done, data not fetched)');
            fprintf('\nAnd it is... 0x%s', dec2hex(capture_status, 4));
        end

        device.data_set_low_byte_first(cid); % Set endian-ness
		% Step 29
        device.hs_set_bit_mode(cid, device.HS_BIT_MODE_FIFO);
        pause(0.1);

		% Step 30
        throw_away = 3;

        [data01, num_samps_read] = device.data_receive_uint16_values(cid, buff_size);

        if(throw_away ~= 0)
            device.data_receive_bytes(cid, throw_away);
        end

		% Step 31 
        device.hs_set_bit_mode(cid, device.HS_BIT_MODE_MPSSE);

        if(verbose ~= 0)
            fprintf('\nRead out %d samples for CH0, 1', num_samps_read);
        end

        % Okay, now get CH2, CH3 data...

        device.hs_set_bit_mode(cid, device.HS_BIT_MODE_MPSSE);
        pause(0.1);
		
		% Step 32
        device.hs_fpga_write_data_at_address(cid, ltc2123.CAPTURE_RESET_REG, 1); % Reset

		% Step 33
        device.hs_fpga_write_data_at_address(cid, ltc2123.CAPTURE_CONFIG_REG, uint8(bitor(mem_size, 10))); % CH2 and CH3

		% Step 34
        device.hs_fpga_write_data_at_address(cid, ltc2123.CAPTURE_CONTROL_REG, 2);
        device.hs_fpga_write_data_at_address(cid, ltc2123.CAPTURE_CONTROL_REG, 3);
		
		% Step 35
        capture_status = device.hs_fpga_read_data_at_address(cid, ltc2123.CAPTURE_STATUS_REG);
        if(bitand(capture_status, 4) ~= 0)
            sync_err = 1;
        else
            sync_err = 0;
        end

        if (verbose ~= 0)
            fprintf('\nReading capture status, should be 0xF1 (CH0, CH1, CH2, CH3 valid, Capture  IS done, data not fetched)');
            fprintf('\nAnd it is... 0x%s', dec2hex(capture_status, 4));
        end

		% Step 36
        device.hs_set_bit_mode(cid, device.HS_BIT_MODE_FIFO);
        pause(0.1);

		% Step 37
        [data23, num_samps_read] = device.data_receive_uint16_values(cid, buff_size);

        if(throw_away ~= 0)
            device.data_receive_bytes(cid, throw_away);
        end

        device.hs_set_bit_mode(cid, device.HS_BIT_MODE_MPSSE);
        pause(0.1);

        if(verbose ~= 0)
            fprintf('\nRead out %d samples for CH2, 3\n', num_samps_read);
        end

        % Initialize data arrays
        data_ch0 = zeros(1, buff_size/2);
        data_ch1 = zeros(1, buff_size/2);
        data_ch2 = zeros(1, buff_size/2);
        data_ch3 = zeros(1, buff_size/2);

        for i = 1 : 2 : (buff_size)/2
            % Split data for CH0, CH1
            data_ch0(i) = data01(i*2 - 1);
            data_ch0(i+1) = data01(i*2);
            data_ch1(i) = data01(i*2 + 1);
            data_ch1(i+1) = data01(i*2 + 2);

            % Split data for CH2, CH3
            data_ch2(i) = data23(i*2 - 1);
            data_ch2(i+1) = data23(i*2);
            data_ch3(i) = data23(i*2 + 1);
            data_ch3(i+1) = data23(i*2 + 2);
        end
        
        if(dump_data ~= 0)
            for i = 1:min(dump_data, buff_size)
                fprintf('0x%s \t 0x%s \t 0x%s \t 0x%s\n', dec2hex(data_ch0(i), 4), ...
                    dec2hex(data_ch1(i), 4), dec2hex(data_ch2(i), 4), dec2hex(data_ch3(i), 4));
            end
        end
        
        num_samps_per_channel = num_samps_read/2;
        channel_data = [data_ch0, data_ch1, data_ch2, data_ch3, num_samps_per_channel, sync_err];
    end % end of function
end