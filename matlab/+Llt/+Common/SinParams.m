function [harmonics, snr, thd, sinad, enob, sfdr] = SinParams(data, ...
        windowType, mask, nHarms, spurInHarms)
    %SinParams Returns basic parameters that describe a sine wave

    if ~exist('windowType', 'var'); windowType = 'BlackmanHarris92'; end
    if ~exist('nHarms', 'var'); nHarms = 8; end
    if ~exist('spurInHarms', 'var'); spurInHarms = true; end

    fftData = WindowedFftMag(data);
    [harmBins, harms, harmBws] = FindHarmonics(fftData, nHarms);
    
    if ~exist('mask', 'var') || isempty(mask)
        mask = CalculateAutoMask(data, harmBins, windowType);
    end
    
    [spur, spurBw] = FindSpur(spurInHarms, harmBins, harms, fftData, windowType);
    [noise, noiseBins] = MaskedSumOfSq(fftData, mask);
    averageNoise = noise / max(1, noiseBins);
    noise = averageNoise * length(fftData);

    harmonics = cell(nHarms, 1);
    for i = 1:nHarms
        h = harms(i) - averageNoise * harmBws(i);
        if (h > 0)
            harmonics{i} = [h, harmBins(i)];
        end
    end

    spur = spur - spurBw * averageNoise;

    signal = harmonics{1}(1);
    snr = 10*log10(signal / noise);
    harmDist = 0;
    for i = 2:5
        if ~isempty(harmonics{i})
            harmDist = harmDist + harmonics{i}(1);
        end
    end
    if harmDist > 0
        thd = 10*log10(harmDist / signal);
    else
        thd = 0;
    end
    sinad = 10*log10(signal / (harmDist + noise));
    enob = (sinad - 1.76) / 6.02;
    if spur > 0
        sfdr = 10*log10(signal / spur);
    else 
        sfdr = 0;
    end
end  

function fftData = WindowedFftMag(data, windowType)
    if ~exist('windowType', 'var'); windowType = 'BlackmanHarris92'; end
    n = length(data);
    data = data - mean(data);
    data = data .* Llt.Common.FftWindow(n, windowType);
    fftData = fft(data);
    fftData = abs(fftData(1:(n/2+1))) / n;
    fftData(2:n/2) = 2 * fftData(2:n/2);
end

function [harmBins, harms, harmBws] = FindHarmonics(fftData, maxHarms)
    BW = 3;
    harmBins = zeros(maxHarms, 1);
    [~, fundBin] = max(fftData);
    harmBins(1) = fundBin;
    harms = zeros(maxHarms, 1);
    harmBws = zeros(maxHarms, 1);

    for h = 1:maxHarms
        % first find the location by searching for the max 
        % inside an area of uncertainty
        mask = InitMask(length(fftData), false);
        nominalBin = h * fundBin;
        hOver2 = floor(h/2);
        if h > 1 
            mask = SetMask(mask, nominalBin-hOver2, nominalBin+hOver2);
            for i = 1:(h-1)
               mask = ClearMask(mask, harmBins(i), harmBins(i));
            end
            [~, harmBins(h)] = MaskedMax(fftData, mask);
        end
        % now find the power in the harmonic
        start = max(1, nominalBin-hOver2);
        finish = min(length(fftData), nominalBin+hOver2);
        mask = ClearMask(mask, start, finish);
        start = max(1, nominalBin-BW);
        finish = min(length(fftData), nominalBin+BW);
        mask = SetMask(mask, start, finish);
        for i = 1:(h-1)
            start = max(1, harmBins(i)-BW);
            finish = min(length(fftData), harmBins(i)+BW);
            mask = ClearMask(mask, start, finish+BW);
        end
        [harms(h), harmBws(h)] = MaskedSumOfSq(fftData, mask);
    end
end
        
function mask = CalculateAutoMask(fftData, harmBins, windowType)
    BANDWIDTH_DIVIDER = 80;
    NUM_INITAL_NOISE_HARMS = 5;
    n = length(fftData);
    bw = floor(n / BANDWIDTH_DIVIDER);

    mask = InitMask(n);
    for i = 1:NUM_INITAL_NOISE_HARMS
        start = max(1, harmBins(i) - bw);
        finish = min(n, harmBins(i) + bw);
        mask = ClearMask(mask, start, finish);
    end
    mask(1) = false;

    [noiseEst, noiseBins] = MaskedSum(fftData, mask);
    noiseEst = noiseEst / noiseBins;

    mask = InitMask(n);
    mask = ClearMaskAtDc(mask, windowType);
    for i = 1:length(harmBins)
        h = harmBins(i);
        if mask(h) == 0
            continue;
        end

        j = 1;
        while (h-j > 0) && mask(h-j) && ...
                (sum(fftData((h-j):(h-j+3))) / 3 > noiseEst)
            j = j + 1;
        end
        low = h - j + 1;

        j = 1;
        while h+j < n && mask(h+j) == 1 && ... 
                sum(fftData((h+j-2):(h+j+1))) / 3 > noiseEst
            j = j + 1;
        end
        high = h + j - 1;

        mask = ClearMask(mask, low, high);
    end
