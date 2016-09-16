% Demonstration of how a FFT works.
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
binNumber = 2.0;
amplitude = 1.0;
mu = 0;
sigma = 0.1;

numBins = 32; % This is also the number of points in the time record
data = zeros(1, numBins);

noise = sigma.*randn(numBins,1) + mu;

% Generate some input data
for i = 1:numBins
    data(i)= amplitude * sin(2 * pi * binNumber * i / numBins);
    data(i) = data(i) + noise(i);
end
    
% And lets take its FFT using MATLAB's FFT function, and tuck it away for later
fftMagnitude = abs(fft(data) / length(data));

% Okay, now let's deconstruct the FFT a bit. And by "a bit", we mean "a LOT!"
% We've already got the data that we
% want to analyze, so the next step is to make two, 2-d arrays of "test sinusoids"
% where one consists of cosines to detect the real part of a frequency component,
% and the other consists of sines to detect the imaginary part:

testCosines = zeros(numBins, numBins);
testSines = zeros(numBins, numBins);
for freq = 1 : numBins
    for time = 1: numBins
        testCosines(freq, time) = cos(2*pi * (freq-1) * time / numBins);
        testSines(freq, time) = sin(2*pi * (freq-1) * time / numBins);
    end
end

% The next step is to multiply the "test sinusoids" by the original data, one
% frequency at a time to see if "anybody's home". You actually only need to
% "multiply and accumulate", such that one test sinusoid will produce a single
% number. But we want to plot the results, so we're going to construct arrays
% (the "multiply" part) and then sum the elements (the "accumulate" part.)

resultCosines = zeros(numBins, numBins);
resultSines = zeros(numBins, numBins);

for freq = 1 : numBins
    resultCosines(freq, 1:32) = testCosines(freq, 1:32) .* data(1:32);
    resultSines(freq, 1:32) = testSines(freq, 1:32) .* data(1:32);
end

% This is the final step! Sum the elements of the result arrays, which gives
% you the real and imaginary parts of the DFT:
realPart = zeros(1, numBins);
imagPart = zeros(1, numBins);

for freq = 1 : numBins
    realPart(freq) = sum(resultCosines(freq, 1:32));
    imagPart(freq) = sum(resultSines(freq, 1:32));
end
% Calculate magnitude of each frequency component (considering real and imaginary parts)
for freq = 1:32
    magnitude(freq) = sqrt(realPart(freq) ^ 2 + imagPart(freq) ^ 2);
end

figure(2)
title('Data and test sinusoids for bins 0-15')
%ax = gca()
%ax.set_axis_bgcolor('%C0C0C0')

%lines = plot(zones_ltc2057_psd(0))

freq = 1:32;
for f = 1 : numBins
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
    plot(freq, testCosines(f, 1:32), 'b.-', freq, testSines(f, 1:32), 'r.-', freq, data, 'g.')
    
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
plot(fftMagnitude)
subplot(3, 1, 3)
title('And our slow FFT!')
drawnow;
hold on;
plot(magnitude/numBins)

