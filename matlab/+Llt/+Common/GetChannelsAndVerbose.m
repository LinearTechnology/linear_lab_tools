function [verbose, channels] = GetChannelsAndVerbose(varargs)
    if isscalar(varargs{end})
        verbose = varargs{end};
        channels = varargs(1:(end-1));
    else
        verbose = false;
        channels = varargs;
    end
    
    