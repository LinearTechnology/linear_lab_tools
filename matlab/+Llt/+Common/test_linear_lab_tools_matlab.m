% Simple program to validate that MATLAB was installed properly and
% instructions on how to proceed to DemoBoardExamples
%  
% REVISION HISTORY
% $Revision: 4256 $
% $Date: 2015-10-19 13:15:40 -0700 (Mon, 19 Oct 2015) $
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

% Choices for LTC parts: 2048 for NON-LTC2440 family, 64 to 32768 for LTC2440
osr = 1024; 
sinc1 = ones(1, osr/4);
sinc2 = conv(sinc1, sinc1);
sinc4 = conv(sinc2, sinc2);
reverser = zeros(1, osr*2);
reverser(1) = 1;
reverser(osr + 1) = 1;
sinc4_w_rev = conv(sinc4, reverser);
sinc4_w_rev = sinc4_w_rev / sum(sinc4_w_rev);

fft_data = fft(sinc4_w_rev, 2*16385);
fft_data = fft_data(1:end/2);
plot(20 * log10(abs(fft_data)));
axis([0 1000 -140 0]);
title('Congratulations! Matlab is installed properly!');
xlabel('Frequency');
ylabel('Rejection');

fprintf('\nYou are all set to run demo board example codes. Please make sure:\n');
fprintf('1. Add the absolute path to "linear_lab_tools\\matlab".\n');
fprintf('2. (Only once) run "mex -setup" to set up a C compiler (32-bit Matlab comes with "Lcc-win32 C").\n.');
