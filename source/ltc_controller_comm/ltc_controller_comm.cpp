#define LTC_CONTROLLER_COMM_API __declspec(dllexport)
#include "ltc_controller_comm.h"
#include "high_speed.hpp"
#include "dc1371.hpp"
#include "dc718.hpp"
#include "dc890.hpp"
#include "error.hpp"
using namespace linear;

extern Ftdi ftdi;

struct Handle {
    string error_string;
    Controller* controller;
    Handle(Controller* controller) : controller(controller) { }
    ~Handle() { delete controller; }
    Handle(const Handle&) = delete;
    Handle(Handle&&) = delete;
    bool operator==(const Handle&) = delete;
};

#define C_MUST_NOT_BE_NULL(h) do {    \
    if ((h) == nullptr) {             \
        return LCC_ERROR_INVALID_ARG; \
    }                                 \
} while (0)

#define GET_STRING(h, es)                        \
string* es;                                      \
do {                                             \
    C_MUST_NOT_BE_NULL(h);                       \
    es = &static_cast<Handle*>(h)->error_string; \
} while (0)

#define GET(h, ctrl, type, es)                                             \
type* ctrl;                                                                \
string* es;                                                                \
do {                                                                       \
    C_MUST_NOT_BE_NULL(h);                                                 \
    es = &static_cast<Handle*>(h)->error_string;                           \
    ctrl = dynamic_cast<type*>(reinterpret_cast<Handle*>(h)->controller);  \
    if (ctrl == nullptr) {                                                 \
        *es = "This operation is not supported for this controller type."; \
        return LCC_ERROR_NOT_SUPPORTED;                                    \
    }                                                                      \
} while (0)

// note we are using a VS extension, __VA_ARGS__ you can pass in 0 arguments for ... (__VA_ARGS__)
#define CALL(ctrl, es, func, ...) \
    return ToErrorCode([&] { controller->func(__VA_ARGS__); }, *es);
// note we are using a VS extension, __VA_ARGS__ you can pass in 0 arguments for ... (__VA_ARGS__)
#define CALL_VAL(ctrl, es, val, func, ...) \
    return ToErrorCode([&] { return controller->func(__VA_ARGS__); }, *val, *es);

LTC_CONTROLLER_COMM_API int LccGetNumControllers(int controller_types, int max_controllers,
                                                 int* num_controllers) {
    try {
        if (controller_types & LCC_TYPE_DC1371) {
            *num_controllers = Dc1371::GetNumControllers(Min(max_controllers, Dc1371::MAX_CONTROLLERS));
        }
        if (*num_controllers < max_controllers) {
            *num_controllers += ftdi.GetNumControllers(controller_types, 
                max_controllers - *num_controllers);
        }
        return LCC_ERROR_OK;
    } catch (invalid_argument&) {
        return LCC_ERROR_INVALID_ARG;
    } catch (domain_error) {
        return LCC_ERROR_NOT_SUPPORTED;
    } catch (logic_error&) {
        return LCC_ERROR_LOGIC;
    } catch (HardwareError&) {
        return LCC_ERROR_HARDWARE;
    } catch (exception&) {
        return LCC_ERROR_UNKNOWN;
    } catch (...) {
        return LCC_ERROR_UNKNOWN;
    }
}

