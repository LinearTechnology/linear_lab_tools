#pragma once
#include "controller.hpp"
namespace linear {
    class IDataEndian : virtual public Controller {
    public:
        virtual void DataSetHighByteFirst() = 0;
        virtual void DataSetLowByteFirst() = 0;
            virtual ~IDataEndian() { }
    };
}

