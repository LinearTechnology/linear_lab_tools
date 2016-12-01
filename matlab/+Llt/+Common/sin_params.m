function [harmonics, snr, thd, sinad, enob, sfdr] = sin_params(data, ...
        window_type, mask, num_harms, spur_in_harms)
    %SinParams Returns basic parameters that describe a sine wave

    if ~exist('window_type', 'var'); window_type = 'BlackmanHarris92'; end
    if ~exist('num_harms', 'var'); num_harms = 9; end
    if ~exist('spur_in_harms', 'var'); spur_in_harms = true; end

    fft_data = windowed_fft_mag(data);
    [harm_bins, harms, harm_bws] = find_harmonics(fft_data, num_harms);
    
    if ~exist('mask', 'var') || isempty(mask)
        mask = calculate_auto_mask(fft_data, harm_bins, window_type);
    end
    
    [noise, noise_bins] = masked_sum_of_sq(fft_data(1:end-1), mask(1:end-1));
    average_noise = noise / max(1, noise_bins);
    noise = average_noise * (length(fft_data) - 1);

    [spur, spur_bw] = find_spur(spur_in_harms, harm_bins(1), harms, harm_bws, ...
        fft_data, window_type);
    
    spur = spur - spur_bw * average_noise;
    
    harmonics = cell(num_harms, 1);
    for i = 1:num_harms
        h = harms(i) - average_noise * harm_bws(i);
        if (h > 0)
            harmonics{i} = [h, harm_bins(i)];
        end
    end

    signal = harmonics{1}(1);
    snr = 10*log10(signal / noise);
    harm_dist = 0;
    for i = 2:5
        if ~isempty(harmonics{i})
            harm_dist = harm_dist + harmonics{i}(1);
        end
    end
    if harm_dist > 0
        thd = 10*log10(harm_dist / signal);
    else
        thd = 0;
    end
    sinad = 10*log10(signal / (harm_dist + noise));
    enob = (sinad - 1.76) / 6.02;
    if spur > 0
        sfdr = 10*log10(signal / spur);
    else 
        sfdr = 0;
    end
end  

function fft_data = windowed_fft_mag(data, window_type)
    if ~exist('window_type', 'var'); window_type = 'BlackmanHarris92'; end
    n = length(data);
    data = data - mean(data);
    data = data .* llt.common.fft_window(n, window_type);
    fft_data = fft(data);
    fft_data = abs(fft_data(1:(n/2+1))) / n;
    fft_data(2:n/2) = 2 * fft_data(2:n/2);
end

function [harm_bins, harms, harm_bws] = find_harmonics(fft_data, max_harms)
    BW = 3;
    harm_bins = zeros(max_harms, 1);
    [~, fund_bin] = max(fft_data);
    harm_bins(1) = fund_bin;
    harms = zeros(max_harms, 1);
    harm_bws = zeros(max_harms, 1);

    for h = 1:max_harms
        % first find the location by searching for the max 
        % inside an area of uncertainty
        mask = init_mask(length(fft_data), false);
        nominal_bin = h * (fund_bin - 1) + 1;
        h_2 = floor(h/2);
        if h > 1 
            mask = set_mask(mask, nominal_bin-h_2, nominal_bin+h_2);
            for i = 1:(h-1)
               mask = clear_mask(mask, harm_bins(i), harm_bins(i));
            end
            % don't include nyquist for PScope compatibility
            [~, harm_bins(h)] = masked_max(fft_data(1:end-1), mask(1:end-1));
        end
        % now find the power in the harmonic
        mask = clear_mask(mask, nominal_bin-h_2, nominal_bin+h_2);
        mask = set_mask(mask, harm_bins(h)-BW, harm_bins(h)+BW);
        for i = 1:(h-1)
            mask = clear_mask(mask, harm_bins(i)-BW, harm_bins(i)+BW);
        end
        [harms(h), harm_bws(h)] = masked_sum_of_sq(fft_data, mask);
    end
end
        
