function Ltc2270_dc1975
    
    % Returns the object in the class constructor
    comm = LtcControllerComm();
    
    % Print extra information to console
    verbose = true;
    % Plot data to screen
    plot_data = true;
    % Write data out to a text file
    write_to_file = true;

    % set test_data_reg to one of these constants
    DATA_REAL = 0;
    DATA_ALL_ZEROS = 8;
    DATA_ALL_ONES = 24;
    DATA_CHECKERBOARD = 40;
    DATA_ALTERNATING = 56;
    % test_data_reg = DATA_ALTERNATING
    test_data_reg = DATA_REAL;

    NUM_ADC_SAMPLES = 64 * 1024;
    SAMPLE_BYTES = 2;
    EEPROM_ID_SIZE = 48;
    
    eeprom_id = 'LTC2270,D9002,DC1975A-A,YGG200T,CMOS,-----------';
    % find demo board with correct ID
    fprintf('Looking for a DC890 with a DC1975A-A demoboard');
    
    deviceInfoList = comm.ListControllers(comm.TYPE_DC890, 1);
    did = comm.Init(deviceInfoList);
    
    for info = deviceInfoList
        if strcmp(eeprom_id, comm.EepromReadString(did, EEPROM_ID_SIZE))
            break;
        end
        did = comm.Cleanup(did);
    end
    
    if(did == 0)
        fprintf('\nDevice not found');
    else
        fprintf('\nDevice Found');
    end
    
    
end