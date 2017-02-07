#pragma once

#include <utility>
#include <vector>
#include <string>
using std::pair;
using std::make_pair;
using std::vector;
using std::string;

#ifdef TIMING
#define _CRT_SECURE_CPP_OVERLOAD_STANDARD_NAMES 1
#define _CRT_SECURE_CPP_OVERLOAD_STANDARD_NAMES_COUNT 1
#include <chrono>
#include <fstream>
using std::chrono::high_resolution_clock;
using std::chrono::duration_cast;
using std::chrono::duration;
using std::chrono::time_point;
using std::chrono::seconds;
using std::ofstream;
#endif

#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN
#define LIB_HANDLE HMODULE
#else
#define LIB_HANDLE void*
#endif
#include "ftd2xx.h"
#ifdef min
#undef min
#undef max
#endif
#ifndef LTC_CONTROLLER_COMM_API
#define LTC_CONTROLLER_COMM_API
#endif
#include "ltc_controller_comm.h"
#include "error.hpp"
#include "controller.hpp"

namespace linear {

class FtdiError : public HardwareError {
public:
    FtdiError(const string& message, int error_code) : HardwareError(message, error_code) { }
    string FullMessage() override {
        if (error_code < BAD_NEGATIVE) {
            error_code = BAD_NEGATIVE;
        } else if (error_code > BAD_TOO_LARGE) {
            error_code = BAD_TOO_LARGE;
        }
        return (string(what()) + " (FTDI error code: " + strings[error_code + 1] + ")");
    }
#define ENUM_DECLARATION                                                   \
        ENUM_START                                                         \
        ENUM(BAD_NEGATIVE,                -1),                             \
        ENUM(OK,                          FT_OK),                          \
        ENUM(INVALID_HANDLE,              FT_INVALID_HANDLE),              \
        ENUM(DEVICE_NOT_FOUND,            FT_DEVICE_NOT_FOUND),            \
        ENUM(DEVICE_NOT_OPENED,           FT_DEVICE_NOT_OPENED),           \
        ENUM(IO_ERROR,                    FT_IO_ERROR),                    \
        ENUM(INSUFFICIENT_RESOURCES,      FT_INSUFFICIENT_RESOURCES),      \
        ENUM(INVALID_PARAMETER,           FT_INVALID_PARAMETER),           \
        ENUM(INVALID_BAUD_RATE,           FT_INVALID_BAUD_RATE),           \
        ENUM(DEVICE_NOT_OPENED_FOR_ERASE, FT_DEVICE_NOT_OPENED_FOR_ERASE), \
        ENUM(DEVICE_NOT_OPENED_FOR_WRITE, FT_DEVICE_NOT_OPENED_FOR_WRITE), \
        ENUM(FAILED_TO_WRITE_DEVICE,      FT_FAILED_TO_WRITE_DEVICE),      \
        ENUM(EEPROM_READ_FAILED,          FT_EEPROM_READ_FAILED),          \
        ENUM(EEPROM_WRITE_FAILED,         FT_EEPROM_WRITE_FAILED),         \
        ENUM(EEPROM_ERASE_FAILED,         FT_EEPROM_ERASE_FAILED),         \
        ENUM(EEPROM_NOT_PRESENT,          FT_EEPROM_NOT_PRESENT),          \
        ENUM(EEPROM_NOT_PROGRAMMED,       FT_EEPROM_NOT_PROGRAMMED),       \
        ENUM(INVALID_ARGS,                FT_INVALID_ARGS),                \
        ENUM(NOT_SUPPORTED,               FT_NOT_SUPPORTED),               \
        ENUM(OTHER_ERROR,                 FT_OTHER_ERROR),                 \
        ENUM(DEVICE_LIST_NOT_READY,       FT_DEVICE_LIST_NOT_READY),       \
        ENUM(DLL_NOT_LOADED,              FT_DEVICE_LIST_NOT_READY + 1),   \
        ENUM(SLAVE_DID_NOT_ACK,           FT_DEVICE_LIST_NOT_READY + 2),   \
        ENUM(BAD_TOO_LARGE,               FT_DEVICE_LIST_NOT_READY + 3),   \
        ENUM_END
#define ENUM_START enum {
#define ENUM(name, value) name = value
#define ENUM_END };
    ENUM_DECLARATION;
private:
    static const int NUM_ERRORS = BAD_TOO_LARGE + 2; // (+2 is for BAD_NEGATIVE and OK)
    static const string strings[NUM_ERRORS];
};

class Ftdi {

#ifdef TIMING
    mutable ofstream timing_file { "linear_lab_tools_timing_file.txt" };
    time_point<high_resolution_clock> start_time = high_resolution_clock::now();
    double get_elapsed_seconds() const {
        auto end_time = high_resolution_clock::now();
        auto elapsed = end_time - start_time;
        return duration_cast<duration<double>>(elapsed).count();
    }
    string make_string(DWORD value) const {
        return std::to_string(value);
    }
    string make_string(UCHAR value) const {
        return std::to_string(value);
    }
    string make_string(USHORT value) const {
        return std::to_string(value);
    }
    string make_string(void* value) const {
        auto data = reinterpret_cast<uint8_t*>(value);
        char buffer[16];
        _snprintf(buffer, _TRUNCATE, "[%02X, %02X, ...]", data[0], data[1]);
        return string(buffer);
    }
    template <typename T, typename U, typename V, typename W>
    void write_timing(const char* function_name, T arg_t, U arg_u, V arg_v, W arg_w) const {
        auto time = get_elapsed_seconds();
        char buffer[1024];

        _snprintf(buffer, _TRUNCATE, "Called LT_%s(%s, %s, %s, %s) at %13.6f seconds\n", function_name,
                  make_string(arg_t).c_str(), make_string(arg_u).c_str(),
                  make_string(arg_v).c_str(), make_string(arg_w).c_str(), time);
        timing_file.write(buffer, strlen(buffer));
    }
    template <typename T, typename U, typename V>
    void write_timing(const char* function_name, T arg_t, U arg_u, V arg_v) const {
        auto time = get_elapsed_seconds();
        char buffer[1024];

        _snprintf(buffer, _TRUNCATE, "Called LT_%s(%s, %s, %s) at %13.6f seconds\n", function_name,
                  make_string(arg_t).c_str(), make_string(arg_u).c_str(),
                  make_string(arg_v).c_str(), time);
        timing_file.write(buffer, strlen(buffer));
    }
    template <typename T, typename U>
    void write_timing(const char* function_name, T arg_t, U arg_u) const {
        auto time = get_elapsed_seconds();
        char buffer[1024];

        _snprintf(buffer, _TRUNCATE, "Called LT_%s(%s, %s) at %13.6f seconds\n", function_name,
                  make_string(arg_t).c_str(), make_string(arg_u).c_str(), time);
        timing_file.write(buffer, strlen(buffer));
    }
    template <typename T>
    void write_timing(const char* function_name, T arg_t) const {
        auto time = get_elapsed_seconds();
        char buffer[1024];

        _snprintf(buffer, _TRUNCATE, "Called LT_%s(%s) at %13.6f seconds\n", function_name,
                  make_string(arg_t).c_str(), time);
        timing_file.write(buffer, strlen(buffer));
    }
    void write_timing(const char* function_name) const {
        auto time = get_elapsed_seconds();
        char buffer[1024];

        _snprintf(buffer, _TRUNCATE, "Called LT_%s at %13.6f seconds\n", function_name, time);
        timing_file.write(buffer, strlen(buffer));
    }
#endif

public:
    Ftdi() { LoadDll(); };
    ~Ftdi() { UnloadDll(); }
    Ftdi(const Ftdi&) = delete;
    Ftdi(Ftdi&&) = delete;
    Ftdi& operator=(const Ftdi) = delete;

