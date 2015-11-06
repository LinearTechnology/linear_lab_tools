% Adding support for V6 core, with true AXI access. Need to confirm that this 
% doesn't break anything with V4 FPGA loads,
% as we'd be writing to undefined registers.
function WriteJesd204bReg(device, address, b3, b2, b1, b0)
    device.HsFpgaWriteDataAtAddress(cId, lt2k.JESD204B_WB3_REG, b3);
    device.HsFpgaWriteDataAtAddress(cId, lt2k.JESD204B_WB2_REG, b2);
    device.HsFpgaWriteDataAtAddress(cId, lt2k.JESD204B_WB1_REG, b1);
    device.HsFpgaWriteDataAtAddress(cId, lt2k.JESD204B_WB0_REG, b0);
    device.HsFpgaWriteDataAtAddress(cId, lt2k.JESD204B_W2INDEX_REG, (bitand(address, 4032) / 6)); % Upper 6 bits of AXI reg address
    device.HsFpgaWriteDataAtAddress(cId, lt2k.JESD204B_CONFIG_REG, (bitor((bitand(address, 63) * 4), 2)));
    x = device.HsFpgaReadDataAtAddress(cId, lt2k.JESD204B_CONFIG_REG);
    if (bitand(x, 1) == 0)
        error('Got bad FPGA status in write_jedec_reg');
    end
end 