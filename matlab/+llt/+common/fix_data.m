function data = fix_data(data, num_bits, alignment, is_bipolar, is_randomized, is_alternate_bit)
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

    if ~exist('is_randomized', 'var')
        is_randomized = false;
    end
    if ~exist('is_alternate_bit', 'var')
        is_alternate_bit = false;
    end
    
    if alignment < num_bits
        error('FixData:BadAlignment', 'alignment must be >= numBits');
    end
    if  alignment > 30
        error('FixData:BadAlignment', 'Does not support alignment greater than 30 bits');
    end
    
    switch class(data(1))
        case { 'int16', 'uint16' }
            if is_bipolar
                data = int32(data);
                internator = @int32;
            else
                data = uint32(data);
                internator = @uint32;
            end
        case { 'int32', 'uint32' }
            if is_bipolar
                data = typecast(data, 'int32');
                internator = @int32;
            else
                data = typecast(data, 'uint32');
                internator = @uint32;
            end
    end  
    num_shift = internator(alignment - num_bits);
    sign_bit = internator(bitshift(1, num_bits - 1));
    offset = internator(bitshift(1, num_bits));
    mask = internator(offset - 1); 
    
    for i = 1:length(data)
        x = data(i);
        x = bitshift(x, -num_shift);
        if is_randomized && (bitand(x, 1))
            x = bitxor(x, 1073741822); % 0x3FFFFFFE
        end
        if is_alternate_bit
            x = bitxor(x, 715827882); % 0x2AAAAAAA
        end
        x = bitand(x, mask);
        if is_bipolar && bitand(x, sign_bit)
            x = x - offset;
        end
        data(i) = x;
    end
    data = double(data);
