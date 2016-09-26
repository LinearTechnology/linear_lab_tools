function win = Window(n, windowType)
    if ~exist('windowType', 'var')
        windowType = 'BlackmanHarris92';
    end
    
    switch lower(windowType)
        case 'hamming'
            win = OneCos(n, 0.54, 0.46, 1.586303);
    
        case 'hann'
            win = OneCos(n, 0.50, 0.50, 1.632993);
    
        case 'blackman'
            win = TwoCos(n, 0.42, 0.50, 0.08, 1.811903);

        case 'blackmanexact'
            win = TwoCos(n, 0.42659071, 0.49656062, 0.07684867, 1.801235);

	    case 'blackmanharris70' % from: www.mathworks.com/access/helpdesk/help/toolbox/signal/window.shtml
            win = TwoCos(n, 0.42323, 0.49755, 0.07922, 1.807637);

        case 'flattop'
            win = TwoCos(n, 0.2810639, 0.5208972, 0.1980399, 2.066037);
        
        case 'blackmanharris92' % from: www.mathworks.com/access/helpdesk/help/toolbox/signal/window.shtml
            win = ThreeCos(n, 0.35875, 0.48829, 0.14128, 0.01168, 1.968888);
        
        otherwise
            error('Window:BadWindowType', 'Unexpected window type %s', windowType);
    end
end

function win = OneCos(n, a0, a1, norm)
    nMinus1 = n - 1;
    t = (0:nMinus1) / nMinus1;
    win = a0 - a1 * cos(2*pi * t);
    win = win(:) * norm;
end

function win = TwoCos(n, a0, a1, a2, norm)
    nMinus1 = n - 1;
    t = (0:nMinus1) / nMinus1;
    win = a0 - a1*cos(2*pi * t) + a2*cos(4*pi * t);
    win = win(:) * norm;
end

function win = ThreeCos(n, a0, a1, a2, a3, norm)
    nMinus1 = n - 1;
    t = (0:nMinus1) / nMinus1;
    win = a0 - a1*cos(2*pi * t) + a2*cos(4*pi * t) - a3*cos(6*pi * t);
    win = win(:) * norm;
end
        
