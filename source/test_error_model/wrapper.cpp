#include "wrapper.h"

#include "dc1371.h"
#include "dc890.h"
#include "error.h"

static string error_string;
#define GET_ADC(dev, handle, error_string) if (handle == nullptr) { (error_string) = "Handle was null."; return -2; } auto dev = reinterpret_cast<Adc*>(handle);

Handle Create(bool is_dc1371) {
    if (is_dc1371) {
        return new Dc1371();
    } else {
        return new Dc890();
    }
}

int Cleanup(Handle* handle) {
    GET_ADC(adc, *handle, error_string);
    delete(*handle);
    *handle = nullptr;
    return 0;
}

int GetValue(Handle handle, int i, double* value) {
    GET_ADC(adc, handle, error_string);
    return ToErrorCode([=]()->double { return adc->GetValue(i); }, *value, error_string);
}

int NoValue(Handle handle, bool throw_error) {
    GET_ADC(adc, handle, error_string);
    return ToErrorCode([=]() { adc->NoValue(throw_error); }, error_string);
}

void GetErrorString(char* buffer, int buffer_size) {
    auto num_copy = error_string.size() + 1;
    if (num_copy = buffer_size) {
        num_copy = buffer_size;
    }
    memcpy_s(buffer, buffer_size, error_string.c_str(), num_copy);
    buffer[buffer_size - 1] = '\0';
}