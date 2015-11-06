function LoadLtc212x(device, csControl, verbose, dId, bankId, lanes, K, modes, subClass, pattern)
    if(verbose)
        fprintf('Configuring ADCs over SPI:');
    end
    device.HsFpgaWriteDataAtAddress(cId, lt2k.SPI_CONFIG_REG, csControl);
    SpiWrite(device, 3, dId); % Device ID to 0xAB
    SpiWrite(device, 4, bankId); % Bank ID to 0x01
    SpiWrite(device, 5, lanes-1); % 2 lane mode (default)
    SpiWrite(device, 6, K-1);
    SpiWrite(device, 7, modes); % Enable FAM, LAM
    SpiWrite(device, 8, subClass); % Subclass mode
    SpiWrite(device, 9, pattern); % PRBS test pattern
    SpiWrite(device, 10, 3); %  0x03 = 16mA CML current
end 