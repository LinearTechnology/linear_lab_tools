function TheTestament
% Tests LLT using the 6 board setup.

fprintf('Set Clocks');
linduino = Llt.Utils.Linduino();
fprintf(linduino, 'MSGxS04S07S08S02S0CS01XgS04S0ES08S01S0CS01G');
fprintf(linduino, 'K00K01K02\n');

for i = 1
    if ~TestDc2290aA(linduino); break; end
    if ~TestDc1925aA(linduino); break; end
    if ~TestDc1369aA(); break; end
    if ~TestDc1563aA(linduino); break; end
    if ~TestDc1532aA(); break; end
    if ~TestDc2085aA(); break; end
end

fprintf(linduino, 'K00K01K02\n');
fclose(linduino);
delete(linduino);
clear linduino

function result = TestDc2290aA(linduino)
fprintf(['########################\n', ...
         '#### TEST DC2290A-A ####\n', ...
         '########################\n']);
fprintf(linduino, 'K01K02K10\n');
pause(5);
Llt.DemoBoardExamples.LTC23XX.LTC2387.Ltc2387Dc2290aA;
Llt.DemoBoardExamples.LTC23XX.LTC2387.Ltc2387Dc2290aA(64*1024);
newFileName = 'test_dc2290a_a_data.txt';
movefile('data.txt', newFileName);
data = ReadFile(newFileName);
delete(newFileName);
result = TestSin(data, 18, 18, -7, 66, -70, -55500, 55500);
fprintf('\n');

function result = TestDc1925aA(linduino)
fprintf(['########################\n', ...
         '#### TEST DC1925A-A ####\n', ...
         '########################\n']);
fprintf(linduino, 'K00K01K12\n');
pause(5);
Llt.DemoBoardExamples.LTC23XX.LTC2378.Ltc2378_20Dc1925aA(8*1024);
newFileName = 'test_dc1925a_a_data.txt';
movefile('data.txt', newFileName);
data = ReadFile(newFileName);
delete(newFileName);
result = TestSin(data, 20, 52, -0, 80, -75, -120000, 120000);
fprintf('\n');

function result = TestDc1369aA()
fprintf(['########################\n', ...
         '#### TEST DC1369A-A ####\n', ...
         '########################\n']);
result = false;
if ~TestDc1369aANormal(); return; end
if ~TestDc1369aABipolar(); return; end
if ~TestDc1369aARandomizer(); return; end
if ~TestDc1369aAAlternateBit(); return; end
result = true;

function result = TestDc1369aANormal()
fprintf('\nNormal:\n-------\n');
nSamps = 8 * 1024;
Llt.DemoBoardExamples.LTC22XX.LTC2261.Ltc2261Dc1369aA(nSamps);
newFileName = 'test_dc1369a_a_data.txt';
movefile('data.txt', newFileName);
data = ReadFile(newFileName);
delete(newFileName);
result = TestSin(data, 14, 2412, -1, 71, -84, 1400, 15000);

function result = TestDc1369aABipolar()
fprintf('\nBipolar:\n--------\n');
nSamps = 8 * 1024;
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
data = controller.Collect(nSamps, Llt.Common.LtcControllerComm.TRIGGER_NONE, 5);
result = TestSin(data, 14, 2412, -1, 71, -84, -6500, 6500);

function result = TestDc1369aARandomizer()
fprintf('\nRandomizer:\n-----------\n');
nSamps = 8 * 1024;
spiReg = [ ... address,       value
               hex2dec('00'), hex2dec('80'), ...
               hex2dec('01'), hex2dec('00'), ...
               hex2dec('02'), hex2dec('00'), ...
               hex2dec('03'), hex2dec('71'), ...
               hex2dec('04'), hex2dec('02'), ... randomizer
          ];
lcc = Llt.Common.LtcControllerComm();
controller = Llt.Common.Dc890(lcc, 'DC1369A-A', ... dcNumber
                                   'DLVDS', ... fpgaLoad
                                   2, ... nChannels
                                   true, ... isPositiveClock
                                   14, ... nBits
                                   14, ... alignment
                                   false, ... isBipolar
                                   spiReg, false);
