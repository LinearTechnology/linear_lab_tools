function lt2k = Ltc2123Functions(lths)

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% SPI read / write bit definitions %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

lt2k.SPI_READ = 128; % OR with register
lt2k.SPI_WRITE = 0;

% FPGA register addresses
lt2k.ID_REG = 0;
lt2k.CAPTURE_CONFIG_REG = 1;
lt2k.CAPTURE_CONTROL_REG = 2;
lt2k.CAPTURE_RESET_REG = 3;
lt2k.CAPTURE_STATUS_REG = 4;
lt2k.SPI_CONFIG_REG = 5;
lt2k.CLOCK_STATUS_REG = 6;
lt2k.JESD204B_WB0_REG = 7;
lt2k.JESD204B_WB1_REG = 8;
lt2k.JESD204B_WB2_REG = 9;
lt2k.JESD204B_WB3_REG = 10;
lt2k.JESD204B_CONFIG_REG = 11;
lt2k.JESD204B_RB0_REG = 12;
lt2k.JESD204B_RB1_REG = 13;
lt2k.JESD204B_RB2_REG = 14;
lt2k.JESD204B_RB3_REG = 15;
lt2k.JESD204B_CHECK_REG = 16;

lt2k.JESD204B_W2INDEX_REG = 18;
lt2k.JESD204B_R2INDEX_REG = 19;

% Register names for basic configuration
lt2k.JESD204B_XILINX_CONFIG_REG_NAMES = {'             Version', '               Reset', '         ILA Support', '          Scrambling',...
                                    '     SYSREF Handling', '         Reserved...', '          Test Modes', '  Link err stat, 0-7',...
                                    '        Octets/frame', 'frames/multiframe(K)', '        Lanes in Use', '            Subclass',...
                                    '        RX buf delay', '     Error reporting', '         SYNC Status', ' Link err stat, 8-11'};

% Register names for per-lane information
lt2k.JESD204B_XILINX_LANE_REG_NAMES = {'  ILA config Data 0', '  ILA config Data 1', '  ILA config Data 2', '  ILA config Data 3',... 
                                  '  ILA config Data 4', '  ILA config Data 5', '  ILA config Data 6', '  ILA config Data 7',...
                                  '  Test Mode Err cnt', '       Link Err cnt', '  Test Mode ILA cnt', 'Tst Mde multif. cnt',...
                                  '      Buffer Adjust'};


end