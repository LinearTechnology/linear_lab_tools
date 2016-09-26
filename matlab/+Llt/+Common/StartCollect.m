function StartCollect(lcc, cid, nSamples, trigger, timeout)
if ~exist('timeout', 'var'); timeout = 5; end

lcc.DataStartCollect(cid, nSamples, trigger);
SLEEP_TIME = 0.2;
nLoop = ceil(timeout / SLEEP_TIME);
for i = 1:nLoop
    if lcc.DataIsCollectDone(cid)
        return;
    end
    sleep(SLEEP_TIME);
end
error('LtcControllerComm:HardwareError', ...
    'Data collect timed out (missing clock?)');
