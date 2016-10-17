function win = FftWindow(n, windowType)
% Generates a window for reducing sidelobes due to FFT of incoherently sampled data.
% 
% Window type is a case INsensitive string and can be one of:
%   'Hamming', 'Hann', 'Blackman', 'BlackmanExact', 'BlackmanHarris70',
%   'FlatTop', 'BlackmanHarris92'
% The default window type is 'BlackmanHarris92'
%
% Copyright (c) 2015, Linear Technology Corp.(LTC)
% All rights reserved.
% 
% Redistribution and use in source and binary forms, with or without
% modification, are permitted provided that the following conditions are met:
% 
% 1. Redistributions of source code must retain the above copyright notice, 
%    this list of conditions and the following disclaimer.
% 2. Redistributions in binary form must reproduce the above copyright 
%    notice, this list of conditions and the following disclaimer in the 
%    documentation and/or other materials provided with the distribution.
% 
% THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
% AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE 
% IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE 
% ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE 
% LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
% CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF 
% SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS 
% INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN 
% CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
% ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE 
% POSSIBILITY OF SUCH DAMAGE.
% 
% The views and conclusions contained in the software and documentation are 
% those of the authors and should not be interpreted as representing official
% policies, either expressed or implied, of Linear Technology Corp.

    if ~exist('windowType', 'var')
        windowType = 'BlackmanHarris92';
    end
    
    switch lower(windowType)
        case 'hamming'
            win = OneCos(n, 0.54, 0.46, 1.586303);
    
        case 'hann'
            win = OneCos(n, 0.50, 0.50, 1.632993);
    
        case 'blackman'
            win = TwoCos(n, 0.42, 0.50, 0.08, 1.811903);

        case 'blackmanexact'
            win = TwoCos(n, 0.42659071, 0.49656062, 0.07684867, 1.801235);

	    case 'blackmanharris70' % from: www.mathworks.com/access/helpdesk/help/toolbox/signal/window.shtml
            win = TwoCos(n, 0.42323, 0.49755, 0.07922, 1.807637);

        case 'flattop'
            win = TwoCos(n, 0.2810639, 0.5208972, 0.1980399, 2.066037);
        
        case 'blackmanharris92' % from: www.mathworks.com/access/helpdesk/help/toolbox/signal/window.shtml
            win = ThreeCos(n, 0.35875, 0.48829, 0.14128, 0.01168, 1.968888);
        
        otherwise
            error('Window:BadWindowType', 'Unexpected window type %s', windowType);
    end
end

function win = OneCos(n, a0, a1, norm)
    nMinus1 = n - 1;
    t = (0:nMinus1) / nMinus1;
    win = a0 - a1 * cos(2*pi * t);
    win = win(:) * norm;
end

function win = TwoCos(n, a0, a1, a2, norm)
    nMinus1 = n - 1;
    t = (0:nMinus1) / nMinus1;
    win = a0 - a1*cos(2*pi * t) + a2*cos(4*pi * t);
    win = win(:) * norm;
end

function win = ThreeCos(n, a0, a1, a2, a3, norm)
    nMinus1 = n - 1;
    t = (0:nMinus1) / nMinus1;
    win = a0 - a1*cos(2*pi * t) + a2*cos(4*pi * t) - a3*cos(6*pi * t);
    win = win(:) * norm;
end
        
