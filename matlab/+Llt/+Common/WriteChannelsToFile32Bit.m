function WriteChannelsToFile32Bit(filename, varargin)
[verbose, channels] = Llt.Common.GetChannelsAndVerbose(varargin);

append = false;
for ch = channels
    Llt.Common.WriteToFile32Bit(filename, ch{1}, append, verbose);
    append = true;
end