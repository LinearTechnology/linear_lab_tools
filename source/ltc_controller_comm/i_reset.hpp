#pragma once
#include "controller.hpp"
namespace linear {
    class IReset : virtual public Controller {
    public:
        virtual void Reset() = 0;
        virtual ~IReset() { }
    };
}

