function controllerInfo = GetControllerInfoByEeeprom(lcc, ...
                type, dcNumber, nChars, isVerbose)
if isVerbose; fprintf('Looking for a controller board...'); end

controllerInfo = [];
infoList = lcc.ListControllers(type);
for info = infoList
    cid = lcc.Init(info);
    eepromId = lcc.EepromReadString(cid, nChars);
    lcc.Cleanup(cid);
    if ~isempty(strfind(eepromId, dcNumber))
        if isVerbose
            fprintf('found the %s demoboard.\n', dcNumber);
        end
        controllerInfo = info;
        return;
    end
end
            