data = controller.Collect(nSamps, Llt.Common.LtcControllerComm.TRIGGER_NONE, 5, true);
result = TestSin(data, 14, 2412, -1, 71, -84, 1400, 15000);

function result = TestDc1369aAAlternateBit()
fprintf('\nAlternate Bit:\n--------------\n');
nSamps = 8 * 1024;
spiReg = [ ... address,       value
               hex2dec('00'), hex2dec('80'), ...
               hex2dec('01'), hex2dec('00'), ...
               hex2dec('02'), hex2dec('00'), ...
               hex2dec('03'), hex2dec('71'), ...
               hex2dec('04'), hex2dec('04'), ... alt bit
          ];
lcc = Llt.Common.LtcControllerComm();
controller = Llt.Common.Dc890(lcc, 'DC1369A-A', ... dcNumber
                                   'DLVDS', ... fpgaLoad
                                   2, ... nChannels
                                   true, ... isPositiveClock
                                   14, ... nBits
                                   14, ... alignment
                                   false, ... isBipolar
                                   spiReg, false);
data = controller.Collect(nSamps, Llt.Common.LtcControllerComm.TRIGGER_NONE, 5, false, true);
clear controller;
result = TestSin(data, 14, 2412, -1, 71, -84, 1400, 15000);

function result = TestDc1563aA(linduino)
fprintf(['########################\n', ...
         '#### TEST DC1563A-A ####\n', ...
         '########################\n']);
fprintf(linduino, 'K00K02K11\n');
pause(5);
Llt.DemoBoardExamples.LTC23XX.LTC2315.Ltc2315Dc1563aA(32*1024);
newFileName = 'test_dc1563a_a_data.txt';
movefile('data.txt', newFileName);
data = ReadFile(newFileName);
result = TestSin(data, 12, 23, -1, 64, -63, 300, 3500);
fprintf('\n');

function result = TestDc1532aA()
fprintf(['########################\n', ...
         '####  TEST DC1532A  ####\n', ...
         '########################\n']);
Llt.DemoBoardExamples.LTC22XX.LTC2268.Ltc2268Dc1532a(8*1024);
newFileName = 'test_dc1925a_a_data.txt';
movefile('data.txt', newFileName);
data = ReadFile(newFileName);
data = data(1:(8*1024));
delete(newFileName);
result = TestSin(data, 14, 2412, -16, 57, -78, 7000, 9200);
fprintf('\n');

function result = TestDc2085aA()
fprintf(['########################\n', ...
         '#### TEST DC2085A-A ####\n', ...
         '########################\n']);
Llt.DemoBoardExamples.LTC2000.Ltc2000Dc2085();
[~, data] = Llt.DemoBoardExamples.LTC22XX.LTC2268.Ltc2268Dc1532a(8*1024);
figure(5)
Llt.Common.Plot(data, 14);
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
minVal = min(data);
maxVal = max(data);
[harmonics, snr, thd] = Llt.Common.SinParams(data);
h1 = harmonics{1};
f1Db = 10*log10(h1(1)) - 20*log10(nBits-1);
f1Bin = h1(2);
fprintf('min              %d\n', minVal);
fprintf('max              %d\n', maxVal);
fprintf('fundamental bin  %d\n', f1Bin);
fprintf('fundamental dBfs %d\n', f1Db);
fprintf('SNR              %f\n', snr);
fprintf('THD              %f\n', thd);

result = false;
if ~softAssert(minVal <= exMin, 'min value too big'); return; end
if ~softAssert(maxVal >= exMax, 'max value too small'); return; end
if ~softAssert(f1Bin == exF1Bin+1, 'bad fundamental bin'); return; end
%if ~softAssert(f1Db >= exF1Db - 1 && f1Db < exF1Db + 5, 'bad fundamental dB'); return; end
%if ~softAssert(snr > exSnr -1 && snr < exSnr + 5, 'bad snr db'); return; end
%if ~softAssert(thd < exThd + 20 && thd > exThd - 10, 'bad thd db'); return; end
result = true;