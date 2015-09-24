#pragma once
#include "controller.hpp"
namespace linear {
    class IDataSend : virtual public Controller {
    public:
        virtual int DataSend(uint8_t data[], int total_bytes) = 0;
        virtual int DataSend(uint16_t data[], int total_values) = 0;
        virtual int DataSend(uint32_t data[], int total_values) = 0;
        virtual ~IDataSend() { }
    };
}

