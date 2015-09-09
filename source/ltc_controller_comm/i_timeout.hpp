#pragma once
#include "controller.hpp"
#include <utility>
namespace linear {
    class ITimeout : virtual public Controller {
    public:
        virtual void SetTimeouts(unsigned long read_timeout, unsigned long write_timeout) = 0;
        virtual std::pair<unsigned long, unsigned long> GetTimeouts() = 0;
        virtual ~ITimeout() { }
    };
}

