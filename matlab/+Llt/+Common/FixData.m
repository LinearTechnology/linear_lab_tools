function data = FixData(data, numBits, alignment, isBipolar, isRandomized, isAlternateBit)
    % Converts data from n-bit count to the correct numerical value.
    % 
    % Does sign extension for 2's complement, adjusts for alignemnt, and decodes the
    % randomizer and alternate bit polarity affects, if applicable. 
    %
    % Copyright (c) 2015, Linear Technology Corp.(LTC)
    % All rights reserved.
    % 
    % Redistribution and use in source and binary forms, with or without
    % modification, are permitted provided that the following conditions are met:
    % 
    % 1. Redistributions of source code must retain the above copyright notice, 
    %    this list of conditions and the following disclaimer.
    % 2. Redistributions in binary form must reproduce the above copyright 
    %    notice, this list of conditions and the following disclaimer in the 
    %    documentation and/or other materials provided with the distribution.
    % 
    % THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
    % AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE 
    % IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE 
    % ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE 
    % LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
    % CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF 
    % SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS 
    % INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN 
    % CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
    % ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE 
    % POSSIBILITY OF SUCH DAMAGE.
    % 
    % The views and conclusions contained in the software and documentation are 
    % those of the authors and should not be interpreted as representing official
    % policies, either expressed or implied, of Linear Technology Corp.

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
    
    internator = @uint32;
    if isBipolar; internator = @int32; end
    
    nShift = alignment - numBits;
    signBit = internator(bitshift(1, numBits - 1));
    offset = bitshift(1, numBits);
    mask = internator(offset) - 1;
    
    for i = 1:length(data)
        x = internator(data(i));
        x = bitshift(x, -nShift);
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
