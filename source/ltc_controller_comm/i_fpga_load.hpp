#pragma once
#include "controller.hpp"
#include <experimental/filesystem>
using std::experimental::filesystem::path;
namespace linear {
    class IFpgaLoad : virtual public Controller {
    public:
        virtual bool FpgaGetIsLoaded(const string& fpga_filename) = 0;
        virtual void FpgaLoadFile(const string& fpga_filename) {
            while (FpgaLoadFileChunked(fpga_filename) != 0) { continue; }
        }
        virtual int FpgaLoadFileChunked(const path& fpga_filename) = 0;
        virtual void FpgaCancelLoad() = 0;
        virtual ~IFpgaLoad() { }
    };
}

