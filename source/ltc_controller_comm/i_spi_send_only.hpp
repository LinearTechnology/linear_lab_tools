#pragma once
#include "controller.hpp"
#include "ltc_controller_comm.h"
namespace linear {
    class ISpiSendOnly : virtual public Controller {
    public:
        enum class SpiCsState {
            LOW = LCC_SPI_CS_STATE_LOW,
            HIGH = LCC_SPI_CS_STATE_HIGH
        };
        virtual void SpiSend(uint8_t values[], int num_values) = 0;
        virtual void SpiSendAtAddress(uint8_t address, uint8_t* values, int num_values) = 0;
        virtual void SpiSendAtAddress(uint8_t address, uint8_t value) = 0;
        virtual void SpiSetCsState(SpiCsState chip_select_state) = 0;
        virtual void SpiSendNoChipSelect(uint8_t values[], int num_values) = 0;
        virtual ~ISpiSendOnly() { }
    };

}

