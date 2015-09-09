#pragma once
#include <stdexcept>
#include "ftdi_adc.hpp"

namespace linear {

    class Dc718 : public FtdiAdc {
    public:
        Dc718(const Ftdi& ftdi, const LccControllerInfo& info) : 
            FtdiAdc(ftdi, info) { }
        ~Dc718() { }
    };
}