function mask = calculate_auto_mask(fft_data, harm_bins, window_type)
    BANDWIDTH_DIVIDER = 80;
    NUM_INITAL_NOISE_HARMS = 5;
    n = length(fft_data);
    bw = floor(n / BANDWIDTH_DIVIDER);

    mask = init_mask(n);
    for i = 1:NUM_INITAL_NOISE_HARMS
        mask = clear_mask(mask, harm_bins(i) - bw, harm_bins(i) + bw);
    end
    mask(1) = false;

    [noise_est, noise_bins] = masked_sum(fft_data, mask);
    noise_est = noise_est / noise_bins;

    mask = init_mask(n);
    mask = clear_mask_at_dc(mask, window_type);
    for i = 1:length(harm_bins)
        h = harm_bins(i);
        if mask(h) == 0
            continue;
        end

        j = 1;
        while (h-j > 0) && mask(h-j) && ...
                (sum(fft_data((h-j+1):(h-j+3))) / 3 > noise_est)
            j = j + 1;
        end
        low = h - j + 2;

        j = 1;
        while h+j < n && mask(h+j) == 1 && ... 
                sum(fft_data((h+j-1):(h+j+1))) / 3 > noise_est
            j = j + 1;
        end
        high = h + j;

        mask = clear_mask(mask, low, high);
    end
end

function [spur, spur_bw] = find_spur(find_in_harms, fund_bin, harms, harm_bws, ...
        fft_data, window_type)   
    if find_in_harms
        [spur, index] = max(harms(2:end));
        spur_bw = harm_bws(index + 1);
    else
        [spur, spur_bw] = find_spur_in_data(fft_data, window_type, fund_bin);
    end
end

function [spur, spur_bw] = find_spur_in_data(fft_data, window_type, fund_bin)
    BW = 3;
    n = length(fft_data);
    mask = init_mask(n);
    mask = clear_mask_at_dc(mask, window_type);
    mask = clear_mask(mask, fund_bin - BW, fund_bin + BW);
    
    index = find(mask, 1);
    if isempty(index); index = 1; end
    max_value = masked_sum_of_sq(fft_data, mask, index - BW, index + BW);
    max_index = index;

    while index < length(fft_data)
        if mask(index)
            value = masked_sum_of_sq(fft_data, mask, index - BW, index + BW);
            if value > max_value
                max_value = value;
                max_index = index;
            end
        end
        index = index + 1;
    end
    [~, spur_bin] = masked_max(fft_data, mask, max_index - BW, max_index + BW);
    [spur, spur_bw] = masked_sum_of_sq(fft_data, mask, spur_bin - BW, spur_bin + BW);
end
        
function mask = clear_mask_at_dc(mask, window_type)
    switch lower(window_type)
        case 'none'
            bins = 1;
        case {'hamming', 'hann'}
            bins = 2;
        case {'blackman', 'blackmanexact', 'blackmanharris70', 'flattop'}
            bins = 3;      
        case 'blackmanharris92' 
            bins = 4;
        otherwise
            error('Window:BadWindowType', 'Unexpected window type %s', window_type);
    end
    mask = clear_mask(mask, 1, bins);
end

function mask = init_mask(n, init_value)
    if ~exist('init_value', 'var'); init_value = true; end
    if init_value
        mask = true(n, 1);
    else
        mask = false(n, 1);
    end
end

function mask = set_mask(mask, start, finish, set_value)
if ~exist('set_value', 'var'); set_value = true; end;
    nyq = length(mask);
    mask(map_nyquist(start:finish, nyq)) = set_value;
end

function mask = clear_mask(mask, start, finish)
    mask = set_mask(mask, start, finish, false);
end

function indices = map_nyquist(indices, nyq)
    indices = indices - 1;
    n = 2 * (nyq - 1);
    indices = mod(indices + n, n);
    indices(indices >= nyq) = n - indices(indices >= nyq);
    indices = indices + 1;
end

function [value, i] = masked_max(data, mask, start, finish)
    if ~exist('start', 'var'); start = 1; end;
    if ~exist('finish', 'var'); finish = length(data); end
    [~, indices] = masked_subset(mask, start, finish);
    [value, i] = max(data(indices));
    i = indices(i);
end

function [value, num_bins] = masked_sum(data, mask, start, finish)
    if ~exist('start', 'var'); start = 1; end;
    if ~exist('finish', 'var'); finish = length(data); end
    [mask, indices] = masked_subset(mask, start, finish);
    value = sum(data(indices));
    num_bins = nnz(mask);
end

function [value, num_bins] = masked_sum_of_sq(data, mask, start, finish)
    if ~exist('start', 'var'); start = 1; end;
    if ~exist('finish', 'var'); finish = length(data); end
    [mask, indices] = masked_subset(mask, start, finish);
    value = sum(data(indices).^2);
    num_bins = nnz(mask);
end

function [mask, indices] = masked_subset(mask, start, finish)
    n = length(mask);
    mapped_subset = map_nyquist(start:finish, n);
    indices = 1:min(finish, n);
    indices = indices(mapped_subset);
    mask = mask(mapped_subset);
    indices = indices(mask);
end



