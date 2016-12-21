function the_testament
% Tests LLT using the 6 board setup.

fprintf('Set Clocks\n');
linduino = llt.utils.linduino();
fprintf(linduino, 'MSGxS04S07S08S02S0CS01XgS04S0ES08S01S0CS01G');
fprintf(linduino, 'K00K01K02\n');

for i = 1
    if ~test_dc2290a_a(linduino); break; end
    if ~test_dc1925a_a(linduino); break; end
    if ~test_dc1369a_a(); break; end
    if ~test_dc1563a_a(linduino); break; end
    if ~test_dc1532a_a(); break; end
    if ~test_dc2085a_a(); break; end
end

fprintf(linduino, 'K00K01K02\n');
fclose(linduino);
delete(linduino);
clear linduino

function result = test_dc2290a_a(linduino)
fprintf(['########################\n', ...
         '#### TEST DC2290A-A ####\n', ...
         '########################\n']);
fprintf(linduino, 'K01K02K10\n');
pause(5);
llt.demo_board_examples.ltc23xx.ltc2387.ltc2387_dc2290a_a(64*1024);
new_file_name = 'test_dc2290a_a_data.txt';
movefile('data.txt', new_file_name);
data = read_file(new_file_name);
delete(new_file_name);
result = test_sin(data, 18, 18, -7, 66, -70, -55500, 55500);
fprintf('\n');

function result = test_dc1925a_a(linduino)
fprintf(['########################\n', ...
         '#### TEST DC1925A-A ####\n', ...
         '########################\n']);
fprintf(linduino, 'K00K01K12\n');
pause(5);
llt.demo_board_examples.ltc23xx.ltc2378.ltc2378_20_dc1925a_a(8*1024);
new_file_name = 'test_dc1925a_a_data.txt';
movefile('data.txt', new_file_name);
data = read_file(new_file_name);
delete(new_file_name);
result = test_sin(data, 20, 52, -9, 80, -80, -120000, 120000);
fprintf('\n');

function result = test_dc1369a_a()
fprintf(['########################\n', ...
         '#### TEST DC1369A-A ####\n', ...
         '########################\n']);
result = false;
if ~test_dc1369a_a_normal(); return; end
if ~test_dc1369a_a_bipolar(); return; end
if ~test_dc1369a_a_randomizer(); return; end
if ~test_dc1369a_a_alternate_bit(); return; end
result = true;

function result = test_dc1369a_a_normal()
fprintf('\nNormal:\n-------\n');
nSamps = 8 * 1024;
llt.demo_board_examples.ltc22xx.ltc2261.ltc2261_dc1369a_a(nSamps);
new_file_name = 'test_dc1369a_a_data.txt';
movefile('data.txt', new_file_name);
data = read_file(new_file_name);
delete(new_file_name);
result = test_sin(data, 14, 2412, -1, 71, -84, 1400, 15000);

function result = test_dc1369a_a_bipolar()
fprintf('\nBipolar:\n--------\n');
nSamps = 8 * 1024;
spiReg = [ ... address,       value
               hex2dec('00'), hex2dec('80'), ...
               hex2dec('01'), hex2dec('00'), ...
               hex2dec('02'), hex2dec('00'), ...
               hex2dec('03'), hex2dec('71'), ...
               hex2dec('04'), hex2dec('01'), ... bipolar
          ];
      
lcc = llt.common.LtcControllerComm();
controller = llt.common.Dc890(lcc, 'DC1369A-A', ... dcNumber
                                   'DLVDS', ... fpgaLoad
                                   2, ... nChannels
                                   true, ... isPositiveClock
                                   14, ... nBits
                                   14, ... alignment
                                   true, ... isBipolar
                                   spiReg, false);
data = controller.collect(nSamps, llt.common.LtcControllerComm.TRIGGER_NONE, 5);
result = test_sin(data, 14, 2412, -1, 71, -84, -6500, 6500);

function result = test_dc1369a_a_randomizer()
fprintf('\nRandomizer:\n-----------\n');
nSamps = 8 * 1024;
spiReg = [ ... address,       value
               hex2dec('00'), hex2dec('80'), ...
               hex2dec('01'), hex2dec('00'), ...
               hex2dec('02'), hex2dec('00'), ...
               hex2dec('03'), hex2dec('71'), ...
               hex2dec('04'), hex2dec('02'), ... randomizer
          ];
lcc = llt.common.LtcControllerComm();
controller = llt.common.Dc890(lcc, 'DC1369A-A', ... dcNumber
                                   'DLVDS', ... fpgaLoad
                                   2, ... nChannels
                                   true, ... isPositiveClock
                                   14, ... nBits
                                   14, ... alignment
                                   false, ... isBipolar
                                   spiReg, false);
