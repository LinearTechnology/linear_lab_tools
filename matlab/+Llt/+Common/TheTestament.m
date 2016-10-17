function TheTestament
% Tests LLT using the 6 board setup.

fprintf('Set Clocks');
linduino = Llt.Utils.Linduino();
linduino.fprintf('MSGxS04S07S08S02S0CS01XgS04S0ES08S01S0CS01G');
linduino.fprintf('K00K01K02\n');

for i = 1
    if ~TestDc2290aA(linduino); break; end
    if ~TestDc1925aA(linduino); break; end
    if ~TestDc1369aA(); break; end
    if ~TestDc1563aA(linduino); break; end
    if ~TestDc1532aA(); break; end
    if ~TestDc2085aA(); break; end
end

linduino.fprintf('K00K01K02\n');
fclose(linduino);
delete(linduino);
clear linduino

function result = TestDc2290aA(linduino)
fprintf(['########################\n', ...
         '#### TEST DC2290A-A ####\n', ...
         '########################\n']);
linduino.fprintf('K01K02K10\n');
sleep(5000);
Llt.DemoBoardExamples.Ltc23XX.LTC2387.Ltc2387Dc2290aA(64*1024);
newFileName = 'test_dc2290a_a_data.txt';
movefile('data.txt', newFileName);
data = ReadFile(newFileName);
delete(newFileName);
result = TestSin(data, 18, 18, -7, 66, -70, -55500, 55500);
fprintf('\n');

function result = TestDc1563aA(linduino)
fprintf(['########################\n', ...
         '#### TEST DC1563A-A ####\n', ...
         '########################\n']);
linduino.fprintf('K00K02K11\n');
sleep(5000);
Llt.DemoBoardExamples.Ltc23XX.LTC2315.Ltc2325Dc1563aA(32*1024);
newFileName = 'test_dc1563a_a_data.txt';
movefile('data.txt', newFileName);
data = ReadFile(newFileName);
delete(newFileName);
result = TestSin(data, 12, 23, -1, 64, -63, 300, 3500);
fprintf('\n');

function result = TestDc1369aA()
fprintf(['########################\n', ...
         '#### TEST DC1369A-A ####\n', ...
         '########################\n']);
fprintf('\nNormal:\n-------\n');
nSamps = 8 * 1024;
Llt.DemoBoardExamples.Ltc22XX.LTC2261.Ltc2261Dc1369aA(nSamps);
newFileName = 'test_dc1369a_a_data.txt';
movefile('data.txt', newFileName);
data = ReadFile(newFileName);
delete(newFileName);
result = TestSin(data, 14, 2412, -1, 71, -84, 1400, 15000);
if ~result; return; end

noTrigger = Llt.Common.LtcControllerComm.TRIGGER_NONE;

fprintf('\nBipolar:\n--------\n');
spiReg = [ ... address,       value
               hex2dec('00'), hex2dec('80'), ...
               hex2dec('01'), hex2dec('00'), ...
               hex2dec('02'), hex2dec('00'), ...
               hex2dec('03'), hex2dec('71'), ...
               hex2dec('04'), hex2dec('01'), ... bipolar
          ];
      
lcc = Llt.Common.LtcControllerComm();
controller = Llt.Common.Dc890(lcc, 'DC1369A-A', ... dcNumber
                                   'DLVDS', ... fpgaLoad
                                   2, ... nChannels
                                   true, ... isPositiveClock
                                   14, ... nBits
                                   14, ... alignment
                                   true, ... isBipolar
                                   spiReg, false);
data = controller.Collect(nSamps, noTrigger, 5);
result = TestSin(data, 14, 2412, -1, 71, -84, -6500, 6500);
if ~result; return; end

fprintf('\nRandomizer:\n-----------\n');
nSamps = 8 * 1024;
spiReg = [ ... address,       value
               hex2dec('00'), hex2dec('80'), ...
               hex2dec('01'), hex2dec('00'), ...
               hex2dec('02'), hex2dec('00'), ...
               hex2dec('03'), hex2dec('71'), ...
               hex2dec('04'), hex2dec('02'), ... randomizer
          ];
