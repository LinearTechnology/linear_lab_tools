function controller_info = get_controller_info_by_eeprom(lcc, ...
        type, dc_number, num_chars, is_verbose)
% Finds a demoboard with the desired DC number
% 
% Looks for all controller types specified in 'type', opens them one at
% a time and queries the eeprom string, when it finds one that contains
% 'dcNumber' it returns a 'controllerInfo' struct. All controllers are
% cleaned up before return, including the one whose 'controllerInfo' isVerbose
% returned.
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
    
if is_verbose; fprintf('Looking for a controller board...'); end

controller_info = [];
info_list = lcc.list_controllers(type);
for info = info_list
    cid = lcc.init(info);
    eeprom_id = lcc.eeprom_read_string(cid, num_chars);
    lcc.cleanup(cid);
    if ~isempty(strfind(eeprom_id, dc_number))
        if is_verbose
            fprintf('found the %s demoboard.\n', dc_number);
        end
        controller_info = info;
        return;
    end
end
            