LTC_CONTROLLER_COMM_API int LccGetControllerList(int controller_types, 
        LccControllerInfo* controller_info_list, int num_controllers) {
    try {
        int index = 0;
        if (controller_types & LCC_TYPE_DC1371) {
            auto dc1371s = Dc1371::ListControllers(Min(num_controllers, Dc1371::MAX_CONTROLLERS));
            for (auto dc1371 : dc1371s) {
                controller_info_list[index] = dc1371;
                ++index;
                if (index == num_controllers) {
                    return LCC_ERROR_OK;
                }
            }
        }

        if (controller_types & ~LCC_TYPE_DC1371) {
            auto ftdis = ftdi.ListControllers(controller_types, num_controllers - index);
            for (auto ft_itr = ftdis.begin();
                index < num_controllers && ft_itr != ftdis.end(); ++ft_itr) {
                controller_info_list[index] = *ft_itr;
                ++index;
            }
        }
        return LCC_ERROR_OK;
    } catch (invalid_argument&) {
        return LCC_ERROR_INVALID_ARG;
    } catch (domain_error) {
        return LCC_ERROR_NOT_SUPPORTED;
    } catch (logic_error&) {
        return LCC_ERROR_LOGIC;
    } catch (HardwareError&) {
        return LCC_ERROR_HARDWARE;
    } catch (exception&) {
        return LCC_ERROR_UNKNOWN;
    } catch (...) {
        return LCC_ERROR_UNKNOWN;
    }
}

LTC_CONTROLLER_COMM_API int LccGetControllerInfoFromId(int controller_type, const char* id,
                                                       LccControllerInfo* controller_info) {
    switch (controller_type) {
        case LCC_TYPE_DC1371:
        {
            if (Dc1371::IsDc1371(id[0])) {
                *controller_info = Dc1371::MakeControllerInfo(id[0]);
                return LCC_ERROR_OK;
            } else {
                return LCC_ERROR_HARDWARE;
            }
        }
        case LCC_TYPE_DC718:
        case LCC_TYPE_DC890:
        case LCC_TYPE_HIGH_SPEED:
        {
            // we could make this more efficient in the future
            int num_controllers = 0;
            auto result = LccGetNumControllers(controller_type, 100, &num_controllers);
            if (result != LCC_ERROR_OK) {
                return result;
            }
            vector<LccControllerInfo> info_list(num_controllers);
            result = LccGetControllerList(controller_type, info_list.data(), info_list.size());
            if (result != LCC_ERROR_OK) {
                return result;
            }

            for (auto&& info: info_list) {
                if (strcmp(info.serial_number, id) == 0) {
                    *controller_info = info;
                    return LCC_ERROR_OK;
                }
            }

            return LCC_ERROR_HARDWARE;
        }
        default:
            return LCC_ERROR_INVALID_ARG;
    }
}

LTC_CONTROLLER_COMM_API int LccInitController(LccHandle* handle,
        LccControllerInfo* controller_info) {
    C_MUST_NOT_BE_NULL(handle);
    C_MUST_NOT_BE_NULL(controller_info);
    auto new_handle = new Handle(nullptr);
    switch (controller_info->type) {
    case LCC_TYPE_DC1371:
    {
        int code = ToErrorCode([&] { return new Dc1371(*controller_info); },
            new_handle->controller, new_handle->error_string);
        *handle = new_handle;
        return code;
    }
    case LCC_TYPE_HIGH_SPEED:
    {
        int code = ToErrorCode([&] { return new HighSpeed(ftdi, *controller_info); },
            new_handle->controller, new_handle->error_string);
        *handle = new_handle;
        return code;
    }
    case LCC_TYPE_DC718:
    {
        int code = ToErrorCode([&] { return new Dc718(ftdi, *controller_info); },
            new_handle->controller, new_handle->error_string);
        *handle = new_handle;
        return code;
    }
    case LCC_TYPE_DC890:
    {
        int code = ToErrorCode([&] {return new Dc890(ftdi, *controller_info); },
            new_handle->controller, new_handle->error_string);
        *handle = new_handle;
        return code;
    }
    default:
        new_handle->error_string = "Invalid device type in device info.";
        return LCC_ERROR_INVALID_ARG;
    }
}

LTC_CONTROLLER_COMM_API int LccCleanup(LccHandle* handle) {
    C_MUST_NOT_BE_NULL(handle);
    delete static_cast<Handle*>(*handle);
    *handle = nullptr;
    return LCC_ERROR_OK;
}

