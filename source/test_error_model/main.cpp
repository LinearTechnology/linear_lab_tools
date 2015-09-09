#include "wrapper.h"
#include <iostream>
#include <string>
using std::cout;
using std::string;
using std::to_string;

int main() {
    double value;

    auto dc1371 = Create(true);

    auto result = GetValue(dc1371, 22, &value);
    if (result != 0) {
        char message[256];
        GetErrorString(message, 256);
        cout << string("Error: ") + message + " (" + to_string(result) + ")\n";
        return result;
    } else {
        cout << "value is " + to_string(value) + ".\n";
    }
    
    result = GetValue(dc1371, -1, &value);
    if (result != 0) {
        char message[256];
        GetErrorString(message, 256);
        cout << string("(expected) error: ") + message + " (" + to_string(result) + ")\n";
    } else {
        cout << "Whoa, bad! This should be an error but isn't!\n";
        cout << "value is " + to_string(value) + ".\n";
        return -99;
    }

    result = GetValue(dc1371, 0, &value);
    if (result != 0) {
        char message[256];
        GetErrorString(message, 256);
        cout << string("(expected) error: ") + message + " (" + to_string(result) + ")\n";
    } else {
        cout << "Whoa, bad! This should be an error but isn't!\n";
        cout << "value is " + to_string(value) + ".\n";
        return -99;
    }

    result = NoValue(dc1371, false);
    if (result != 0) {
        char message[256];
        GetErrorString(message, 256);
        cout << string("Error: ") + message + " (" + to_string(result) + ")\n";
        return result;
    } else {
        cout << "NoValue\n";
    }

    result = NoValue(dc1371, true);
    if (result != 0) {
        char message[256];
        GetErrorString(message, 256);
        cout << string("(expected) error: ") + message + " (" + to_string(result) + ")\n";
    } else {
        cout << "Whoa, bad! This should be an error but isn't!\n";
        return -99;
    }
    
    result = Cleanup(&dc1371);
    if (result != 0) {
        char message[256];
        GetErrorString(message, 256);
        cout << string("Error: ") + message + " (" + to_string(result) + ")\n";
    } else {
        cout << "Cleanup\n";
    }

    result = GetValue(dc1371, 5, &value);
    if (result == 0) {
        cout << "Whoa, bad! This should be an error but isn't!\n";
        return -99;
    } else {
        char message[256];
        GetErrorString(message, 256);
        cout << string("(Expected) error: ") + message + " (" + to_string(result) + ")\n";
    }


    auto dc890 = Create(false);

    result = GetValue(dc890, 36, &value);
    if (result != 0) {
        char message[256];
        GetErrorString(message, 256);
        cout << string("Error: ") + message + " (" + to_string(result) + ")\n";
        return result;
    } else {
        cout << "value is " + to_string(value) + ".\n";
    }

    result = GetValue(dc890, -1, &value);
    if (result != 0) {
        char message[256];
        GetErrorString(message, 256);
        cout << string("(expected) error: ") + message + " (" + to_string(result) + ")\n";
    } else {
        cout << "Whoa, bad! This should be an error but isn't!\n";
        cout << "value is " + to_string(value) + ".\n";
        return -99;
    }

    result = GetValue(dc890, 0, &value);
    if (result != 0) {
        char message[256];
        GetErrorString(message, 256);
        cout << string("(expected) error: ") + message + " (" + to_string(result) + ")\n";
    } else {
        cout << "Whoa, bad! This should be an error but isn't!\n";
        cout << "value is " + to_string(value) + ".\n";
        return -99;
    }

    result = NoValue(dc890, false);
    if (result != 0) {
        char message[256];
        GetErrorString(message, 256);
        cout << string("Error: ") + message + " (" + to_string(result) + ")\n";
        return result;
    } else {
        cout << "NoValue\n";
    }

    result = NoValue(dc890, true);
    if (result != 0) {
        char message[256];
        GetErrorString(message, 256);
        cout << string("(expected) error: ") + message + " (" + to_string(result) + ")\n";
    } else {
        cout << "Whoa, bad! This should be an error but isn't!\n";
        return -99;
    }

    result = Cleanup(&dc890);
    if (result != 0) {
        char message[256];
        GetErrorString(message, 256);
        cout << string("Error: ") + message + " (" + to_string(result) + ")\n";
        return result;
    } else {
        cout << "Cleanup\n";
    }
    result = GetValue(dc890, 7, &value);
    if (result == 0) {
        cout << "Whoa, bad! This should be an error but isn't!\n";
        return -99;
    } else {
        char message[256];
        GetErrorString(message, 256);
        cout << string("(Expected) error: ") + message + " (" + to_string(result) + ")\n";
    }
    return 0;
}