end

function [spur, spurBw] = FindSpur(findInHarms, harmBins, harms, fftData, windowType)
    BW = 3;
    n = length(fftData);
    fundBin = harmBins(1);
    mask = InitMask(n);
    mask = ClearMaskAtDc(mask, windowType);
    start = max(1, fundBin - BW);
    finish = min(n, fundBin + BW);
    mask = ClearMask(mask, start, finish);
    
    if findInHarms
        spurBin = FindSpurBin(fftData, mask);
    else
        spurBin = FindSpurInHarmonics(harmBins, harms);
    end
    
    start = max(1, spurBin - BW);
    finish = min(n, spurBin + BW);
    [spur, spurBw] = MaskedSumOfSq(fftData, mask, start, finish);
end

function spurBin = FindSpurInHarmonics(harmBins, harms)
    [~, index] = max(harms(2:ends));
    spurBin = harmBins(index);
end

function spurBin = FindSpurBin(fftData, mask)
    BW = 3;
    n = length(fftData);
    index = find(mask, 1);
    if isempty(index); index = 1; end
    start = max(0, index - BW);
    finish = min(n, index + BW);
    maxValue = MaskedSumOfSq(fftData, mask, start, finish);
    maxIndex = index;

    while index < length(fftData)
        if mask(index)
            start = max(1, index - BW);
            finish = min(n, index + BW);
            value = MaskedSumOfSq(fftData, mask, start, finish);
            if value > maxValue
                maxValue = value;
                maxIndex = index;
            end
        end
        index = index + 1;
    end
    start = max(1, maxIndex - BW);
    finish = min(n, maxIndex + BW);
    [~, spurBin] = MaskedMax(fftData, mask, start, finish);
end
        
function mask = ClearMaskAtDc(mask, windowType)
    switch lower(windowType)
        case 'none'
            bins = 1;
        case {'hamming', 'hann'}
            bins = 2;
        case {'blackman', 'blackmanexact', 'blackmanharris70', 'flattop'}
            bins = 3;      
        case 'blackmanharris92' 
            bins = 4;
        otherwise
            error('Window:BadWindowType', 'Unexpected window type %s', windowType);
    end
    mask = ClearMask(mask, 1, bins);
end

function mask = InitMask(n, initValue)
    if ~exist('initValue', 'var'); initValue = true; end
    if initValue
        mask = true(n, 1);
    else
        mask = false(n, 1);
    end
end

function mask = SetMask(mask, start, finish, setValue)
    if ~exist('setValue', 'var'); setValue = true; end;
    nyq = length(mask);
    mask(MapNyquist(start:finish, nyq)) = setValue;
end

function mask = ClearMask(mask, start, finish)
    mask = SetMask(mask, start, finish, false);
end

function value = MapNyquist(value, nyq)
    n = 2 * (nyq - 1);
    value = mod(value + n, n);
    value(value > nyq) = n - value(value > nyq);
end

function [value, i] = MaskedMax(data, mask, start, finish)
    if ~exist('start', 'var'); start = 1; end;
    if ~exist('finish', 'var'); finish = length(data); end
    [~, indices] = MaskedSubset(mask, start, finish);
    [value, i] = max(data(indices));
    i = indices(i);
end

function [value, numBins] = MaskedSum(data, mask, start, finish)
    if ~exist('start', 'var'); start = 1; end;
    if ~exist('finish', 'var'); finish = length(data); end
    [mask, indices] = MaskedSubset(mask, start, finish);
    value = sum(data(indices));
    numBins = nnz(mask);
end

function [value, numBins] = MaskedSumOfSq(data, mask, start, finish)
    if ~exist('start', 'var'); start = 1; end;
    if ~exist('finish', 'var'); finish = length(data); end
    [mask, indices] = MaskedSubset(mask, start, finish);
    value = sum(data(indices).^2);
    numBins = nnz(mask);
end

function [mask, indices] = MaskedSubset(mask, start, finish)
    n = length(mask);
    mappedSubset = MapNyquist(start:finish, n);
    indices = 1:min(finish, n);
    indices = indices(mappedSubset);
    mask = mask(mappedSubset);
    indices = indices(mask);
end