LTC_CONTROLLER_COMM_API int LccGetDescription(LccHandle handle, char* description_buffer,
        int description_buffer_size) {
    GET(handle, controller, Controller, error_string);
    string description;
    int code = ToErrorCode(
        [&] { return controller->GetDescription(); }, description, *error_string);
    if (code != LCC_ERROR_OK) { return code; }
    auto string_size = Narrow<int>(description.size() + 1);
    if (description_buffer_size < string_size || description_buffer == nullptr) {
        return string_size;
    } else {
        strcpy_s(description_buffer, description_buffer_size, description.c_str());
        description_buffer[string_size - 1] = '\0';
        return LCC_ERROR_OK;
    }
}

LTC_CONTROLLER_COMM_API int LccGetSerialNumber(LccHandle handle, char* serial_number_buffer,
        int serial_number_buffer_size) {
    GET(handle, controller, Controller, error_string);
    string serial_number;
    int code = ToErrorCode(
        [&] { return controller->GetSerialNumber(); }, serial_number, *error_string);
    if (code != LCC_ERROR_OK) { return code; }
    auto string_size = Narrow<int>(serial_number.size() + 1);
    if (serial_number_buffer_size < string_size || serial_number_buffer == nullptr) {
        return string_size;
    } else {
        strcpy_s(serial_number_buffer, serial_number_buffer_size, serial_number.c_str());
        serial_number_buffer[string_size - 1] = '\0';
        return LCC_ERROR_OK;
    }
}

LTC_CONTROLLER_COMM_API int LccHsPurgeIo(LccHandle handle) {
    GET(handle, controller, HighSpeed, error_string);
    CALL(controller, error_string, PurgeIo);
}

LTC_CONTROLLER_COMM_API int LccReset(LccHandle handle) {
    GET(handle, controller, IReset, error_string);
    CALL(controller, error_string, Reset);
}

LTC_CONTROLLER_COMM_API int LccClose(LccHandle handle) {
    GET(handle, controller, IClose, error_string);
    CALL(controller, error_string, Close);
}

LTC_CONTROLLER_COMM_API int LccGetErrorInfo(LccHandle handle, char* message_buffer,
        int buffer_size) {
    if (handle == nullptr) {
        string error_string = "LccHandle is null.";
        if (Narrow<int>(error_string.size()) > buffer_size) {
            return Narrow<int>(error_string.size());
        } else {
            strcpy_s(message_buffer, buffer_size, error_string.c_str());
        }
        return LCC_ERROR_INVALID_ARG;
    }
    GET_STRING(handle, error_string);
    if (Narrow<int>(error_string->size()) > buffer_size) {
        return Narrow<int>(error_string->size());
    } else {
        strcpy_s(message_buffer, buffer_size, error_string->c_str());
    }
    return LCC_ERROR_OK;
}

LTC_CONTROLLER_COMM_API int LccDataSetHighByteFirst(LccHandle handle) {
    GET(handle, controller, IDataEndian, error_string);
    CALL(controller, error_string, DataSetHighByteFirst);
}

LTC_CONTROLLER_COMM_API int LccDataSetLowByteFirst(LccHandle handle) {
    GET(handle, controller, IDataEndian, error_string);
    CALL(controller, error_string, DataSetLowByteFirst);
}

LTC_CONTROLLER_COMM_API int LccDataSetCharacteristics(LccHandle handle, bool is_multichannel,
        int sample_bytes, bool is_positive_clock) {
    GET(handle, controller, FtdiAdc, error_string);
    CALL(controller, error_string, DataSetCharacteristics, is_multichannel, sample_bytes,
        is_positive_clock);
}

LTC_CONTROLLER_COMM_API int LccDataSendBytes(LccHandle handle, uint8_t* values, int num_values,
        int* num_sent) {
    GET(handle, controller, IDataSend, error_string);
    CALL_VAL(controller, error_string, num_sent, DataSend, values, num_values);
}

