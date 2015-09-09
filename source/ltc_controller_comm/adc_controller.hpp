#pragma once

#include <cstdint>
#include <string>
#include <utility>
#include <stdexcept>
#include "controller.hpp"

#define NOT_SUPPORTED_ADC throw domain_error("This operation is not supported for ADC controllers.");

namespace linear {

    using std::string;
    using std::pair;
    using std::domain_error;

    class AdcController : public Controller {
    public:
    
        using Controller::SpiChipSelect;
        using Controller::Trigger;

        AdcController(Type type) : Controller(type) { }

        virtual bool FpgaGetIsLoaded(const string& fpga_filename) = 0;
        virtual void FpgaLoadFile(const string& fpga_filename) = 0;
        
        virtual void DataStartCollect(int total_bytes, Trigger trigger);
        virtual bool DataIsCollectDone();
        virtual void DataCancelCollect();

        int DataWrite(uint8_t* values, int num_values) override { NOT_SUPPORTED_ADC; }
        void DataCancelWrite() override { NOT_SUPPORTED_ADC; }
        
        virtual void SpiSend(uint8_t* values, int num_values) = 0;
        virtual void SpiReceive(uint8_t* values, int num_values) = 0;
        virtual void SpiTransceive(uint8_t* send_values, uint8_t* receive_values,
            int num_values) = 0;

        // Convenience SPI functions with "address/value" mode
        virtual void SpiSendAtAddress(uint8_t address, uint8_t* values, int num_values) = 0;
        void SpiSendAtAddress(uint8_t address, uint8_t value) {
            return SpiSendAtAddress(address, &value, 1);
        }
        virtual void SpiReceiveAtAddress(uint8_t address, uint8_t* values, int num_values) = 0;
        void SpiReceiveAtAddress(uint8_t address, uint8_t& value) {
            return SpiReceiveAtAddress(address, &value, 1);
        }

        // Low-level SPI routines
        virtual void SpiSetChipSelect(SpiChipSelect chip_select_level) = 0;
        virtual void SpiSendNoChipSelect(uint8_t* values, int num_values) = 0;
        virtual void SpiReceiveNoChipSelect(uint8_t* values, int num_values) = 0;
        virtual void SpiTransceiveNoChipSelect(uint8_t* send_values, uint8_t* receive_values,
            int num_values) = 0;
    };

}