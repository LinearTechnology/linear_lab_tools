function PlotChannels(numBits, varargin)
[verbose, channels] = Llt.Common.GetChannelsAndVerbose(varargin);

i = 0;
for data = channels
    Llt.Common.Plot(data{1}, numBits, i, verbose);
    i = i + 1;
end