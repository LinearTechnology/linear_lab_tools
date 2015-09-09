#pragma once
#include "error.h"
#include "adc.h"

class Dc890 : public Adc {
public:
    double GetValue(int i) override {
        if (i < 0) {
            throw invalid_argument("i cannot be negative.");
        } else if (i == 0) {
            throw FtdiError("simulated hardware error", 890);
        } else {
            return i;
        }
    }
    void NoValue(bool throw_error) override {
        if (throw_error) {
            throw FtdiError("simulated hardware error", -7);
        }
    }
};

