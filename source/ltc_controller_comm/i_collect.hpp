#pragma once
#include "controller.hpp"
namespace linear {
    class ICollect : virtual public Controller {
    public:
        enum class Trigger {
            NONE = LCC_TRIGGER_NONE,
            START_POSITIVE_EDGE = LCC_TRIGGER_START_POSITIVE_EDGE,
            DC890_START_NEGATIVE_EDGE = LCC_TRIGGER_DC890_START_NEGATIVE_EDGE,
            DC1371_STOP_NEGATIVE_EDGE = LCC_TRIGGER_DC1371_STOP_NEGATIVE_EDGE,
        };
        virtual void DataStartCollect(int total_samples, Trigger trigger) = 0;
        virtual bool DataIsCollectDone() = 0;
        virtual void DataCancelCollect() = 0;
        virtual ~ICollect() { }
    };
}

