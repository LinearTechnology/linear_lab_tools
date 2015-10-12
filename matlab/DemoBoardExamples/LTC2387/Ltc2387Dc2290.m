function Ltc2387Dc2290
    
    % Print extra information to console
    VERBOSE = true;
    % Plot data to screen
    plotData = true;
    % Write data out to a text file
    writeToFile = true;

    % set testDataReg to one of these constants
    DATA_REAL = 0;
    DATA_ALL_ZEROS = 8;
    DATA_ALL_ONES = 24;
    DATA_CHECKERBOARD = 40;
    DATA_ALTERNATING = 56;
    % testDataReg = DATA_CHECKERBOARD
    testDataReg = DATA_REAL;

    NUM_ADC_SAMPLES = 16 * 1024;
    SAMPLE_BYTES = 3;
    EEPROM_ID_SIZE = 48;

    % Returns the object in the class constructor
    comm = LtcControllerComm();  
    
    % find demo board with correct ID
    EEPROM_ID = 'LTC2387,D2433,DC2290A,YII101Q,NONE,-------------';
    eepromIdSize = length(EEPROM_ID);
    fprintf('Looking for a DC718 with a DC2290A demoboard');
    
    deviceInfoList = comm.ListControllers(comm.TYPE_DC890, 1);
    
	% Open communication to the device
    cId = comm.Init(deviceInfoList);
    
    for info = deviceInfoList
        if strcmp(eepromId, comm.EepromReadString(cId, eepromIdSize))
            break;
        end
        cId = comm.Cleanup(cId);
    end
    
    if(cId == 0)
        fprintf('\nDevice not found');
    else
        fprintf('\nDevice Found');
    end
    
    if(VERBOSE)
        fprintf('\nStarting Data Collect');
    end 
 
    comm.DataSetCharacteristics(cId, false, SAMPLE_BYTES, false);
    comm.DataStartCollect(cId, NUM_ADC_SAMPLES, comm.TRIGGER_NONE);
    
    for i = 1: 10
        isDone = comm.DataIsCollectDone(cId);
        if(isDone)
            break;
        end
        pause(0.2);
    end
    
    if(isDone ~= true)
        comm.DataCancelCollect(cId);
        error('LtcControllerComm:HardwareError', 'Data collect timed out (missing clock?)');
    end
    
    if(VERBOSE)
        fprintf('\nData Collect done');
    end
    
    if(VERBOSE)
        fprintf('\nReading data');
    end
    
    [dataBytes, numBytes] = comm.DataReceiveUint16Values(cId, TOTAL_ADC_SAMPLES);
    
    if(VERBOSE)
        fprintf('\nData read done, parsing data...');
    end
    
    data = zeros(1, NUM_ADC_SAMPLES);
    for i = 1:NUM_ADC_SAMPLES
        d1 = bitand((uint8(dataBytes(i * 3 - 2)) * 65536), 16711680);
        d2 = bitand((uint8(dataBytes(i * 3 - 1)) * 256), 65280);
        d3 = bitand(uint8(dataBytes(i * 3)), 255);
        data(i) = bitor(bitor(d1, d2), d3);
        if(data(i) > 131072)
            data(i) = data(i) - 262144;
        end
    end
    
    if(writeToFile)
        if(verbose)
            fprintf('\nWriting data to file');
        end    

        fileID = fopen('data.txt','w');

        for i = 1:NUM_ADC_SAMPLES
            fprintf(fileID,'%d\r\n', data(i));
        end

        fclose(fileID);
        fprintf('\nFile write done');
    end
    
    if(plotData == true)
        figure(1)
        plot(data)
    end
end