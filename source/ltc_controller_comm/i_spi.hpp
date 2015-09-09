#pragma once
#include "i_spi_send_only.hpp"
namespace linear {
    class ISpi : public ISpiSendOnly{
    public:
        virtual void SpiReceive(uint8_t values[], int num_values) = 0;
        virtual void SpiTransceive(uint8_t send_values[], uint8_t receive_values[],
            int num_values) = 0;
        virtual void SpiReceiveAtAddress(uint8_t address, uint8_t* values, int num_values) = 0;
        virtual uint8_t SpiReceiveAtAddress(uint8_t address) = 0;
        virtual void SpiReceiveNoChipSelect(uint8_t values[], int num_values) = 0;
        virtual void SpiTransceiveNoChipSelect(uint8_t send_values[], uint8_t receive_values[],
            int num_values) = 0;
        virtual ~ISpi() { }
    };

}