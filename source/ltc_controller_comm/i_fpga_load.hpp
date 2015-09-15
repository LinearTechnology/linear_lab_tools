#pragma once
#include "controller.hpp"
namespace linear {
    class IFpgaLoad : virtual public Controller {
    public:
        virtual bool FpgaGetIsLoaded(const string& fpga_filename) = 0;
        virtual void FpgaLoadFile(const string& fpga_filename) {
            while (FpgaLoadFileChunked(fpga_filename) != 0) { continue; }
        }
        virtual int FpgaLoadFileChunked(const string& fpga_filename) = 0;
        virtual void FpgaCancelLoad() = 0;
        virtual ~IFpgaLoad() { }
    };
}

