function data = FixData(data, numBits, alignment, isBipolar, isRandomized, isAlternateBit)
    if ~exist('isRandomized', 'var')
        isRandomized = false;
    end
    if ~exist('isAlternateBit', 'var')
        isAlternateBit = false;
    end
    
    if alignment < numBits
        error('FixData:BadAlignment', 'alignment must be >= numBits');
    end
    if  alignment > 30
        error('FixData:BadAlignment', 'Does not support alignment greater than 30 bits');
    end
    nShift = alignment - numBits;
    signBit = uint32(bitshift(1, numBits - 1));
    offset = bitshift(1, numBits);
    mask = uint32(offset) - 1;
    
    for i = 1:length(data)
        x = uint32(data(i));
        x = bitshift(x, nShift);
        if isRandomized && (bitand(x, 1))
            x = xor(x, hex2dec('0x3FFFFFFE'));
        end
        if isAlternateBit
            x = xor(x, hex2dec('0x2AAAAAAA'));
        end
        x = bitand(x, mask);
        if isBipolar && bitand(x, signBit)
            x = x - offset;
        end
        data(i) = x;
    end