    static const int EEPROM_ID_STRING_SIZE = 50;

    int GetNumControllers(int search_type, int max_controllers) const;
    vector<LccControllerInfo> ListControllers(int search_type, int max_controllers) const;
    void LoadDll();
    void UnloadDll();

    void Close(FT_HANDLE handle) const {
#ifdef TIMING
        write_timing("Close");
#endif
        // don't throw errors on close (it ends up in destructors)
        if (close != nullptr) {
            close(handle);
        }
    }

    void OpenByIndex(WORD device_index, FT_HANDLE* handle) const {
#ifdef TIMING
        write_timing("Open", device_index);
#endif
        check_library(open);
        check(open(device_index, handle), "Error opening device by index");
    }

    void OpenBySerialNumber(const char* serial_number, FT_HANDLE* handle) const {
        // function needs a void* but it doesn't change the memory so const cast is safe.
        auto casted_serial_number = const_cast<char*>(serial_number);
#ifdef TIMING
        write_timing("OpenEx", casted_serial_number);
#endif
        check_library(open_ex);
        check(open_ex(casted_serial_number, FT_OPEN_BY_SERIAL_NUMBER, handle),
              "Error opening device by serial number");
    }

    void GetDriverVersion(FT_HANDLE handle, LPDWORD driver_version) const {
#ifdef TIMING
        write_timing("GetDriverVersion");
#endif
        check_library(get_driver_version);
        check_close(handle, get_driver_version(handle, driver_version),
                    "Error getting driver version");
    }

    void GetLibraryVersion(LPDWORD library_version) const {
#ifdef TIMING
        write_timing("GetLibraryVersion");
#endif
        check_library(get_library_version);
        check(get_library_version(library_version), "Error getting library version");
    }

