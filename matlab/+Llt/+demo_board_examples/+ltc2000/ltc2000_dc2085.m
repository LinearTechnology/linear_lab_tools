% DC2085 / LTC2000 Interface Example
% LTC2000: 16-/14-/11- Bit 2.5 Gsps DAcs
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
% REVISION HISTORY
% $Revision: 6110 $
% $Date: 2016-11-30 13:34:08 -0800 (Wed, 30 Nov 2016) $
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

function ltc2000_dc2085(num_samples, is_verbose)

    AMPLITUDE = 32000;
    NUM_CYCLES = 800;   % Number of sinewave cycles over the entire data record
    SLEEP_TIME = 0.1;

    if ~exist('num_samples', 'var'); num_samples = 64*1024; end
    if ~exist('is_verbose', 'var'); is_verbose = nargout == 0; end

    if is_verbose
        fprintf('LTC2000 Test Script\n');
    end

    % Import LTC2000 definitions and support functions
    ltc2000 = llt.demo_board_examples.ltc2000.ltc2000_constants();

    % Returns the object in the class constructor
    lths = llt.common.LtcControllerComm();

    device_info_list = lths.list_controllers(lths.TYPE_HIGH_SPEED);
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

    fprintf('FPGA Load ID is %X\n', lths.hs_fpga_read_data_at_address(did, ltc2000.FPGA_ID_REG));
    fprintf('Reading PLL status, should be 0x47\n');
    data = lths.hs_fpga_read_data_at_address(did, ltc2000.FPGA_STATUS_REG);
    fprintf('And it is... 0x%s\n', dec2hex(data));
    fprintf('Turning on DAC...\n');
    
    lths.hs_fpga_write_data_at_address(did, ltc2000.FPGA_DAC_PD, 1);

    pause(SLEEP_TIME);

    if is_verbose
        fprintf('Configuring ADC over SPI\n');
    end

    % Initial register values can be taken directly from LTDACGen.
    % Refer to LTC2000 datasheet for detailed register descriptions.

    spi_write(ltc2000.REG_RESET_PD, 0);
    spi_write(ltc2000.REG_CLK_CONFIG, 2);    % setting output current to 7mA?
    spi_write(ltc2000.REG_CLK_PHASE, 7);     % DCKIP/N delay = 315 ps
    spi_write(ltc2000.REG_PORT_EN, 11);      % Enables Port A and B Rxs and allows DAC to be updated from A and B
    spi_write(ltc2000.REG_SYNC_PHASE, 0);
    spi_write(ltc2000.REG_LINER_GAIN, 0);
    spi_write(ltc2000.REG_LINEARIZATION, 8);
    spi_write(ltc2000.REG_DAC_GAIN, 32);
    spi_write(ltc2000.REG_LVDS_MUX, 0);
    spi_write(ltc2000.REG_TEMP_SELECT, 0);
    spi_write(ltc2000.REG_PATTERN_ENABLE, 0);

    pause(SLEEP_TIME);

    % Optionally read back all registers
    if is_verbose
        fprintf('LTC2000 Register Dump:\n');
        for k = 0:9
            fprintf('Register %d: 0x%02X\n', k, spi_read(k));
        end
    end

    lths.hs_fpga_write_data_at_address(did, ltc2000.FPGA_CONTROL_REG, 32);

    pause(SLEEP_TIME);

    % Demonstrates how to generate sinusoidal data. Note that the total data 
    % record length contains an exact integer number of cycles.
    data = round(AMPLITUDE * sin((NUM_CYCLES * 2 * pi / num_samples) * ...
        (0:(num_samples - 1))));

    % Demonstrates how to generate sinc data.
    sinc_data = zeros(num_samples, 1);
    for i = 1:num_samples
    x = ((i - 32768) / (512.0)) + 0.0001;
    sinc_data(i) = int16((32000 * (sin(x) / x)));
    end

    % Demonstrates how to write generated data to a file.
    fprintf('writing data out to file')
    outFile = fopen('dacdata_sinc.csv', 'w');
    for i = 1 : num_samples
        fprintf(outFile, '%d\n', sinc_data(i));
    end
    fclose(outFile);
    fprintf('\ndone writing!')

    % Demonstrates how to read data in from a file.
    in_data = zeros(num_samples, 1);
    fprintf('\nreading data from file')
    in_file = fopen('dacdata_sinc.csv', 'r');
    for i = 1: num_samples 
        in_data(i) = str2double(fgetl(in_file));
    end
    fclose(in_file);
    fprintf('\ndone reading!')

    lths.hs_set_bit_mode(did, lths.HS_BIT_MODE_FIFO);
    % DAC should start running here!
    num_bytes_sent = lths.data_send_uint16_values(did, data);
    fprintf('\nnumBytesSent (should be %d) = %d\n', num_samples * 2, ...
        num_bytes_sent);
    fprintf('You should see a waveform at the output of the LTC2000 now!\n');
    
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    %%%    FUNCTION DEFINITIONS    
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    
    function spi_write(address, value)
        lths.spi_send_byte_at_address(did, bitor(address, ltc2000.SPI_WRITE), value);
    end

    function value = spi_read(address)
        value = lths.spi_receive_byte_at_address(did, bitor(address, ltc2000.SPI_READ));
    end

end