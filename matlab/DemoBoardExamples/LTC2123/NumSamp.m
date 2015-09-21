classdef NumSamp
    properties
        MemSize;
        BuffSize;
    end
    methods
        function obj = NumSamp(memSize, buffSize)
            this.MemSize = memSize;
            this.BuffSize = buffSize;
        end
    end
end
