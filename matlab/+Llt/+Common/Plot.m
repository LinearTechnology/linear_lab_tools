function Plot(data, numBits, channel, verbose)
if ~exist('channel', 'var'); channel = 0; end
if ~exist('verbose', 'var'); verbose = false; end

if verbose; fprintf('Plotting channel %d time domain.\n', channel); end

nSamples = length(data);
    
figure(2*channel+1)
plot(data)
title(sprintf('Ch %d : Time Domain Samples', channel))

if verbose; fprintf('FFT''ing channel %d data.\n', channel); end

adcAmplitude = 2.0^(numBits-1);
dataNoDc = double(data);
dataNoDc = dataNoDc - mean(dataNoDc); % Remove DC to avoid leakage when windowing
window = Llt.Common.Window(nSamples);
windowedData = double(dataNoDc) .* window;
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
