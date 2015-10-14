function SaveForPscope(outPath, numBits, isBipolar, numSamples, dcNum, ...
    ltcNum, data)
%SaveForPscope Save data in PScope compatible format

% default values for running without argument, i.e. simple example.
if nargin == 0
    outPath = 'test.adc';
    numBits = 16;
    isBipolar = true;
    numSamples = 65536;
    dcNum = 'DC9876A-A';
    ltcNum = 'LTC9999';
    channel1 = transpose(int16(8192 * cos(0.12 * (0:(numSamples-1)))));
    channel2 = transpose(int16(8192 * cos(0.034 * (0:(numSamples-1)))));
    data = [channel1, channel2];
end

numChannels = size(data, 2);
if numChannels < 0 || numChannels > 16
    error('SaveForMatlab:BadNumberOfChannels', ...
        ['Channels must be between 1 and 16 ', ...
        '(do you need to transpose the data?']);
end

fullScale = bitshift(1, numBits);
if isBipolar
    minVal = -fullScale / 2;
    maxVal = fullScale / 2;
else
    minVal = 0;
    maxVal = fullScale;
end

fid = fopen(outPath, 'w');
fprintf(fid, 'Version,115\n');
fprintf(fid, 'Retainers,0,%d,%d,1024,0,%0.15f,1,1\n', ...
    numChannels, numSamples, 0.0);
fprintf(fid, 'Placement,44,0,1,-1,-1,-1,-1,10,10,1031,734\n');
fprintf(fid, 'DemoID,%s,%s,0\n', dcNum, ltcNum);
for ch = 1:numChannels
    fprintf(fid, 'RawData,%d,%d,%d,%d,%d,%0.15f,%e,%e\n', ...
        ch, numSamples, numBits, minVal, maxVal, 1.0, minVal, maxVal);
end
for s = 1:numSamples
    fprintf(fid, '%d', data(s, 1));
    for ch = 2:numChannels
        fprintf(fid, ', ,%d', data(s, ch));
    end
    fprintf(fid, '\n');
end
fprintf(fid, 'End\n');