data = controller.collect(nSamps, llt.common.LtcControllerComm.TRIGGER_NONE, 5, true);
result = test_sin(data, 14, 2412, -1, 71, -84, 1400, 15000);

function result = test_dc1369a_a_alternate_bit()
fprintf('\nAlternate Bit:\n--------------\n');
nSamps = 8 * 1024;
spiReg = [ ... address,       value
               hex2dec('00'), hex2dec('80'), ...
               hex2dec('01'), hex2dec('00'), ...
               hex2dec('02'), hex2dec('00'), ...
               hex2dec('03'), hex2dec('71'), ...
               hex2dec('04'), hex2dec('04'), ... alt bit
          ];
lcc = llt.common.LtcControllerComm();
controller = llt.common.Dc890(lcc, 'DC1369A-A', ... dcNumber
                                   'DLVDS', ... fpgaLoad
                                   2, ... nChannels
                                   true, ... isPositiveClock
                                   14, ... nBits
                                   14, ... alignment
                                   false, ... isBipolar
                                   spiReg, false);
data = controller.collect(nSamps, llt.common.LtcControllerComm.TRIGGER_NONE, 5, false, true);
clear controller;
result = test_sin(data, 14, 2412, -1, 71, -84, 1400, 15000);

function result = test_dc1563a_a(linduino)
fprintf(['########################\n', ...
         '#### TEST DC1563A-A ####\n', ...
         '########################\n']);
fprintf(linduino, 'K00K02K11\n');
pause(5);
llt.demo_board_examples.ltc23xx.ltc2315.ltc2315_dc1563a_a(32*1024);
new_file_name = 'test_dc1563a_a_data.txt';
movefile('data.txt', new_file_name);
data = read_file(new_file_name);
result = test_sin(data, 12, 23, -1, 64, -63, 300, 3500);
fprintf('\n');

function result = test_dc1532a_a()
fprintf(['########################\n', ...
         '####  TEST DC1532A  ####\n', ...
         '########################\n']);
llt.demo_board_examples.ltc22xx.ltc2268.ltc2268_dc1532a(8*1024);
new_file_name = 'test_dc1925a_a_data.txt';
movefile('data.txt', new_file_name);
data = read_file(new_file_name);
data = data(1:(8*1024));
delete(new_file_name);
result = test_sin(data, 14, 2412, -16, 57, -78, 7000, 9200);
fprintf('\n');

function result = test_dc2085a_a()
fprintf(['########################\n', ...
         '#### TEST DC2085A-A ####\n', ...
         '########################\n']);
llt.demo_board_examples.ltc2000.ltc2000_dc2085();
[~, data] = llt.demo_board_examples.ltc22xx.ltc2268.ltc2268_dc1532a(8*1024);
figure(5)
llt.common.plot(data, 14);
result = test_sin(data, 14, 2500, -14, 57, -78, 6800, 9400);

fprintf('\n');

function data = read_file(filename)
fid = fopen(filename, 'rt');
data = textscan(fid, '%f');
data = data{1};
fclose(fid);

function condition = soft_assert(condition, fail_message)
if ~condition
    n = length(fail_message);
    bangs = char(repmat('!', 1, n));
    fprintf('%s\n%s\n%s\n', bangs, fail_message, bangs);
end

function result = test_sin(data, num_bits, ex_f1_bin, ex_f1_db, ex_snr, ex_thd, ex_min, ex_max)
min_val = min(data);
max_val = max(data);
[harmonics, snr, thd] = llt.common.sin_params(data);
h1 = harmonics{1};
f1_db = 10*log10(h1(1)) - 20*log10(2^(num_bits-1));
f1_bin = h1(2);
fprintf('min              %d\n', min_val);
fprintf('max              %d\n', max_val);
fprintf('fundamental bin  %d\n', f1_bin);
fprintf('fundamental dBfs %d\n', f1_db);
fprintf('SNR              %f\n', snr);
fprintf('THD              %f\n', thd);

result = false;
if ~soft_assert(min_val <= ex_min, 'min value too big'); return; end
if ~soft_assert(max_val >= ex_max, 'max value too small'); return; end
if ~soft_assert(f1_bin == ex_f1_bin+1, 'bad fundamental bin'); return; end
if ~soft_assert(f1_db >= ex_f1_db - 1 && f1_db < ex_f1_db + 5, 'bad fundamental dB'); return; end
if ~soft_assert(snr > ex_snr -1 && snr < ex_snr + 5, 'bad snr db'); return; end
if ~soft_assert(thd < ex_thd + 10 && thd > ex_thd - 10, 'bad thd db'); return; end
result = true;