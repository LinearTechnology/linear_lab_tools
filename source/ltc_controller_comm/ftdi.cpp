#include "ftdi.hpp"
#include <unordered_map>
#include "dc718.hpp"
#ifndef _WIN32
#include <dlfcn.h>
#endif

namespace linear {

using std::unordered_map;

#undef ENUM_START
#define ENUM_START const string FtdiError::strings[NUM_ERRORS] = {
#undef ENUM
#define ENUM(name, value) #name
ENUM_DECLARATION;

const char* DC890_DESCRIPTION       = "DC890 FastDAACS CNTLR";
const char* DC718_DC590_DESCRIPTION = "USB SERIAL CONTROLLER";

int Ftdi::GetNumControllers(int search_type, int max_controllers) const {
    DWORD num_devices = 0;
    CreateDeviceInfoList(&num_devices);
    int num_controllers = 0;
    if (num_devices == 0) { return num_controllers; }

    auto ftdi_info_list = vector<FT_DEVICE_LIST_INFO_NODE>(num_devices);
    GetDeviceInfoList(ftdi_info_list.data(), &num_devices);

    for (WORD i = 0; i < num_devices; ++i) {
        auto ftdi_info = ftdi_info_list[i];
        if (ftdi_info.Type == FT_DEVICE_BM) {
            if (ftdi_info.Type == FT_DEVICE_BM) {
                if (ftdi_info.Description == string(DC890_DESCRIPTION) &&
                    (search_type & LCC_TYPE_DC890)) {
                    ++num_devices;
                    break;
                }

                if (ftdi_info.Description == string(DC718_DC590_DESCRIPTION)) {
                    // to check between DC590 and DC718 we need to open the device, so we only do
                    // that if they are actually looking for one or the other
                    if (search_type & (LCC_TYPE_DC590 | LCC_TYPE_DC718)) {
                        auto type = GetBasicType(ftdi_info.SerialNumber);
                        // now we check if it matches the specific one they are interested in
                        if ((type == Controller::Type::DC590 && (search_type & LCC_TYPE_DC590)) ||
                            (type == Controller::Type::DC718 && (search_type & LCC_TYPE_DC718))) {
                            ++num_devices;
                            break;
                        }
                    }
                }
            }
        } else if (ftdi_info.Type == FT_DEVICE_2232H && (search_type & LCC_TYPE_HIGH_SPEED)) {
            // The 2232H is actually two devices, we only count channel A
            auto   serial_number = string(ftdi_info.SerialNumber);
            size_t last          = serial_number.size() - 1;
            if (serial_number[last] == 'A') { ++num_controllers; }
        }
        if (num_controllers >= max_controllers) { break; }
    }
    return num_controllers;
}

vector<LccControllerInfo> Ftdi::ListControllers(int search_type, int max_controllers) const {
    auto  controller_info_list = vector<LccControllerInfo>();
    DWORD num_devices          = 0;
    CreateDeviceInfoList(&num_devices);

    if (num_devices == 0) { return controller_info_list; }

    auto ftdi_info_list = vector<FT_DEVICE_LIST_INFO_NODE>(num_devices);
    GetDeviceInfoList(ftdi_info_list.data(), &num_devices);

    auto found_serial_numbers = unordered_map<string, size_t>();
    for (WORD i = 0; i < num_devices; ++i) {
        auto ftdi_info = ftdi_info_list[i];
        if (ftdi_info.Type == FT_DEVICE_BM) {
            if (ftdi_info.Description == string(DC890_DESCRIPTION) &&
                (search_type & LCC_TYPE_DC890)) {
                auto controller_info = Controller::MakeControllerInfo(
                        Controller::Type::DC890, ftdi_info.Description, ftdi_info.SerialNumber, i);
                controller_info_list.push_back(controller_info);
                break;
            }

            if (ftdi_info.Description == string(DC718_DC590_DESCRIPTION)) {
                // to check between DC590 and DC718 we need to open the device, so we only do that
                // if they are actually looking for one or the other
                if (search_type & (LCC_TYPE_DC590 | LCC_TYPE_DC718)) {
                    auto type = GetBasicType(ftdi_info.SerialNumber);
                    // now we check if it matches the specific one they are interested in
                    if ((type == Controller::Type::DC590 && (search_type & LCC_TYPE_DC590)) ||
                        (type == Controller::Type::DC718 && (search_type & LCC_TYPE_DC718))) {
                        auto controller_info = Controller::MakeControllerInfo(
                                type, ftdi_info.Description, ftdi_info.SerialNumber, i);
                        controller_info_list.push_back(controller_info);
                        break;
                    }
                }
            }
        } else if (ftdi_info.Type == FT_DEVICE_2232H && (search_type & LCC_TYPE_HIGH_SPEED)) {
            // The 2232H is actually two devices, so we need two indices to open it, they might
            // not be next to each other either.
            auto   serial_number = string(ftdi_info.SerialNumber);
            size_t last          = serial_number.size() - 1;
            bool   is_a          = serial_number[last] == 'A';
            serial_number        = serial_number.substr(0, last);

            if (found_serial_numbers.count(serial_number) == 0) {
                found_serial_numbers[serial_number] = controller_info_list.size();
                auto description                    = string(ftdi_info.Description);
                // the description gets a space and a letter, so take off two characters
                description          = description.substr(0, description.size() - 2);
                auto controller_info = Controller::MakeControllerInfo(
                        Controller::Type::HIGH_SPEED, description, serial_number, i, i);
                controller_info_list.push_back(controller_info);
            } else {
                auto controller_info = controller_info_list[found_serial_numbers[serial_number]];
                if (is_a) {
                    controller_info.id = (controller_info.id & 0xFFFF0000) | i;
                } else {
                    controller_info.id = (controller_info.id & 0x0000FFFF) | (i << 16);
                }
                controller_info_list[found_serial_numbers[serial_number]] = controller_info;
            }
        }
    }
    return (controller_info_list);
}

static const char* DC590_PREFIX = "USBSPI,PIC,";
static const char* DC718_PREFIX = "QUDATS,PIC,";
static const char* DC890_PREFIX = "FSDACS,PIC,";

Controller::Type Ftdi::GetBasicType(const string& serial_number) const {
    FT_HANDLE handle;
    OpenBySerialNumber(serial_number.c_str(), &handle);
    Write(handle, "i\n", 2);
    char buffer[Ftdi::EEPROM_ID_STRING_SIZE];
    auto num_read = Read(handle, buffer, Ftdi::EEPROM_ID_STRING_SIZE);
    Close(handle);
    if (num_read != Ftdi::EEPROM_ID_STRING_SIZE) {
        throw HardwareError("Not all EEPROM bytes received.");
    }

    if (CompareStart(buffer, DC590_PREFIX)) {
        return Controller::Type::DC590;
    } else if (CompareStart(buffer, DC718_PREFIX)) {
        return Controller::Type::DC718;
    } else if (CompareStart(buffer, DC890_PREFIX)) {
        return Controller::Type::DC890;
    }
    return Controller::Type::UNKNOWN;
}

void* LoadFunc(LIB_HANDLE ftdi, const char* name) {
#ifdef _WIN32
    return GetProcAddress(ftdi, name);
#else
    return dlsym(ftdi, name);
#endif
}

void Ftdi::LoadDll() {
#ifdef _WIN32
#ifdef X64
    ftdi = LoadLibraryW(L"ftd2xx64.dll");
#else
    ftdi = LoadLibraryW(L"ftd2xx.dll");
#endif
#else
#ifdef X64
    ftdi = dlopen("libftd2xx64.so", RTLD_NOW);
#else
    ftdi = dlopen("libftd2xx.so", RTLD_NOW);
#endif
#endif

    if (ftdi != nullptr) {
        close = reinterpret_cast<CloseFunction>(LoadFunc(ftdi, "FT_Close"));

        create_device_info_list = reinterpret_cast<CreateDeviceInfoListFunction>(
                LoadFunc(ftdi, "FT_CreateDeviceInfoList"));

        get_device_info_list =
                reinterpret_cast<GetDeviceInfoListFunction>(LoadFunc(ftdi, "FT_GetDeviceInfoList"));

        open = reinterpret_cast<OpenFunction>(LoadFunc(ftdi, "FT_Open"));

        open_ex = reinterpret_cast<OpenExFunction>(LoadFunc(ftdi, "FT_OpenEx"));

        get_driver_version =
                reinterpret_cast<GetDriverVersionFunction>(LoadFunc(ftdi, "FT_GetdllVersion"));

        get_library_version =
                reinterpret_cast<GetLibraryVersionFunction>(LoadFunc(ftdi, "FT_GetLibraryVersion"));

        set_timeouts = reinterpret_cast<SetTimeoutsFunction>(LoadFunc(ftdi, "FT_SetTimeouts"));

        set_usb_parameters =
                reinterpret_cast<SetUSBParametersFunction>(LoadFunc(ftdi, "FT_SetUSBParameters"));

        write = reinterpret_cast<WriteFunction>(LoadFunc(ftdi, "FT_Write"));

        read = reinterpret_cast<ReadFunction>(LoadFunc(ftdi, "FT_Read"));

        purge = reinterpret_cast<PurgeFunction>(LoadFunc(ftdi, "FT_Purge"));

        set_bit_mode = reinterpret_cast<SetBitModeFunction>(LoadFunc(ftdi, "FT_SetBitMode"));

        set_latency_timer =
                reinterpret_cast<SetLatencyTimerFunction>(LoadFunc(ftdi, "FT_SetLatencyTimer"));

        set_flow_control =
                reinterpret_cast<SetFlowControlFunction>(LoadFunc(ftdi, "FT_SetFlowControl"));

        get_device_info =
                reinterpret_cast<GetDeviceInfoFunction>(LoadFunc(ftdi, "FT_GetDeviceInfo"));

        get_status = reinterpret_cast<GetStatusFunction>(LoadFunc(ftdi, "FT_GetStatus"));

        set_chars = reinterpret_cast<SetCharsFunction>(LoadFunc(ftdi, "FT_SetChars"));
    }
}

void Ftdi::UnloadDll() {
    if (ftdi != nullptr) {
#ifdef _WIN32
        FreeLibrary(ftdi);
#else
        dlclose(ftdi);
#endif
    }

    ftdi                    = nullptr;
    close                   = nullptr;
    create_device_info_list = nullptr;
    get_device_info_list    = nullptr;
    open                    = nullptr;
    open_ex                 = nullptr;
    get_driver_version      = nullptr;
    get_library_version     = nullptr;
    set_timeouts            = nullptr;
    set_usb_parameters      = nullptr;
    write                   = nullptr;
    read                    = nullptr;
    purge                   = nullptr;
    set_bit_mode            = nullptr;
    set_latency_timer       = nullptr;
    set_flow_control        = nullptr;
    get_device_info         = nullptr;
    get_status              = nullptr;
    set_chars               = nullptr;
}
}
