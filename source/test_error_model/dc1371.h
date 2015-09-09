#pragma once
#include "error.h"
#include "adc.h"

class Dc1371 : public Adc {
public:
    double GetValue(int i) override {
        if (i < 0) {
            throw invalid_argument("i cannot be negative.");
        } else if (i == 0) {
            throw Dc1371Error("simulated hardware error", 2);
        } else {
            return i;
        }
    }
    void NoValue(bool throw_error) override {
        if (throw_error) {
            throw Dc1371Error("simulated hardware error", 13);
        }
    }
};

