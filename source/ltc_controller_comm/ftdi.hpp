#pragma once

#include <utility>
#include <vector>
#include <string>
using std::pair;
using std::make_pair;
using std::vector;
using std::string;

#define WINDOWS_LEAN_AND_MEAN
#include <Windows.h>
#include "ftd2xx.h"
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
        ENUM(BAD_NEGATIVE,   -1),                                          \
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

#define CHECK_LIBRARY(function) if (function == nullptr) { throw logic_error("FTDI DLL was not loaded."); }
#define CHECK(result, message) if (result != FtdiError::OK) { throw FtdiError(message, result); }
#define CHECK_CLOSE(handle, result, message) if (result != FtdiError::OK) { Close(handle); throw FtdiError(message, result); }

        void Close(FT_HANDLE handle) const {
            // don't throw errors on close (it ends up in destructors)
            if (close != nullptr) {
                close(handle);
            }
        }
        void OpenByIndex(WORD device_index, FT_HANDLE* handle) const {
            CHECK_LIBRARY(open);
            CHECK(open(device_index, handle), "Error opening device by index");
        }
        void OpenBySerialNumber(const char* serial_number, FT_HANDLE* handle) const {
            CHECK_LIBRARY(open_ex);
            // function needs a void* but it doesn't change the memory so const cast is safe.
            CHECK(open_ex(const_cast<char*>(serial_number), FT_OPEN_BY_SERIAL_NUMBER, handle),
                "Error opening device by serial number");
        }
        void GetDriverVersion(FT_HANDLE handle, LPDWORD driver_version) const {
            CHECK_LIBRARY(get_driver_version);
            CHECK_CLOSE(handle, get_driver_version(handle, driver_version),
                "Error getting driver version");
        }
        void GetLibraryVersion(LPDWORD library_version) const {
            CHECK_LIBRARY(get_library_version);
            CHECK(get_library_version(library_version), "Error getting library version");
        }
        void SetTimeouts(FT_HANDLE handle, ULONG read_timeout, ULONG write_timeout) const {
            CHECK_LIBRARY(set_timeouts);
            CHECK_CLOSE(handle, set_timeouts(handle, read_timeout, write_timeout),
                "Error setting timeouts");
        }
        void SetUSBParameters(FT_HANDLE handle, ULONG in_transfer_size,
                ULONG out_transfer_size) const {
            CHECK_LIBRARY(set_usb_parameters);
            CHECK_CLOSE(handle, set_usb_parameters(handle, in_transfer_size, out_transfer_size),
                "Error setting USB parameters");
        }
        DWORD Write(FT_HANDLE handle, const BYTE* data, DWORD data_length) const {
            CHECK_LIBRARY(write);
            DWORD num_written;
            CHECK_CLOSE(handle, write(handle, const_cast<BYTE*>(data), data_length, &num_written),
                "Error writing to device");
            return num_written;
        }
        DWORD Write(FT_HANDLE handle, const char* data, DWORD data_length) const {
            CHECK_LIBRARY(write);
            DWORD num_written;
            CHECK_CLOSE(handle, write(handle, const_cast<char*>(data), data_length, &num_written),
                "Error writing to device");
            return num_written;
        }
        DWORD Read(FT_HANDLE handle, BYTE* buffer, DWORD buffer_length) const {
            CHECK_LIBRARY(read);
            DWORD num_read;
            CHECK_CLOSE(handle, read(handle, buffer, buffer_length, &num_read),
                "Error reading from device");
            return num_read;
        }
        DWORD Read(FT_HANDLE handle, char* buffer, DWORD buffer_length) const {
            CHECK_LIBRARY(read);
            DWORD num_read;
            CHECK_CLOSE(handle, read(handle, buffer, buffer_length, &num_read),
                "Error reading from device");
            return num_read;
        }
        void Purge(FT_HANDLE handle, ULONG mask) const {
            CHECK_LIBRARY(purge);
            CHECK_CLOSE(handle, purge(handle, mask), "Error purging device IO");
        }
        void SetBitMode(FT_HANDLE handle, BYTE mask, BYTE enable) const {
            CHECK_LIBRARY(set_bit_mode);
            CHECK_CLOSE(handle, set_bit_mode(handle, mask, enable), "Error setting bit mode");
        }
        void SetLatencyTimer(FT_HANDLE handle, BYTE latency) const {
            CHECK_LIBRARY(set_latency_timer);
            CHECK_CLOSE(handle, set_latency_timer(handle, latency), "Error setting latency timer");
        }
        void SetFlowControl(FT_HANDLE handle, USHORT flow_control, BYTE xon, BYTE xoff) const {
            CHECK_LIBRARY(set_flow_control);
            CHECK_CLOSE(handle, set_flow_control(handle, flow_control, xon, xoff), 
                "Error setting flow control");
        }
        void GetDeviceInfo(FT_HANDLE handle, FT_DEVICE* device_type, LPDWORD id,
                PCHAR serial_number, PCHAR description) const {
            CHECK_LIBRARY(get_device_info);
            CHECK_CLOSE(handle, get_device_info(handle, device_type, id, serial_number,
                description, nullptr), "Error getting device info");
        }
        void GetStatus(FT_HANDLE handle, LPDWORD num_receive_bytes,
                LPDWORD num_send_bytes, LPDWORD event_dword) const {
            CHECK_LIBRARY(get_status);
            CHECK_CLOSE(handle, get_status(handle, num_receive_bytes, num_send_bytes, event_dword),
                "Error getting device status");
        }
        void EnableEventChar(FT_HANDLE handle, bool enable = true) const {
            CHECK_LIBRARY(set_chars);
            CHECK_CLOSE(handle, set_chars(handle, '\n', enable ? 1 : 0, '\0', 0),
                "Error setting event char");
        }
        void DisableEventChar(FT_HANDLE handle) const {
            CHECK_LIBRARY(set_chars);
            CHECK_CLOSE(handle, set_chars(handle, '\n', 0, '\0', 0),
                "Error setting event char");
        }
    private:

        void CreateDeviceInfoList(LPDWORD num_devices) const {
            CHECK_LIBRARY(create_device_info_list);
            CHECK(create_device_info_list(num_devices), "Error creating device info list");
        }
        void GetDeviceInfoList(FT_DEVICE_LIST_INFO_NODE* device_list, LPDWORD num_devices) const {
            CHECK_LIBRARY(get_device_info_list);
            CHECK(get_device_info_list(device_list, num_devices),
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
        HMODULE                      ftdi                    = nullptr;
    };
}

