% Demonstration of how a FFT works.
% 
% REVISION HISTORY
% $Revision: 6098 $
% $Date: 2016-11-29 12:08:36 -0800 (Tue, 29 Nov 2016) $
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

% first, let's make a sinewave with some noise:
bin_number = 2.0;
amplitude = 1.0;
mu = 0;
sigma = 0.1;

num_bins = 32; % This is also the number of points in the time record
data = zeros(1, num_bins);

noise = sigma.*randn(num_bins,1) + mu;

% Generate some input data
for i = 1:num_bins
    data(i)= amplitude * sin(2 * pi * bin_number * i / num_bins);
    data(i) = data(i) + noise(i);
end
    
% And lets take its FFT using MATLAB's FFT function, and tuck it away for later
fft_magnitude = abs(fft(data) / length(data));

% Okay, now let's deconstruct the FFT a bit. And by "a bit", we mean "a LOT!"
% We've already got the data that we
% want to analyze, so the next step is to make two, 2-d arrays of "test sinusoids"
% where one consists of cosines to detect the real part of a frequency component,
% and the other consists of sines to detect the imaginary part:

test_cosines = zeros(num_bins, num_bins);
test_sines = zeros(num_bins, num_bins);
for freq = 1 : num_bins
    for time = 1: num_bins
        test_cosines(freq, time) = cos(2*pi * (freq-1) * time / num_bins);
        test_sines(freq, time) = sin(2*pi * (freq-1) * time / num_bins);
    end
end

% The next step is to multiply the "test sinusoids" by the original data, one
% frequency at a time to see if "anybody's home". You actually only need to
% "multiply and accumulate", such that one test sinusoid will produce a single
% number. But we want to plot the results, so we're going to construct arrays
% (the "multiply" part) and then sum the elements (the "accumulate" part.)

result_cosines = zeros(num_bins, num_bins);
result_sines = zeros(num_bins, num_bins);

for freq = 1 : num_bins
    result_cosines(freq, 1:32) = test_cosines(freq, 1:32) .* data(1:32);
    result_sines(freq, 1:32) = test_sines(freq, 1:32) .* data(1:32);
end

% This is the final step! Sum the elements of the result arrays, which gives
% you the real and imaginary parts of the DFT:
real_part = zeros(1, num_bins);
imag_part = zeros(1, num_bins);

for freq = 1 : num_bins
    real_part(freq) = sum(result_cosines(freq, 1:32));
    imag_part(freq) = sum(result_sines(freq, 1:32));
end
% Calculate magnitude of each frequency component (considering real and imaginary parts)
for freq = 1:32
    magnitude(freq) = sqrt(real_part(freq) ^ 2 + imag_part(freq) ^ 2);
end

figure(2)
title('Data and test sinusoids for bins 0-15')
%ax = gca()
%ax.set_axis_bgcolor('%C0C0C0')

%lines = plot(zones_ltc2057_psd(0))

freq = 1:32;
for f = 1 : num_bins
    if(f<=16)
        figure(2)
        subplot(4, 4, f)
    else
        figure(3)
        subplot(4, 4, (f - 16)) % mod to take care of bins > 15
    end
    title(['Bin ', num2str(f - 1), ' '])
    drawnow;
    hold on;
    plot(freq, test_cosines(f, 1:32), 'b.-', freq, test_sines(f, 1:32), 'r.-', freq, data, 'g.')
    
    % Enabling the following two lines shows the product of the test sinusoids
    % And original data, but makes for a cluttered plot!!
    %lines = plot(resultCosines(f), color='#9900CC', marker='.') %purple
    %lines = plot(resultSines(f), color='#00FF00', marker='.') %Green
end

figure(1)
subplot(3, 1, 1)
title('Original signal')
drawnow;
hold on;
plot(data)
subplot(3, 1, 2)
title('and MATLAB FFT')
drawnow;
hold on;
plot(fft_magnitude)
subplot(3, 1, 3)
title('And our slow FFT!')
drawnow;
hold on;
plot(magnitude/num_bins)

