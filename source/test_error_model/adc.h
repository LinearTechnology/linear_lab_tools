#pragma once
class Adc {
public:
    virtual double GetValue(int) = 0;
    virtual void NoValue(bool throw_error) = 0;
};

