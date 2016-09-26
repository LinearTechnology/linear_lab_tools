function varargout = Scatter(data)
nChannels = nargout;
if mod(length(data), nChannels) ~= 0
    error('Scatter:BadNChannels', 'nChannels doesn''t divide data length');
end

for i = 1:nChannels
    varargout{i} = data(i:nChannels:end);
end