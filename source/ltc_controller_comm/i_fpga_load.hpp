#pragma once
#include "controller.hpp"
namespace linear {
    class IFpgaLoad : virtual public Controller {
    public:
        virtual bool FpgaGetIsLoaded(const string& fpga_filename) = 0;
        virtual void FpgaLoadFile(const string& fpga_filename) = 0;
        virtual ~IFpgaLoad() { }
    };
}

