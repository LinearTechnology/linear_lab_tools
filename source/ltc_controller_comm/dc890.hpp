#pragma once
#include <fstream>
#include "i_spi_send_only.hpp"
#include "i_fpga_load.hpp"
#include "ftdi_adc.hpp"
#include "controller.hpp"
#include "error.hpp"

#define CHECK_BIT_VALUE(bit) if (bit < 0 || bit > 7) { throw invalid_argument(CAT(QUOTE(bit), " must be between 0 and 7, inclusive")); }

namespace linear {

    class Dc890 : public FtdiAdc, ISpiSendOnly, IFpgaLoad {
    public:
        Dc890(const Ftdi& ftdi, const LccControllerInfo& info) : 
            FtdiAdc(ftdi, info) { }
        ~Dc890() { }

        Type GetType() override { return FtdiAdc::GetType(); }
        string GetDescription() override { return FtdiAdc::GetDescription(); }
        string GetSerialNumber() override { return FtdiAdc::GetSerialNumber(); }
        void EepromReadString(char* buffer, int buffer_size) override { 
            return FtdiAdc::EepromReadString(buffer, buffer_size);
        }
        bool FpgaGetIsLoaded(const string& fpga_filename) override;
        int FpgaLoadFileChunked(const string& fpga_filename) override;
        void FpgaCancelLoad() override;

        void GpioSetByte(uint8_t byte) {
            base_byte = byte;
            GpioSendByte(byte);
        }
        void GpioSpiSetBits(int cs_bit, int sck_bit, int sdi_bit) {
            CHECK_BIT_VALUE(cs_bit);
            CHECK_BIT_VALUE(sck_bit);
            CHECK_BIT_VALUE(sdi_bit);
            cs_bit_mask  = 1 << cs_bit;
            sck_bit_mask = 1 << sck_bit;
            sdi_bit_mask = 1 << sdi_bit;
        }

        void SpiSend(uint8_t* values, int num_values) override;
        // Convenience SPI functions with "address/value" mode
        void SpiSendAtAddress(uint8_t address, uint8_t* values, int num_values) override;
        void SpiSendAtAddress(uint8_t address, uint8_t value) override {
            SpiSendAtAddress(address, &value, 1);
        }
        // Low-level SPI routines
        void SpiSetCsState(SpiCsState chip_select_level) override;
        void SpiSendNoChipSelect(uint8_t* values, int num_values) override;
    private:
        struct FpgaLoad {
            uint16_t load_id;
            uint8_t revision;
            FpgaLoad(uint16_t load_id = 0, uint8_t revision = 0) : load_id(load_id), revision(revision) { }
        };

        static const int FPGA_PAGE_SIZE = 256;
        static const int NUM_FPGA_PAGES = 512;
        class FpgaPageBuffer {
        public:
            static const int FPGA_SIZE = NUM_FPGA_PAGES * FPGA_PAGE_SIZE;
            FpgaPageBuffer() = default;
            ~FpgaPageBuffer() {
                delete file;
            }
            void Reset(const wstring& path);
            void Reset();
            explicit operator bool() {
                return file != nullptr;
            }
            bool GetPage(char data[FPGA_PAGE_SIZE]);
        private:
            std::ifstream* file = nullptr;
            int total_bytes = 0;
            int page_bytes = 0;
            char buffer[2 * FPGA_PAGE_SIZE];
        };

        int FpgaFileToFlashChunked(const wstring& path);
        bool FpgaFlashToLoaded(uint16_t load_id, uint8_t revision);
        wstring FpgaGetPath(const string& load_filename);
        FpgaLoad GetFpgaLoadIdFromFile(const string& fpga_filename);
        void GpioSendByte(uint8_t byte);
        uint8_t base_byte = 0;
        uint8_t cs_bit_mask = 0;
        uint8_t sck_bit_mask = 0;
        uint8_t sdi_bit_mask = 0;
        bool fpga_load_started = false;
        int fpga_load_progress = NUM_FPGA_PAGES;
        int fpga_page_index = 0;
        FpgaPageBuffer fpga_page_buffer;
        char fpga_page_data[FPGA_PAGE_SIZE];
    };
}