LTC_CONTROLLER_COMM_API int LccDataReceiveBytes(LccHandle handle, uint8_t* values,
        int num_values, int* num_received) {
    GET(handle, controller, IDataReceive, error_string);
    CALL_VAL(controller, error_string, num_received, DataReceive, values, num_values);
}

LTC_CONTROLLER_COMM_API int LccDataSendUint16Values(LccHandle handle, uint16_t* values,
        int num_values, int* num_bytes_sent) {
    GET(handle, controller, IDataSend, error_string);
    CALL_VAL(controller, error_string, num_bytes_sent, DataSend, values, num_values);
}

LTC_CONTROLLER_COMM_API int LccDataReceiveUint16Values(LccHandle handle, uint16_t* values,
        int num_values, int* num_bytes_received) {
    GET(handle, controller, IDataReceive, error_string);
    CALL_VAL(controller, error_string, num_bytes_received, DataReceive, values, num_values);
}

LTC_CONTROLLER_COMM_API int LccDataSendUint32Values(LccHandle handle, uint32_t* values,
        int num_values, int* num_bytes_sent) {
    GET(handle, controller, IDataSend, error_string);
    CALL_VAL(controller, error_string, num_bytes_sent, DataSend, values, num_values);
}

LTC_CONTROLLER_COMM_API int LccDataReceiveUint32Values(LccHandle handle, uint32_t* values,
        int num_values, int* num_bytes_received) {
    GET(handle, controller, IDataReceive, error_string);
    CALL_VAL(controller, error_string, num_bytes_received, DataReceive, values, num_values);
}

LTC_CONTROLLER_COMM_API int LccDataStartCollect(LccHandle handle, int total_samples,
        int trigger) {
    GET(handle, controller, ICollect, error_string);
    CALL(controller, error_string, DataStartCollect, total_samples, ICollect::Trigger(trigger));
}
LTC_CONTROLLER_COMM_API int LccDataIsCollectDone(LccHandle handle, bool* is_done) {
    GET(handle, controller, ICollect, error_string);
    CALL_VAL(controller, error_string, is_done, DataIsCollectDone);
}
LTC_CONTROLLER_COMM_API int LccDataCancelCollect(LccHandle handle) {
    GET(handle, controller, ICollect, error_string);
    CALL(controller, error_string, DataCancelCollect);
}

LTC_CONTROLLER_COMM_API int LccSpiSendBytes(LccHandle handle, uint8_t* values,
        int num_values) {
    GET(handle, controller, ISpiSendOnly, error_string);
    CALL(controller, error_string, SpiSend, values, num_values);
}

LTC_CONTROLLER_COMM_API int LccSpiReceiveBytes(LccHandle handle, uint8_t* values,
        int num_values) {
    GET(handle, controller, ISpi, error_string);
    CALL(controller, error_string, SpiReceive, values, num_values);
}

LTC_CONTROLLER_COMM_API int LccSpiTransceiveBytes(LccHandle handle, uint8_t* send_values,
        uint8_t* receive_values, int num_values) {
    GET(handle, controller, ISpi, error_string);
    CALL(controller, error_string, SpiTransceive, send_values, receive_values, num_values);
}

LTC_CONTROLLER_COMM_API int LccSpiSendByteAtAddress(LccHandle handle, uint8_t address,
        uint8_t value) {
    GET(handle, controller, ISpiSendOnly, error_string);
    CALL(controller, error_string, SpiSendAtAddress, address, value);
}

LTC_CONTROLLER_COMM_API int LccSpiSendBytesAtAddress(LccHandle handle, uint8_t address,
        uint8_t* values, int num_values) {
    GET(handle, controller, ISpiSendOnly, error_string);
    CALL(controller, error_string, SpiSendAtAddress, address, values, num_values);
}

LTC_CONTROLLER_COMM_API int LccSpiReceiveByteAtAddress(LccHandle handle, uint8_t address,
        uint8_t* value) {
    GET(handle, controller, ISpi, error_string);
    CALL_VAL(controller, error_string, value, SpiReceiveAtAddress, address);
}

