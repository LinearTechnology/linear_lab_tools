#pragma once
#include <cstdint>
#ifndef LTC_CONTROLLER_COMM_API
#define LTC_CONTROLLER_COMM_API
#endif
#include "ltc_controller_comm.h"
#include "utilities.hpp"
#include <functional>
#ifdef max
#undef max
#endif
#include <gsl>

using gsl::narrow;

namespace linear {

class Controller {
public :
    enum class Type {
        NONE       = LCC_TYPE_NONE,
        DC1371     = LCC_TYPE_DC1371,
        DC718      = LCC_TYPE_DC718,
        DC890      = LCC_TYPE_DC890,
        HIGH_SPEED = LCC_TYPE_HIGH_SPEED,
        SOC_KIT    = LCC_TYPE_SOC_KIT,
        UNKNOWN    = LCC_TYPE_UNKNOWN
    };

    struct ControllerHandle {
        int ftdi_indices[2];
        char dc1371_drive_letter;
    };
    virtual ~Controller() { }

    virtual Type GetType() = 0;
    virtual string GetDescription() = 0;
    virtual string GetSerialNumber() = 0;
    virtual void EepromReadString(char* buffer, int buffer_size) = 0;

    static LccControllerInfo MakeControllerInfo(Type type, const string& description,
                                                const string& serial_number, uint16_t index_0, uint16_t index_1 = 0) {
        LccControllerInfo info;
        info.type = narrow<int>(type);
        CopyToBuffer(info.description, sizeof(info.description), description);
        CopyToBuffer(info.serial_number, sizeof(info.serial_number), serial_number);
        info.id = (index_1 << 16) | index_0;
        return info;
    }

protected:
    template <typename R, typename T>
    static int DataRead(R& reader, bool swap_bytes, T* values, int num_values) {
        int num_read = reader.ReadBytes(reinterpret_cast<uint8_t*>(values), num_values * sizeof(T));
        if (swap_bytes) {
            SwapBytes(values, num_values);
        }
        return num_read;
    }

    template <typename W, typename T>
    static int DataWrite(W& writer, bool swap_bytes, T* values, int num_values) {
        if (swap_bytes) {
            SwapBytes(values, num_values);
        }
        int num_written = writer.WriteBytes(reinterpret_cast<uint8_t*>(values), num_values * sizeof(T));
        // need to swap back or else user will still have their array to use,
        // but the contents will be wrong
        if (swap_bytes) {
            SwapBytes(values, num_values);
        }
        return num_written;
    }
};
}
