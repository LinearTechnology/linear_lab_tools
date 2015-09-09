#pragma once
#include "controller.hpp"
namespace linear {
    class IClose: virtual public Controller {
    public:
        virtual void Close() = 0;
        virtual ~IClose() { }
    };
}