LTC_CONTROLLER_COMM_API int LccSpiReceiveBytesAtAddress(LccHandle handle, uint8_t address,
        uint8_t* values, int num_values) {
    GET(handle, controller, ISpi, error_string);
    CALL(controller, error_string, SpiReceiveAtAddress, address, values, num_values);
}

LTC_CONTROLLER_COMM_API int LccSpiSetCsState(LccHandle handle, int chip_select_state) {
    GET(handle, controller, ISpiSendOnly, error_string);
    CALL(controller, error_string, SpiSetCsState, ISpiSendOnly::SpiCsState(chip_select_state));
}

LTC_CONTROLLER_COMM_API int LccSpiSendNoChipSelect(LccHandle handle, uint8_t* values,
        int num_values) {
    GET(handle, controller, ISpiSendOnly, error_string);
    CALL(controller, error_string, SpiSendNoChipSelect, values, num_values);
}

LTC_CONTROLLER_COMM_API int LccSpiReceiveNoChipSelect(LccHandle handle, uint8_t* values,
        int num_values) {
    GET(handle, controller, ISpi, error_string);
    CALL(controller, error_string, SpiReceiveNoChipSelect, values, num_values);
}

LTC_CONTROLLER_COMM_API int LccSpiTransceiveNoChipSelect(LccHandle handle,
        uint8_t * send_values, uint8_t* receive_values, int num_values) {
    GET(handle, controller, ISpi, error_string);
    CALL(controller, error_string, SpiTransceiveNoChipSelect, send_values,
        receive_values, num_values);
}

LTC_CONTROLLER_COMM_API int LccFpgaGetIsLoaded(LccHandle handle, const char* fpga_filename,
        bool* is_loaded) {
    GET(handle, controller, IFpgaLoad, error_string);
    CALL_VAL(controller, error_string, is_loaded, FpgaGetIsLoaded, fpga_filename);
}

LTC_CONTROLLER_COMM_API int LccFpgaLoadFile(LccHandle handle, const char* fpga_filename) {
    GET(handle, controller, IFpgaLoad, error_string);
    CALL(controller, error_string, FpgaLoadFile, fpga_filename);
}

LTC_CONTROLLER_COMM_API int LccFpgaLoadFileChunked(LccHandle handle, const char* fpga_filename,
        int* progress) {
    GET(handle, controller, IFpgaLoad, error_string);
    CALL_VAL(controller, error_string, progress, FpgaLoadFileChunked, fpga_filename);
}

LTC_CONTROLLER_COMM_API int LccFpgaCancelLoad(LccHandle handle) {
    GET(handle, controller, IFpgaLoad, error_string);
    CALL(controller, error_string, FpgaCancelLoad);
}

LTC_CONTROLLER_COMM_API int LccEepromReadString(LccHandle handle, char* buffer,
        int buffer_size) {
    GET(handle, controller, Controller, error_string);
    CALL(controller, error_string, EepromReadString, buffer, buffer_size);
}

LTC_CONTROLLER_COMM_API int LccHsSetBitMode(LccHandle handle, int mode) {
    GET(handle, controller, HighSpeed, error_string);
    CALL(controller, error_string, SetBitMode, HighSpeed::BitMode(mode));
}

LTC_CONTROLLER_COMM_API int LccHsFpgaToggleReset(LccHandle handle) {
    GET(handle, controller, HighSpeed, error_string);
    CALL(controller, error_string, FpgaToggleReset);
}

LTC_CONTROLLER_COMM_API int LccHsFpgaWriteAddress(LccHandle handle, uint8_t address) {
    GET(handle, controller, HighSpeed, error_string);
    CALL(controller, error_string, FpgaWriteAddress, address);
}

