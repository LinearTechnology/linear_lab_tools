function plot(data, num_bits, channel, verbose)
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

num_samples = length(data);
    
figure(2*channel+1)
plot(data)
title(sprintf('Ch %d : Time Domain Samples', channel))

if verbose; fprintf('FFT''ing channel %d data.\n', channel); end

adc_amplitude = 2.0^(num_bits-1);
data_no_dc = double(data);
data_no_dc = data_no_dc - mean(data_no_dc); % Remove DC to avoid leakage when windowing
window = llt.common.fft_window(num_samples);
windowed_data = double(data_no_dc(:)) .* window;
freq_domain = fft(windowed_data);
freq_domain = freq_domain(1:(num_samples/2+1));
freq_domain_magnitude = abs(freq_domain);
freq_domain_magnitude = freq_domain_magnitude / num_samples;
freq_domain_magnitude(2:num_samples/2) = freq_domain_magnitude(2:num_samples/2) * 2;
freq_domain_magnitude_db = 20*log10(freq_domain_magnitude/adc_amplitude);

if verbose; fprintf('Plotting channel %d frequency domain.\n', channel); end

figure(2*channel+2);
title(sprintf('Ch %d: FFT', channel))
plot(freq_domain_magnitude_db);
