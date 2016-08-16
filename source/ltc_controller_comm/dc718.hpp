#pragma once
#include <stdexcept>
#include "ftdi_adc.hpp"

namespace linear {

    class Dc718 : public FtdiAdc {
    public:
        Dc718(const Ftdi& ftdi, const LccControllerInfo& info) : 
            FtdiAdc(ftdi, info) { }
        ~Dc718() { }

        const char* DC718_ID_STRING  = "QUDATS,PIC,03,00,DC,DC718,CPLD,04---------------\n";
        const char* DC718_ID_STRING2 = "QUDATS,PIC,02,00,DC,DC718,CPLD,03---------------\n";
        bool VerifyId() {
            Write("i\n", 2);
            char buffer[Ftdi::EEPROM_ID_STRING_SIZE];
            auto num_read = Read(buffer, Ftdi::EEPROM_ID_STRING_SIZE);
            if (num_read != Ftdi::EEPROM_ID_STRING_SIZE) {
                Close();
                throw HardwareError("Not all EEPROM bytes received.");
            }
            if (strcmp(DC718_ID_STRING, buffer) == 0) {
                return true;
            } else if (strcmp(DC718_ID_STRING2, buffer) == 0) {
                return true;
            }
            return false;
        }
    };
}