controller = Llt.Common.Dc890(lcc, 'DC1369A-A', ... dcNumber
                                   'DLVDS', ... fpgaLoad
                                   2, ... nChannels
                                   true, ... isPositiveClock
                                   14, ... nBits
                                   14, ... alignment
                                   false, ... isBipolar
                                   spiReg, false);
data = controller.Collect(nSamps, noTrigger, 5, true);
result = TestSin(data, 14, 2412, -1, 71, -84, 1400, 15000);
if ~result; return; end

fprintf('\nAlternate Bit:\n--------------\n');
nSamps = 8 * 1024;
spiReg = [ ... address,       value
               hex2dec('00'), hex2dec('80'), ...
               hex2dec('01'), hex2dec('00'), ...
               hex2dec('02'), hex2dec('00'), ...
               hex2dec('03'), hex2dec('71'), ...
               hex2dec('04'), hex2dec('04'), ... alt bit
          ];
controller = Llt.Common.Dc890(lcc, 'DC1369A-A', ... dcNumber
                                   'DLVDS', ... fpgaLoad
                                   2, ... nChannels
                                   true, ... isPositiveClock
                                   14, ... nBits
                                   14, ... alignment
                                   false, ... isBipolar
                                   spiReg, false);
data = controller.Collect(nSamps, noTrigger, 5, false, true);
result = TestSin(data, 14, 2412, -1, 71, -84, 1400, 15000);

function result = TestDc1925aA(linduino)
fprintf(['########################\n', ...
         '#### TEST DC1925A-A ####\n', ...
         '########################\n']);
linduino.fprintf('K00K01K12\n');
sleep(5000);
Llt.DemoBoardExamples.Ltc23XX.LTC2378.Ltc2378Dc1925aA(8*1024);
newFileName = 'test_dc1925a_a_data.txt';
movefile('data.txt', newFileName);
data = ReadFile(newFileName);
delete(newFileName);
result = TestSin(data, 20, 52, -0, 80, -75, -120000, 120000);
fprintf('\n');

function result = TestDc1532aA()
fprintf(['########################\n', ...
         '#### TEST DC1532A-A ####\n', ...
         '########################\n']);
sleep(5000);
Llt.DemoBoardExamples.Ltc22XX.LTC2268.Ltc2268Dc1532aA(8*1024);
newFileName = 'test_dc1925a_a_data.txt';
movefile('data.txt', newFileName);
data = ReadFile(newFileName);
delete(newFileName);
result = TestSin(data, 14, 2412, -16, 57, -78, 7000, 9200);
fprintf('\n');

function result = TestDc2085aA()
fprintf(['########################\n', ...
         '#### TEST DC2085A-A ####\n', ...
         '########################\n']);
Llt.DemoBoardExamples.LTC2000.Ltc2000_dc2085();
[~, data] = Llt.DemoBoardExamples.Ltc22XX.LTC2268.Ltc2268Dc1532aA(8*1024);
result = TestSin(data, 14, 2500, -14, 57, -75, 6800, 9400);

fprintf('\n');

function data = ReadFile(filename)
fid = fopen(filename, 'rt');
data = textscan(fid, '%f');
data = data{1};
fclose(fid);

function condition = softAssert(condition, failMessage)
if ~condition
    n = length(failMessage);
    bangs = char(repmat('!', 1, n));
    fprintf('%s\n%s\n%s\n', bangs, failMessage, bangs);
end

function result = TestSin(data, nBits, exF1Bin, exF1Db, exSnr, exThd, exMin, exMax)
[minVal, maxVal, f1Bin, f1Db, snr, thd] = SinStats(data, nBits);
fprintf('min              %d\n', minVal);
fprintf('max              %d\n', maxVal);
fprintf('fundamental bin  %d\n', f1Bin);
fprintf('fundamental dBfs %d\n', f1Db);
fprintf('SNR              %f\n', snr);
fprintf('THD              %f\n', thd);

