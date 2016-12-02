classdef Ltc2000
    properties (Access = private)
        lcc;
        cid;
        expected_description;
        expected_id;
        expected_pll_status;
        expected_max_val;
        range_string;
        is_little_endian;
        size_lookup;
        verbose;
    end
    properties (Constant)
        FPGA_ID_REG = 0
        FPGA_CONTROL_REG = 1
        FPGA_STATUS_REG = 2
        FPGA_DAC_PD = 3
    end
    methods
        function self = Ltc2000(lcc, is_xilinx, spi_reg_values, verbose)
            self.lcc = lcc;
            self.verbose = verbose;
            if is_xilinx
                self.expected_description = 'LTC Communication Interface';
                self.expected_id = 32; % 0x20
                self.expected_pll_status = 6; % 0x06
                self.expected_max_val = 2 * 1024 * 1024;
                self.range_string = '16K to 2M';
                sizes = 2.^(0:7) * 16*1024;
                reg_values = uint8(bitshift(0:7, 4));
            else
                self.expected_description = 'LTC2000';
                self.expected_id = 26; % 0x1A
                self.expected_pll_status = 71; % 0x47
                self.expected_max_val = 512 * 1024 * 1024;
                self.range_string = '16K to 512M';
                sizes = 2.^(0:15) * 16*1024;
                reg_values = uint8(bitshift(0:15, 4));
            end
            self.size_lookup = containers.Map(sizes, reg_values);
            self = self.connect();
            self.init_controller(spi_reg_values);
        end
        
        function set_spi_registers(self, register_values)
            self.vprint('Configuring DAC over SPI');
            if ~isempty(register_values)
                for i = 1:2:length(register_values)
                    self.lcc.spi_send_byte_at_address(self.cid, ...
                        register_values(i), register_values(i+1));
                end
            end
        end
        
        function send_data(self, data)
            num_samples = length(data);
            num_samples_reg_value = self.size_lookup(num_samples);
            self.vprint('Reading PLL status');
            pll_status = self.lcc.hs_fpga_read_data_at_address(self.cid, Ltc2000.FPGA_STATUS_REG);
            if self.expected_pll_status ~= pll_status
                error('LtcControllerComm:HardwareError', 'FPGA PLL status was bad');
            end
            self.vprint('PLL status is OK');
            pause(0.1);
            self.lcc.hs_fpga_write_data_at_address(self.cid, ...
                Ltc2000.FPGA_CONTROL_REG, num_samples_reg_value);
            if self.lcc.is_little_endian
                self.lcc.data_set_low_byte_first(self.cid);
            else
                self.lcc.data.set_high_byte_first(self.cid);
            end
            
            self.lcc.hs_set_bit_mode(self.lcc.HS_BIT_MODE_FIFO);
            self.vprint('Sending data');
            num_bytes_sent = self.lcc.data_send_uint16_values(data);
            self.lcc.hs_set_bit_mode(self.lcc.HS_BIT_MODE_MPSSE);
            if num_bytes_sent ~= num_samples * 2
                error('LtcControllerComm:HardwareError', 'Not all data was sent');
            end
            self.vprint('All data was sent (%d bytes)', num_bytes_sent);
        end
    end
    
    methods (Access = private)
        function self = connect(self)
           self.vprint('Looking for Controller');
           for info = self.lcc.list_controllers(self.lcc.TYPE_HIGH_SPEED)
               description = info.get_description();
               if ~isempty(strfind(self.expected_description, description))
                   self.vprint('Found a possible setup');
                   self.cid = self.lcc.init(info);
                   return;
               end
           end
           error('LtcControllerComm:HardwareError', 'Could not find a compatible setup');
        end
        
        function init_controller(self, spi_reg_values)
            self.lcc.hs_set_bit_mode(self.cid, self.lcc.HS_BIT_MODE_MPSSE);
            self.lcc.hs_fpga_toggle_reset(self.cid);
            % Read FPGA ID register
            id = self.lcc.hs_fpga_read_data_at_Address(self.cid, Ltc2000.FPGA_ID_REG);
            self.vprint('FPGA Load ID: 0x%4X\n', id);
            if self.expected_id ~= id
                error('LtcControllerComm:HardwareError', 'Wrong FPGA Load');
            end
            self.lcc.hs_fpga_write_data_at_address(self.cid, Ltc2000.FPGA_DAC_PD, 1);
            self.lcc.set_spi_registers(self.cid, spi_reg_values);
        end
        
        function vprint(self, varargin)
            if self.verbose
                fprintf(varargin{:})
            end
        end
    end
end