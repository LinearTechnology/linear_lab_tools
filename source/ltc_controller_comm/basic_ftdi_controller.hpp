#pragma once
#include <cstdint>
#include <string>
#include <vector>
#include "controller.hpp"
#include "ftdi.hpp"
#include "i_close.hpp"
#include "i_reset.hpp"

namespace linear {

using std::string;
using std::vector;

class BasicFtdiController : public IReset, public IClose {
    static const int DEFAULT_READ_TIMEOUT  = 100;
    static const int DEFAULT_WRITE_TIMEOUT = 50;

   public:
    BasicFtdiController(const Ftdi& ftdi, const LccControllerInfo& info)
            : ftdi(ftdi),
              description(info.description),
              serial_number(info.serial_number),
              index(info.id),
              type(Controller::Type(info.type)) {}
    virtual ~BasicFtdiController() { Close(); }

    Type GetType() override { return type; }

    string GetDescription() override { return description; }
    string GetSerialNumber() override { return serial_number; }

    void EepromReadString(char* buffer, int buffer_size) override;

    void Flush();
    void Reset() override;
    void Close() override;

   protected:
    int Write(const BYTE* data, DWORD data_length) {
        OpenIfNeeded();
        return ftdi.Write(handle, data, data_length);
    }
    int Write(const char* data, DWORD data_length) {
        OpenIfNeeded();
        return ftdi.Write(handle, data, data_length);
    }
    int Read(BYTE* buffer, DWORD buffer_length) {
        OpenIfNeeded();
        return ftdi.Read(handle, buffer, buffer_length);
    }
    int Read(char* buffer, DWORD buffer_length) {
        OpenIfNeeded();
        return ftdi.Read(handle, buffer, buffer_length);
    }
    void SetTimeouts(ULONG read_timeout  = DEFAULT_READ_TIMEOUT,
                     ULONG write_timeout = DEFAULT_WRITE_TIMEOUT) {
        OpenIfNeeded();
        ftdi.SetTimeouts(handle, read_timeout, write_timeout);
    }

   protected:
    Type type;
    friend class Controller;
    bool        OpenByIndex();
    void        OpenBySerialNumber();
    void        OpenIfNeeded();
    const Ftdi& ftdi;
    string      description;
    string      serial_number;
    int         index;
    FT_HANDLE   handle = nullptr;
};
}
