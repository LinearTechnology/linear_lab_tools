% DC2303 / LTC2000 Interface Example
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
% http://www.linear.com/demo/2303
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

function ltc2000_dc2303(data, spi_regs, is_verbose)
    if nargin == 0
        data = make_sample_data();
        spi_regs = [ ...
        ... addr, value
            1,    0,  ...
            2,    2,  ...
            3,    7,  ...
            4,    11, ...
            5,    0,  ...
            7,    0,  ...
            8,    8,  ...
            9,    32, ...
            24,   0,  ...
            25,   0,  ...
            30,   0   ...
          ];
        is_verbose = true;
    else
        if ~exist('spi_regs', 'var'); spi_regs = []; end
        if ~exist('is_verbose', 'var'); is_verbose = false; end
    end
    
    lcc = llt.common.LtcControllerComm();
    ltc2000 = llt.demo_board_examples.ltc2000.Ltc2000(lcc, true, spi_regs, is_verbose);
    ltc2000.send_data(data);    
end

function data = make_sample_data()
    AMPLITUDE = 32000;
    NUM_SAMPLES = 64 * 1024;
    NUM_CYCLES = 800;   % Number of sinewave cycles over the entire data record
    data = round(AMPLITUDE * sin((NUM_CYCLES * 2 * pi / NUM_SAMPLES) * ...
        (0:(NUM_SAMPLES - 1))));
end
