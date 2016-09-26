function WriteToFile32Bit(filename, data, append, isVerbose)
if ~exist('append', 'var'); append = false; end
if ~exist('isVerbose', 'var'); isVerbose = false; end

if isVerbose; fprintf('Writing data to file...'); end

openStr = 'wt';
if append; openStr = 'at'; end

fid = fopen(filename, openStr);
for d = data
    fprintf(fid, '%d\n', d);
end
fclose(fid);

if isVerbose; fprintf('done.\n'); end

