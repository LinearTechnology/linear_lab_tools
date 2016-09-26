function Plot(data, nBits, channel, verbose)
% Plots time-domain and frequency-domain of a single channel
% 
% nBits is required to correctly scale FFT, channel is just the channel
% number used in the plot title.
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

if ~exist('channel', 'var'); channel = 0; end
if ~exist('verbose', 'var'); verbose = false; end

if verbose; fprintf('Plotting channel %d time domain.\n', channel); end

nSamples = length(data);
    
figure(2*channel+1)
plot(data)
title(sprintf('Ch %d : Time Domain Samples', channel))

if verbose; fprintf('FFT''ing channel %d data.\n', channel); end

adcAmplitude = 2.0^(nBits-1);
dataNoDc = double(data);
dataNoDc = dataNoDc - mean(dataNoDc); % Remove DC to avoid leakage when windowing
window = Llt.Common.Window(nSamples);
windowedData = double(dataNoDc(:)) .* window;
freqDomain = fft(windowedData);
freqDomain = freqDomain(1:(nSamples/2+1));
freqDomainMagnitude = abs(freqDomain);
freqDomainMagnitude = freqDomainMagnitude / nSamples;
freqDomainMagnitude(2:nSamples/2) = freqDomainMagnitude(2:nSamples/2) * 2;
freqDomainMagnitudeDb = 20*log10(freqDomainMagnitude/adcAmplitude);

if verbose; fprintf('Plotting channel %d frequency domain.\n', channel); end

figure(2*channel+2);
title(sprintf('Ch %d: FFT', channel))
plot(freqDomainMagnitudeDb);
