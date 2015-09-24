#pragma once
#include "controller.hpp"
namespace linear {
    class IDataReceive : virtual public Controller {
    public:
        virtual int DataReceive(uint8_t data[], int total_bytes) = 0;
        virtual int DataReceive(uint16_t data[], int total_values) = 0;
        virtual int DataReceive(uint32_t data[], int total_values) = 0;
        virtual ~IDataReceive() { }
    };
}

