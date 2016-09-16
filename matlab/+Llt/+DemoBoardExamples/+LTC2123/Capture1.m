
% Capture a single channel on a single lane
% NEED TO TEST!!
function channelData = Capture1(device, memSize, buffSize, channels, lanes, dumpData, dumpPscopeData, verbose)
    device.HsSetBitMode(cId, device.HS_BIT_MODE_MPSSE);
    dec = 0;
    
    if(channels == 1)
        device.HsFpgaWriteDataAtAddress(cId, lt2k.CAPTURE_CONFIG_REG, uint8(bitor(memSize, 0))); % Channel A active
    elseif(channels == 2)
        device.HsFpgaWriteDataAtAddress(cId, lt2k.CAPTURE_CONFIG_REG, uint8(bitor(memSize, 2))); % Channel B active
    end
    
    device.HsFpgaWriteDataAtAddress(cId, lt2k.CAPTURE_CONTROL_REG, 1);   % Reset
    device.HsFpgaWriteDataAtAddress(cId, lt2k.CAPTURE_CONTROL_REG, 1);   % Start
    pause(1);  % wait for capture
    
    captureStatus = device.HsFpgaReadDataAtAddress(cId, lt2k.CAPTURE_STATUS_REG);
    if(bitand(captureStatus, 4) ~= 0)
        syncErr = 1;
    else
        syncErr = 0;
    end
    
    if (verbose ~= 0)
        fprintf('\nReading capture status, should be 0x31 (CH0, CH1 valid, Capture done, data not fetched)');
        fprintf('\nAnd it is... 0x%s', dec2hex(captureStatus, 4));
    end
    
    device.DataSetLowByteFirst(cId); % Set endian-ness
    device.HsSetBitMode(cId, device.HS_BIT_MODE_FIFO);
    pause(0.1);
    
    [data, nSampsRead] = device.DataReceiveUint16Values(cId, buffSize + 100);
    device.HsSetBitMode(cId, device.HS_BIT_MODE_MPSSE);
    
    pause(sleepTime);
    
    if(verbose ~= 0)
        fprintf('\nRead out %d samples for CH0, 1', nSampsRead);
    end
    
end
    
  
    
    

            
    # Split CH0, CH1
    data_ch0 = data[:]
    data_ch1 = data[:]

    if(lanes == 1): #EXPERIMENT!!!
        for i in range(0, (n.BuffSize)/4):
            data[i*4+0] = data_ch0[i*4+0]
            data[i*4+1] = data_ch0[i*4+2]
            data[i*4+2] = data_ch0[i*4+1]
            data[i*4+3] = data_ch0[i*4+3]

    if(channels != 3): #One channel only
    #if(1==1): # Force print single array
        if(dumpdata !=0):
            for i in range(0, min(dumpdata, n.BuffSize)):
                if(hex == 1 & dec == 1):
                    print '0x' + '{:04X}'.format(data[i]) + ', ' + str(data[i])     # UN-comment for hex
                    ##print '0x' + '{:016b}'.format(data[i]) + ', ' + str(data[i])   # UN-comment for binary
                elif(hex == 1):
                    print '0x' + '{:04X}'.format(data[i])
                elif(dec == 1):
                    print data[i]

    else: #Two channels

        if(dumpdata !=0):
            for i in range(0, min(dumpdata, n.BuffSize/2)):
                if(hex == 1 & dec == 1):
                    print '0x' + '{:04X}'.format(data[2*i]) + ', ' + str(data[2*i]) + ', 0x' + '{:04X}'.format(data[2*i+1]) + ', ' + str(data[2*i+1])     # UN-comment for hex
                    #print '0b' + '{:016b}'.format(data[i]) + ', ' + str(data[i])   # UN-comment for binary
                elif(hex == 1):
                    print '0x' + '{:04X}'.format(data_ch0[i]) + ', 0x' + '{:04X}'.format(data_ch1[i])
                elif(dec == 1):
                    print str(data[2*i]) + ", " + str(data[2*i+1])

    if(dump_pscope_data != 0):
        outfile = open("pscope_data.csv", "w")
        for i in range(0, n.BuffSize/2):
            outfile.write("{:d}, ,{:d}\n".format((data_ch0[i]-32768)/4, (data_ch1[i]-32768)/4))

        outfile.write("End\n")
        outfile.close()

    nSamps_per_channel = n.BuffSize
    return data, data_ch0, data_ch1, nSamps_per_channel, syncErr