    void SetTimeouts(FT_HANDLE handle, ULONG read_timeout, ULONG write_timeout) const {
#ifdef TIMING
        write_timing("SetTimeouts", read_timeout, write_timeout);
#endif
        check_library(set_timeouts);
        check_close(handle, set_timeouts(handle, read_timeout, write_timeout),
                    "Error setting timeouts");
    }

    void SetUSBParameters(FT_HANDLE handle, ULONG in_transfer_size,
                          ULONG out_transfer_size) const {
#ifdef TIMING
        write_timing("SetUSBParameters", in_transfer_size, out_transfer_size);
#endif
        check_library(set_usb_parameters);
        check_close(handle, set_usb_parameters(handle, in_transfer_size, out_transfer_size),
                    "Error setting USB parameters");
    }
    DWORD Write(FT_HANDLE handle, const BYTE* data, DWORD data_length) const {
        // function needs a void* but it doesn't change the memory so const cast is safe.
        auto casted_data = const_cast<BYTE*>(data);
#ifdef TIMING
        write_timing("Write", casted_data, data_length);
#endif
        check_library(write);
        DWORD num_written;
        check_close(handle, write(handle, casted_data, data_length, &num_written),
                    "Error writing to device");
        return num_written;
    }
    DWORD Write(FT_HANDLE handle, const char* data, DWORD data_length) const {
        // function needs a void* but it doesn't change the memory so const cast is safe.
        auto casted_data = const_cast<char*>(data);
#ifdef TIMING
        write_timing("Write", casted_data, data_length);
#endif
        check_library(write);
        DWORD num_written;
        check_close(handle, write(handle, casted_data, data_length, &num_written),
                    "Error writing to device");
        return num_written;
    }
    DWORD Read(FT_HANDLE handle, BYTE* buffer, DWORD buffer_length) const {
#ifdef TIMING
        write_timing("Read", buffer_length);
#endif
        check_library(read);
        DWORD num_read;
        check_close(handle, read(handle, buffer, buffer_length, &num_read),
                    "Error reading from device");
        return num_read;
    }
    DWORD Read(FT_HANDLE handle, char* buffer, DWORD buffer_length) const {
#ifdef TIMING
        write_timing("Read", buffer_length);
#endif
        check_library(read);
        DWORD num_read;
        check_close(handle, read(handle, buffer, buffer_length, &num_read),
                    "Error reading from device");
        return num_read;
    }
    void Purge(FT_HANDLE handle, ULONG mask) const {
#ifdef TIMING
        write_timing("Purge");
#endif
        check_library(purge);
        check_close(handle, purge(handle, mask), "Error purging device IO");
    }
    void SetBitMode(FT_HANDLE handle, BYTE mask, BYTE enable) const {
#ifdef TIMING
        write_timing("SetBitMode", mask, enable);
#endif
        check_library(set_bit_mode);
        check_close(handle, set_bit_mode(handle, mask, enable), "Error setting bit mode");
    }
    void SetLatencyTimer(FT_HANDLE handle, BYTE latency) const {
#ifdef TIMING
        write_timing("SetLatencyTimer", latency);
#endif
        check_library(set_latency_timer);
        check_close(handle, set_latency_timer(handle, latency), "Error setting latency timer");
    }
    void SetFlowControl(FT_HANDLE handle, USHORT flow_control, BYTE xon, BYTE xoff) const {
#ifdef TIMING
        write_timing("SetFlowControl", flow_control, xon, xoff);
#endif
        check_library(set_flow_control);
        check_close(handle, set_flow_control(handle, flow_control, xon, xoff),
                    "Error setting flow control");
    }
    void GetDeviceInfo(FT_HANDLE handle, FT_DEVICE* device_type, LPDWORD id,
                       PCHAR serial_number, PCHAR description) const {
#ifdef TIMING
        write_timing("GetDeviceInfo");
#endif
        check_library(get_device_info);
        check_close(handle, get_device_info(handle, device_type, id, serial_number,
                                            description, nullptr), "Error getting device info");
    }
    void GetStatus(FT_HANDLE handle, LPDWORD num_receive_bytes,
                   LPDWORD num_send_bytes, LPDWORD event_dword) const {
#ifdef TIMING
        write_timing("GetStatus");
#endif
        check_library(get_status);
        check_close(handle, get_status(handle, num_receive_bytes, num_send_bytes, event_dword),
                    "Error getting device status");
    }
    void EnableEventChar(FT_HANDLE handle, bool enable = true) const {
        const UCHAR event_char = '\n';
        const UCHAR error_char = '\0';
        const UCHAR error_enable = 0;
        UCHAR event_enable = enable ? 1 : 0;
#ifdef TIMING
        write_timing("SetChars", event_char, event_enable, error_char, error_enable);
#endif
        check_library(set_chars);
        check_close(handle, set_chars(handle, event_char, event_enable, error_char, error_enable),
                    "Error setting event char");
    }
    void DisableEventChar(FT_HANDLE handle) const {
        check_library(set_chars);
        EnableEventChar(handle, false);
    }
private:

    void check(FT_STATUS result, const string& message) const {
        if (result != FtdiError::OK) {
            throw FtdiError(message, result);
        }
    }

    void check_close(FT_HANDLE handle, FT_STATUS result, const string& message) const {
        if (result != FtdiError::OK) {
            Close(handle);
            throw FtdiError(message, result);
        }
    }

    template <typename FuncPtr>
    void check_library(FuncPtr function) const {
        if (function == nullptr) {
            throw logic_error("FTDI DLL was not loaded.");
        }
    }

    void CreateDeviceInfoList(LPDWORD num_devices) const {
        check_library(create_device_info_list);
        check(create_device_info_list(num_devices), "Error creating device info list");
    }
    void GetDeviceInfoList(FT_DEVICE_LIST_INFO_NODE* device_list, LPDWORD num_devices) const {
        check_library(get_device_info_list);
        check(get_device_info_list(device_list, num_devices),
              "Error getting device info list");
    }

    typedef FT_STATUS(WINAPI *CloseFunction)(FT_HANDLE);
    typedef FT_STATUS(WINAPI *CreateDeviceInfoListFunction)(LPDWORD);
    typedef FT_STATUS(WINAPI *GetDeviceInfoListFunction)(FT_DEVICE_LIST_INFO_NODE*, LPDWORD);
    typedef FT_STATUS(WINAPI *OpenFunction)(int, FT_HANDLE*);
    typedef FT_STATUS(WINAPI *OpenExFunction)(PVOID, DWORD, FT_HANDLE*);
    typedef FT_STATUS(WINAPI *GetDriverVersionFunction)(FT_HANDLE, LPDWORD);
    typedef FT_STATUS(WINAPI *GetLibraryVersionFunction)(LPDWORD);
    typedef FT_STATUS(WINAPI *SetTimeoutsFunction)(FT_HANDLE, ULONG, ULONG);
    typedef FT_STATUS(WINAPI *SetUSBParametersFunction)(FT_HANDLE, ULONG, ULONG);
    typedef FT_STATUS(WINAPI *WriteFunction)(FT_HANDLE, PVOID, DWORD, LPDWORD);
    typedef FT_STATUS(WINAPI *ReadFunction)(FT_HANDLE, PVOID, DWORD, LPDWORD);
    typedef FT_STATUS(WINAPI *PurgeFunction)(FT_HANDLE, ULONG);
    typedef FT_STATUS(WINAPI *SetBitModeFunction)(FT_HANDLE, UCHAR, UCHAR);
    typedef FT_STATUS(WINAPI *SetLatencyTimerFunction)(FT_HANDLE, UCHAR);
    typedef FT_STATUS(WINAPI *SetFlowControlFunction)(FT_HANDLE, USHORT, UCHAR, UCHAR);
    typedef FT_STATUS(WINAPI *GetDeviceInfoFunction)(FT_HANDLE, FT_DEVICE*, LPDWORD, PCHAR, PCHAR, LPVOID);
    typedef FT_STATUS(WINAPI *GetStatusFunction)(FT_HANDLE, DWORD*, DWORD*, DWORD*);
    typedef FT_STATUS(WINAPI *SetCharsFunction)(FT_HANDLE, UCHAR, UCHAR, UCHAR, UCHAR);

    CloseFunction                close                   = nullptr;
    CreateDeviceInfoListFunction create_device_info_list = nullptr;
    GetDeviceInfoListFunction    get_device_info_list    = nullptr;
    OpenFunction                 open                    = nullptr;
    OpenExFunction               open_ex                 = nullptr;
    GetDriverVersionFunction     get_driver_version      = nullptr;
    GetLibraryVersionFunction    get_library_version     = nullptr;
    SetTimeoutsFunction          set_timeouts            = nullptr;
    SetUSBParametersFunction     set_usb_parameters      = nullptr;
    WriteFunction                write                   = nullptr;
    ReadFunction                 read                    = nullptr;
    PurgeFunction                purge                   = nullptr;
    SetBitModeFunction           set_bit_mode            = nullptr;
    SetLatencyTimerFunction      set_latency_timer       = nullptr;
    SetFlowControlFunction       set_flow_control        = nullptr;
    GetDeviceInfoFunction        get_device_info         = nullptr;
    GetStatusFunction            get_status              = nullptr;
    SetCharsFunction             set_chars               = nullptr;
    LIB_HANDLE                   ftdi                    = nullptr;
};
}

