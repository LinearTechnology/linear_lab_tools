% DC1974 / LTC2123 Register definitions and bitfield definitions
% 
% Demo board documentation:
% http://www.linear.com/demo/1974
% http://www.linear.com/product/LTC2123#demoboards
% 
% LTC2123 product page
% http://www.linear.com/product/LTC2123
%  
% REVISION HISTORY
% $Revision: 6108 $
% $Date: 2016-11-30 10:34:36 -0800 (Wed, 30 Nov 2016) $
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

function ltc2123 = ltc2123_constants

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% SPI read / write bit definitions %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

ltc2123.SPI_READ = 128; % OR with register
ltc2123.SPI_WRITE = 0;

% FPGA register addresses
ltc2123.ID_REG = 0;
ltc2123.CAPTURE_CONFIG_REG = 1;
ltc2123.CAPTURE_CONTROL_REG = 2;
ltc2123.CAPTURE_RESET_REG = 3;
ltc2123.CAPTURE_STATUS_REG = 4;
ltc2123.SPI_CONFIG_REG = 5;
ltc2123.CLOCK_STATUS_REG = 6;
ltc2123.JESD204B_WB0_REG = 7;
ltc2123.JESD204B_WB1_REG = 8;
ltc2123.JESD204B_WB2_REG = 9;
ltc2123.JESD204B_WB3_REG = 10;
ltc2123.JESD204B_CONFIG_REG = 11;
ltc2123.JESD204B_RB0_REG = 12;
ltc2123.JESD204B_RB1_REG = 13;
ltc2123.JESD204B_RB2_REG = 14;
ltc2123.JESD204B_RB3_REG = 15;
ltc2123.JESD204B_CHECK_REG = 16;

ltc2123.JESD204B_W2INDEX_REG = 18;
ltc2123.JESD204B_R2INDEX_REG = 19;

% Register names for basic configuration
ltc2123.JESD204B_XILINX_CONFIG_REG_NAMES = {'             Version', '               Reset', '         ILA Support', '          Scrambling',...
                                    '     SYSREF Handling', '         Reserved...', '          Test Modes', '  Link err stat, 0-7',...
                                    '        Octets/frame', 'frames/multiframe(K)', '        Lanes in Use', '            Subclass',...
                                    '        RX buf delay', '     Error reporting', '         SYNC Status', ' Link err stat, 8-11'};

% Register names for per-lane information
ltc2123.JESD204B_XILINX_LANE_REG_NAMES = {'  ILA config Data 0', '  ILA config Data 1', '  ILA config Data 2', '  ILA config Data 3',... 
                                  '  ILA config Data 4', '  ILA config Data 5', '  ILA config Data 6', '  ILA config Data 7',...
                                  '  Test Mode Err cnt', '       Link Err cnt', '  Test Mode ILA cnt', 'Tst Mde multif. cnt',...
                                  '      Buffer Adjust'};
                              
%lookup byte to write based on collect size                              
ltc2123.mem_size_byte = containers.Map;
ltc2123.mem_size_byte(128) = 0;
ltc2123.mem_size_byte(256) = 16;
ltc2123.mem_size_byte(512) = 32;
ltc2123.mem_size_byte(1024) = 48;
ltc2123.mem_size_byte(2*1024) = 64;
ltc2123.mem_size_byte(4*1024) = 80;
ltc2123.mem_size_byte(8*1024) = 96;
ltc2123.mem_size_byte(16*1024) = 112;
ltc2123.mem_size_byte(32*1024) = 128;
ltc2123.mem_size_byte(64*1024) = 144;
ltc2123.mem_size_byte(128*1024) = 160;

end