LTC_CONTROLLER_COMM_API int LccHsFpgaWriteData(LccHandle handle, uint8_t value) {
    GET(handle, controller, HighSpeed, error_string);
    CALL(controller, error_string, FpgaWriteData, value);
}

LTC_CONTROLLER_COMM_API int LccHsFpgaReadData(LccHandle handle, uint8_t* value) {
    GET(handle, controller, HighSpeed, error_string);
    CALL_VAL(controller, error_string, value, FpgaReadData);
}

LTC_CONTROLLER_COMM_API int LccHsFpgaWriteDataAtAddress(LccHandle handle, uint8_t address,
        uint8_t value) {
    GET(handle, controller, HighSpeed, error_string);
    CALL(controller, error_string, FpgaWriteDataAtAddress, address, value);
}

LTC_CONTROLLER_COMM_API int LccHsFpgaReadDataAtAddress(LccHandle handle, uint8_t address,
        uint8_t* value) {
    GET(handle, controller, HighSpeed, error_string);
    CALL_VAL(controller, error_string, value, FpgaReadDataAtAddress, address);
}

LTC_CONTROLLER_COMM_API int LccHsGpioWriteHighByte(LccHandle handle, uint8_t value) {
    GET(handle, controller, HighSpeed, error_string);
    CALL(controller, error_string, GpioWriteHighByte, value);
}

LTC_CONTROLLER_COMM_API int LccHsGpioReadHighByte(LccHandle handle, uint8_t* value) {
    GET(handle, controller, HighSpeed, error_string);
    CALL_VAL(controller, error_string, value, GpioReadHighByte);
}

LTC_CONTROLLER_COMM_API int LccHsGpioWriteLowByte(LccHandle handle, uint8_t value) {
    GET(handle, controller, HighSpeed, error_string);
    CALL(controller, error_string, GpioWriteLowByte, value);
}

LTC_CONTROLLER_COMM_API int LccHsGpioReadLowByte(LccHandle handle, uint8_t* value) {
    GET(handle, controller, HighSpeed, error_string);
    CALL_VAL(controller, error_string, value, GpioReadLowByte);
}

LTC_CONTROLLER_COMM_API int LccHsFpgaEepromSetBitBangRegister(LccHandle handle,
        uint8_t register_address) {
    GET(handle, controller, HighSpeed, error_string);
    CALL(controller, error_string, FpgaEepromSetBitBangRegister, register_address);
}

LTC_CONTROLLER_COMM_API int Lcc1371SetGenericConfig(LccHandle handle, uint32_t generic_config) {
    GET(handle, controller, Dc1371, error_string);
    CALL(controller, error_string, SetGenericConfig, generic_config);
}
LTC_CONTROLLER_COMM_API int Lcc1371SetDemoConfig(LccHandle handle, uint32_t demo_config) {
    GET(handle, controller, Dc1371, error_string);
    CALL(controller, error_string, SetDemoConfig, demo_config);
}

LTC_CONTROLLER_COMM_API int Lcc1371SpiChooseChipSelect(LccHandle handle, int new_chip_select) {
    GET(handle, controller, Dc1371, error_string);
    CALL(controller, error_string, SpiChooseChipSelect, Dc1371::ChipSelect(new_chip_select));
}

LTC_CONTROLLER_COMM_API int Lcc890GpioSetByte(LccHandle handle, uint8_t byte) {
    GET(handle, controller, Dc890, error_string);
    CALL(controller, error_string, GpioSetByte, byte);
}

LTC_CONTROLLER_COMM_API int Lcc890GpioSpiSetBits(LccHandle handle, int cs_bit,
    int sck_bit, int sdi_bit) {
    GET(handle, controller, Dc890, error_string);
    CALL(controller, error_string, GpioSpiSetBits, cs_bit, sck_bit, sdi_bit);
}

LTC_CONTROLLER_COMM_API int Lcc890Flush(LccHandle handle) {
    GET(handle, controller, Dc890, error_string);
    CALL(controller, error_string, Flush);
}