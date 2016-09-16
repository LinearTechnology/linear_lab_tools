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
% $Revision$
% $Date$
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

function Ltc2000Dc2085(arg1NumSamples, arg2Verbose)

    AMPLITUDE = 16000;
    NUM_CYCLES = 800;   % Number of sinewave cycles over the entire data record
    SLEEP_TIME = 0.1;

    if(~nargin)
        numSamples = 65536;    % n.BuffSize
        % Print extra information to console
        verbose = true;
    else
        numSamples = arg1NumSamples;
        verbose = arg2Verbose;
    end

    if verbose
        fprintf('LTC2000 Test Script\n');
    end

    % Import LTC2000 definitions and support functions
    lt2k = Llt.DemoBoardExamples.LTC2000.Ltc2000Constants();

    % Returns the object in the class constructor
    lths = Llt.Common.LtcControllerComm();

    deviceInfoList = lths.ListControllers(lths.TYPE_HIGH_SPEED);
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

    fprintf('FPGA Load ID is %X\n', lths.HsFpgaReadDataAtAddress(did, lt2k.FPGA_ID_REG));
    fprintf('Reading PLL status, should be 0x47\n');
    data = lths.HsFpgaReadDataAtAddress(did, lt2k.FPGA_STATUS_REG);
    fprintf('And it is... 0x%s\n', dec2hex(data));
    fprintf('Turning on DAC...\n');
    
    lths.HsFpgaWriteDataAtAddress(did, lt2k.FPGA_DAC_PD, 1);

    pause(SLEEP_TIME);

    if verbose
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
    if verbose
        fprintf('LTC2000 Register Dump:\n');
        for k = 0:9
            fprintf('Register %d: 0x%02X\n', k, SpiRead(k));
        end
    end

    lths.HsFpgaWriteDataAtAddress(did, lt2k.FPGA_CONTROL_REG, 32);

    pause(SLEEP_TIME);

    % Demonstrates how to generate sinusoidal data. Note that the total data 
    % record length contains an exact integer number of cycles.
    data = round(AMPLITUDE * sin((NUM_CYCLES * 2 * pi / numSamples) * ...
        (0:(numSamples - 1))));

    % Demonstrates how to generate sinc data.
    sincData = zeros(numSamples, 1);
    for i = 1:numSamples
    x = ((i - 32768) / (512.0)) + 0.0001;
    sincData(i) = int16((32000 * (sin(x) / x)));
    end

    % Demonstrates how to write generated data to a file.
    fprintf('writing data out to file')
    outFile = fopen('dacdata_sinc.csv', 'w');
    for i = 1 : numSamples
        fprintf(outFile, '%d\n', sincData(i));
    end
    fclose(outFile);
    fprintf('\ndone writing!')

    % Demonstrates how to read data in from a file.
    inData = zeros(numSamples, 1);
    fprintf('\nreading data from file')
    inFile = fopen('dacdata_sinc.csv', 'r');
    for i = 1: numSamples 
        inData(i) = str2double(fgetl(inFile));
    end
    fclose(inFile);
    fprintf('\ndone reading!')

    lths.HsSetBitMode(did, lths.HS_BIT_MODE_FIFO);
    % DAC should start running here!
    numBytesSent = lths.DataSendUint16Values(did, inData);
    fprintf('\nnumBytesSent (should be %d) = %d\n', numSamples * 2, ...
        numBytesSent);
    fprintf('You should see a waveform at the output of the LTC2000 now!\n');
    
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    %%%    FUNCTION DEFINITIONS    
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    
    function SpiWrite(address, value)
        lths.SpiSendByteAtAddress(did, bitor(address, lt2k.SPI_WRITE), value);
    end

    function value = SpiRead(address)
        value = lths.SpiReceiveByteAtAddress(did, bitor(address, lt2k.SPI_READ));
    end

end