result = false;
if ~softAssert(minVal <= exMin, 'min value too big'); return; end
if ~softAssert(maxVal >= exMax, 'max value too small'); return; end
if ~softAssert(f1Bin == exF1Bin, 'bad fundamental bin'); return; end
if ~softAssert(f1Db >= exF1Db, 'bad fundamental dB'); return; end
if ~softAssert(snr > exSnr -1 && snr < exSnr + 5, 'bad snr db'); return; end
if ~softAssert(thd < exThd + 20 && thd > exThd - 10, 'bad thd db'); return; end
result = true;

function [minVal, maxVal, f1Bin, f1Db, snr, thd] = SinStats(data, nBits)
minVal = min(data);
maxVal = max(data);

% fft mag
n = length(data);
nyq = floor(n / 2) + 1;
data = data - mean(data);
data = data .* Llt.Common.FftWindow(n);
fftData = fft(data);
fftData = fftData(1:nyq);
fftData = abs(fftData) / n;
fftData(2:(nyq-1)) = 2 * fftData(2:(nyq-1));

% harmonic bins
N_HARMS = 8;
harmBins = zeros(N_HARMS,1);
[~, f1Bin] = max(fftData);
f1Bin = f1Bin - 1; % do the math w/ 0-based indices
harmBins(1) = f1Bin;
for h = 2:N_HARMS
    nominal = h * f1Bin;
    hOver2 = floor(h/2);
    bins = (nominal - hOver2):(nominal + hOver2);
    bins = MapIndices(bins, nyq);
    [~, maxBin] = max(fftData(bins + 1));
    harmBins(h) = bins(maxBin);
end

% auto mask
mask = true(nyq, 1);
mask(1:4) = false;
noiseFloor = EstimateNoiseFloor(fftData, harmBins);

for i = 1:N_HARMS
    k = harmBins(i);
    low = k;
    high = k;
    
    if ~mask(k+1); continue; end
    
    for j = 1:k
        if ~mask(k-1+1); break; end
        avg = mean(fftData((k-j+1):(k-j+3)));
        if avg < noiseFloor
            low = k - j + 1;
            break;
        end
    end
    
    for j = 1:k
        if ~mask(k-1+1); break; end
        avg = mean(fftData((k+j-1):(k+j+1)));
        if avg < noiseFloor
            high = k + j - 1;
            break;
        end
    end
    
    mask((low+1):(high+1)) = false(high-low+1, 1);
end

% noise
avgNoise = sum(fftData(mask).^2) / nnz(mask);
noise = avgNoise * nyq;

% harmonics
prevBins = [];
harmPowers = zeros(N_HARMS, 1);
for i = 1:N_HARMS
    h = harmBins(i);
    bins = (h-3):(h+3);
    bins = MapIndices(bins, nyq);
    bins = unique(bins+1);
    bins = setdiff(bins, prevBins);
    prevBins = [prevBins, bins];%#ok
    power = sum(fftData(bins).^2);
    harmPowers(i) = power - avgNoise * length(bins);
end

f1Db = 10*log10(harmPowers(1)) - 20*log10(2^(nBits-1));

snr = 10*log10(harmPowers(1) / noise);

harmp = harmPowers(2:5);
harmp = harmp(harmp > 0);
thd = 10*log10(sum(harmp) / harmPowers(1));

function indices = MapIndices(indices, nyq)
% NOTE: 0-based indices!    
n = (nyq - 1) * 2;
indices = mod(indices + n, n);
indices(indices > nyq) = n - indices(indices > nyq);

function noise = EstimateNoiseFloor(fftData, harmBins)
n = length(fftData);
bw = floor(n / 80);
mask = true(n, 1);
mask(1) = false;
for i = 1:4
    mask((harmBins(i)-bw+1):(harmBins(i)+bw+1)) = false;
end
indices = find(mask);
indices = MapIndices(indices - 1, n) + 1; % do math w/ 0-based indices
indices = unique(indices);

noiseData = fftData(indices);
noise = sum(noiseData) / length(noiseData);










    

