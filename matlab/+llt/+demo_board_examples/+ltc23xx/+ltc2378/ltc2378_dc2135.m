% DC2135 or DC1925 / LTC2378-20 Interface Example
% LTC2378: 20-Bit, 1Msps, Low Power SAR ADC
%
% This program demonstrates how to communicate with the LTC2378-20 demo board 
% using Matlab.
% 
% Board setup is described in Demo Manual 1925 or 2135. Follow the procedure in 
% the manual, and verify operation with the PScope software. Once 
% operation is verified, exit PScope and run this script.
% 
% Demo board documentation:
% http://www.linear.com/demo/1925
% http://www.linear.com/demo/2135
% http://www.linear.com/product/LTC2378-20#demoboards
% 
% LTC2378-20 product page
% http://www.linear.com/product/LTC2378-20
%  
% REVISION HISTORY
% $Revision: 4272 $
% $Date: 2015-10-20 10:33:43 -0700 (Tue, 20 Oct 2015) $
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

function ltc2378_dc2135(num_samples, is_verbose, do_plot, do_write_to_file)

if ~exist('num_samples', 'var'); num_samples = 32*1024; end
do_demo = false;
if nargout == 0; do_demo = true; end
if ~exist('is_verbose', 'var'); is_verbose = do_demo; end
if ~exist('do_plot', 'var'); do_plot = do_demo; end
if ~exist('do_write_to_file', 'var'); do_write_to_file = do_demo; end
      
SAMPLE_BYTES = 4; % for 32-bit reads

% Returns the object in the class constructor
comm = llt.common.LtcControllerComm();  

device_info_list = comm.list_controllers(comm.TYPE_DC890);

% Open communication to the device
cid = comm.init(device_info_list);

% find demo board with correct ID
eeprom_id_size = 50;
fprintf('\nLooking for a DC890 with a DC2135A-A demoboard');

for info = device_info_list
    % if strcmp(EEPROM_ID, comm.eeprom_read_string(cid, eepromIdSize))
    if(~isempty(strfind(comm.eeprom_read_string(cid, eeprom_id_size), 'DC2135'))...
        || ~isempty(strfind(comm.eeprom_read_string(cid, eeprom_id_size), 'DC1925')));
        break;
    end

    cid = comm.cleanup(cid);
end

if(cid == 0)
    fprintf('\nDevice not found');
else
    fprintf('\nDevice Found');
end

if (~comm.fpga_get_is_loaded(cid, 'CMOS'))
   if(is_verbose)
        fprintf('\nLoading FPGA');
   end 
   comm.fpga_load_file(cid, 'CMOS');
else
   if(is_verbose)
        fprintf('\nFPGA already loaded');
   end 
end

if(is_verbose)
    fprintf('\nStarting Data Collect');
end 

comm.data_set_high_byte_first(cid);

comm.data_set_characteristics(cid, true, SAMPLE_BYTES, true);
comm.data_start_collect(cid, num_samples, comm.TRIGGER_NONE);

for i = 1: 10
    is_done = comm.data_is_collect_done(cid);
    if(is_done)
        break;
    end
    pause(0.2);
end

if(is_done ~= true)
    error('LtcControllerComm:HardwareError', 'Data collect timed out (missing clock?)');
end

if(is_verbose)
    fprintf('\nData Collect done');
end

comm.dc890_flush(cid);

if(is_verbose)
    fprintf('\nReading data');
end

raw_data = comm.DataReceiveUint32Values(cid, num_samples);

if(is_verbose)
    fprintf('\nData Read done');
end

for i = 1 : num_samples
    raw_data(i) = bitand(raw_data(i), 1048575);
end
data = zeros(1,num_samples);
for i = 1 : num_samples
    if(raw_data(i) > 524287)
        data(i) = int32(1048576 - raw_data(i));
        data(i) = (-1) * int32(data(i));
    else
        data(i) = int32(raw_data(i));
    end
end


if(do_write_to_file)
    if(is_verbose)
        fprintf('\nWriting data to file');
    end    

    file_id = fopen('data.txt','w');

    for i = 1:num_samples
        fprintf(file_id,'%d\r\n', data(i));
    end

    fclose(file_id);
    fprintf('\nFile write done');
end

% Plot data if not running pattern check
if(do_plot == true)
    figure(1)
    plot(data)
    title('Time Domain Samples')

    adc_amplitude = 1048576.0 / 2.0;

    window_scale = (num_samples) / sum(llt.common.fft_window(num_samples));
    fprintf('\nWindow scaling factor: %d', window_scale);

    data_no_dc = data - mean(data);      % Remove DC to avoid leakage when windowing
    windowed_data = data_no_dc .* (llt.common.fft_window(num_samples))';
    windowed_data = windowed_data .* window_scale; 	% Apply BlackmanHarris92 window
    freq_domain_data = fft(windowed_data)/(num_samples); % FFT
    freq_domain_magnitude_data = abs(freq_domain_data); 		% Extract magnitude
    freq_domain_magnitude_db_data = 20 * log10(freq_domain_magnitude_data/adc_amplitude);

    figure(2)
    plot(freq_domain_magnitude_db_data)
    title('FFT')

end
fprintf('\nAll finished');
    
end