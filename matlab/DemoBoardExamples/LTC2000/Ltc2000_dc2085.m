
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

function Ltc2000_dc2085

clear all;
AMPLITUDE = 16000;
NUM_CYCLES = 800;   % Number of sinewave cycles over the entire data record
VERBOSE = true;
SLEEP_TIME = 0.1;
NUM_SAMPLES = 65536;    % n.BuffSize

if VERBOSE
    fprintf('LTC2000 Test Script\n');
end

% Import LTC2000 definitions and support functions
[lt2k] = ltc2000Constants();

% Returns the object in the class constructor
controller = LtcControllerComm();

controllerInfoList = controller.ListControllers();
controllerInfo = [];
for info = controllerInfoList
   if strcmp(info.description(1:7), 'LTC2000')
       controllerInfo = info;
   end
end

if isempty(controllerInfo)
    error('TestLtcControllerComm:noDevice', 'No LTC200 demo board detected');
end

fprintf('Found LTC2000 demo board:\n');
fprintf('Description: %s\n', controllerInfo.description);
fprintf('Serial Number: %s\n', controllerInfo.serialNumber);

% init a device and get an id
did = controller.Init(controllerInfo);

controller.HsSetBitMode(did, controller.BIT_MODE_MPSSE);
controller.HsFpgaToggleReset(did);

fprintf('FPGA ID is %X\n', controller.FpgaReadDataAtAddress(did, lt2k.FPGA_ID_REG));

controller.HsFpgaWriteDataAtAddress(did, lt2k.FPGA_DAC_PD, 1);
      
pause(SLEEP_TIME);

if VERBOSE
    fprintf('Configuring ADC over SPI\n');
end

% Initial register values can be taken directly from LTDACGen.
% Refer to LTC2000 datasheet for detailed register descriptions.

SpiWrite(lt2k.REG_RESET_PD, 0);
SpiWrite(lt2k.REG_CLK_CONFIG, 2);    % setting output current to 7mA?
SpiWrite(lt2k.REG_CLK_PHASE, 7);     % DCKIP/N delay = 315 ps
SpiWrite(lt2k.REG_PORT_EN, 11);      % Enables Port A and B Rxs and allows DAC to be updated from A and B
SpiWrite(lt2k.REG_SYNC_PHASE, 0);
SpiWrite(lt2k.REG_LINER_GAIN, 0);
SpiWrite(lt2k.REG_LINEARIZATION, 8);
SpiWrite(lt2k.REG_DAC_GAIN, 32);
SpiWrite(lt2k.REG_LVDS_MUX, 0);
SpiWrite(lt2k.REG_TEMP_SELECT, 0);
SpiWrite(lt2k.REG_PATTERN_ENABLE, 0);

pause(SLEEP_TIME);

% Optionally read back all registers
if VERBOSE
    fprintf('LTC2000 Register Dump:\n');
    for k = 1:9
        fprintf('Register %d: 0x%02X\n', k, SpiRead(k));
    end
end

controller.HsFpgaWriteDataAtAddress(did, lt2k.FPGA_CONTROL_REG, 32);

pause(SLEEP_TIME);

% Demonstrates how to generate sinusoidal data. Note that the total data 
% record length contains an exact integer number of cycles.
data = round(AMPLITUDE * sin((NUM_CYCLES * 2 * pi / NUM_SAMPLES) * ...
    (0:(NUM_SAMPLES - 1))));

% Demonstrates how to generate sinc data.
sinc_data = zeros(NUM_SAMPLES, 1);
for i = 1:NUM_SAMPLES
x = ((i - 32768) / (512.0)) + 0.0001;
sinc_data(i) = int16((32000 * (sin(x) / x)));
end

% Demonstrates how to write generated data to a file.
fprintf('writing data out to file')
outfile = fopen('dacdata_sinc.csv', 'w');
for i = 1 : NUM_SAMPLES
    fprintf(outfile, '%d\n', sinc_data(i));
end
fclose(outfile);
fprintf('\ndone writing!')

% Demonstrates how to read data in from a file.
indata = zeros(NUM_SAMPLES, 1);
fprintf('\nreading data from file')
infile = fopen('dacdata_sinc.csv', 'r');
for i = 1: NUM_SAMPLES 
    indata(i) = str2double(fgetl(infile));
end
fclose(infile);
fprintf('\ndone reading!')

controller.HsSetBitMode(did, controller.BIT_MODE_FIFO);
% DAC should start running here!
numBytesSent = controller.DataSendUint16Values(did, indata);
fprintf('numBytesSent (should be %d) = %d\n', NUM_SAMPLES * 2, ...
    numBytesSent);


function SpiWrite(address, value)
        controller.SpiSendByteAtAddress(did, bitor(address, lt2k.SPI_WRITE), value);
    end

    function value = SpiRead(address)
        value = controller.SpiReceiveByteAtAddress(did, bitor(address, lt2k.SPI_READ));
    end

end