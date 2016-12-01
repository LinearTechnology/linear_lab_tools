function save_for_pscope(out_path, num_bits, is_bipolar, num_samples, dc_num, ...
    ltc_num, data)
% Save data in PScope compatible format

% default values for running without argument, i.e. simple example.
if nargin == 0
    out_path = 'test.adc';
    num_bits = 16;
    is_bipolar = true;
    num_samples = 65536;
    dc_num = 'DC9876A-A';
    ltc_num = 'LTC9999';
    channel1 = transpose(int16(8192 * cos(0.12 * (0:(num_samples-1)))));
    channel2 = transpose(int16(8192 * cos(0.034 * (0:(num_samples-1)))));
    data = [channel1, channel2];
end

num_channels = size(data, 2);
if num_channels < 0 || num_channels > 16
    error('SaveForMatlab:BadNumberOfChannels', ...
        ['Channels must be between 1 and 16 ', ...
        '(do you need to transpose the data?']);
end

full_scale = bitshift(1, num_bits);
if is_bipolar
    min_val = -full_scale / 2;
    max_val = full_scale / 2;
else
    min_val = 0;
    max_val = full_scale;
end

fid = fopen(out_path, 'w');
fprintf(fid, 'Version,115\n');
fprintf(fid, 'Retainers,0,%d,%d,1024,0,%0.15f,1,1\n', ...
    num_channels, num_samples, 0.0);
fprintf(fid, 'Placement,44,0,1,-1,-1,-1,-1,10,10,1031,734\n');
fprintf(fid, 'DemoID,%s,%s,0\n', dc_num, ltc_num);
for ch = 1:num_channels
    fprintf(fid, 'RawData,%d,%d,%d,%d,%d,%0.15f,%e,%e\n', ...
        ch, num_samples, num_bits, min_val, max_val, 1.0, min_val, max_val);
end
for s = 1:num_samples
    fprintf(fid, '%d', data(s, 1));
    for ch = 2:num_channels
        fprintf(fid, ', ,%d', data(s, ch));
    end
    fprintf(fid, '\n');
end
fprintf(fid, 'End\n');

