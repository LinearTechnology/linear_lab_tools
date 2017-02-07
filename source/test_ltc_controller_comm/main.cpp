#include <iostream>
#include "ltc_controller_comm.h"

using std::cout;

void print_error(LccHandle handle, int error_code) {
    if (handle == nullptr) {
        cout << "Error creating handle.\n";
        cout << "(" << error_code << ")\n";
        return;
    }
    const int buffer_size = 256;
    char buffer[buffer_size];
    LccGetErrorInfo(handle, buffer, buffer_size);
    cout << "Error: " << buffer << "\n";
    cout << "(" << error_code << ")\n";
}

#define HANDLE_RESULT(MACRO_handle, MACRO_result) if ((MACRO_result) != LCC_ERROR_OK) { print_error(MACRO_handle, MACRO_result); return MACRO_result; }

int main() {
    int num_controllers;
    auto result = LccGetNumControllers(LCC_TYPE_DC1371, 1, &num_controllers);
    if ((result != LCC_ERROR_OK) || (num_controllers == 0)) {
        cout << "No DC1371 detected\n";
        return -1;
    } else {
        cout << "Found a DC1371!\n";
    }
    LccControllerInfo info;
    LccHandle handle = nullptr;
    result = LccGetControllerList(LCC_TYPE_DC1371, &info, 1);
    HANDLE_RESULT(handle, result);
    cout << "Got Info: desc:" << info.description << " serial:" << info.serial_number << "\n";
    result = LccInitController(&handle, &info);
    HANDLE_RESULT(handle, result);
    cout << "Created handle\n";
    const int eeprom_buffer_size = 200;
    char eeprom_buffer[eeprom_buffer_size];
    LccEepromReadString(handle, eeprom_buffer, eeprom_buffer_size);
    cout << "ID string: " << eeprom_buffer << "\n";

    bool is_loaded;
    LccFpgaGetIsLoaded(handle, "s2175", &is_loaded);
    if (!is_loaded) {
        LccFpgaLoadFile(handle, "s2175");
    }
    
    LccCleanup(&handle);
}
