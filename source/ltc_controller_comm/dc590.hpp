#pragma once
#include "basic_ftdi_controller.hpp"
#include "i_spi.hpp"

namespace linear {

using std::string;
using std::vector;

class Dc590 : public BasicFtdiController, public ISpi {
   public:
    Dc590(const Ftdi& ftdi, const LccControllerInfo& info) : BasicFtdiController(ftdi, info) {}
    virtual ~Dc590() {}

    void    SpiReceive(uint8_t values[], int num_values) override;
    void    SpiTransceive(uint8_t send_values[], uint8_t receive_values[], int num_values) override;
    void    SpiReceiveAtAddress(uint8_t address, uint8_t* values, int num_values) override;
    uint8_t SpiReceiveAtAddress(uint8_t address) override;
    void    SpiReceiveNoChipSelect(uint8_t values[], int num_values) override;
    void    SpiTransceiveNoChipSelect(uint8_t send_values[],
                                      uint8_t receive_values[],
                                      int     num_values) override;
    void    SpiSend(uint8_t values[], int num_values) override;
    void    SpiSendAtAddress(uint8_t address, uint8_t* values, int num_values) override;
    void    SpiSendAtAddress(uint8_t address, uint8_t value) override;
    void    SpiSetCsState(SpiCsState chip_select_state) override;
    void    SpiSendNoChipSelect(uint8_t values[], int num_values) override;

    using BasicFtdiController::Read;
    using BasicFtdiController::Write;

    void SetEventChar(bool enable);

    Controller::Type GetType() override { return BasicFtdiController::GetType(); }
    string           GetDescription() override { return BasicFtdiController::GetDescription(); }
    string           GetSerialNumber() override { return BasicFtdiController::GetSerialNumber(); }
    void             EepromReadString(char* buffer, int buffer_size) override {
        return BasicFtdiController::EepromReadString(buffer, buffer_size);
    }

    friend class Controller;
};
}
