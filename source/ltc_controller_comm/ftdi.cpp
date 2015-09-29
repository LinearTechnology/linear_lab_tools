#include <unordered_map>
#include "ftdi.hpp"
#include "dc718.hpp"

namespace linear {

    using std::unordered_map;

#undef ENUM_START
#define ENUM_START const string FtdiError::strings[NUM_ERRORS] = {
#undef ENUM
#define ENUM(name, value) #name
    ENUM_DECLARATION;

    const char* DC890_DESCRIPTION = "DC890 FastDAACS CNTLR";
    const char* DC718_DESCRIPTION = "USB SERIAL CONTROLLER";
    const char* DC590_DESCRIPTION = DC718_DESCRIPTION;

    int Ftdi::GetNumControllers(int search_type, int max_controllers) const {
        DWORD num_devices = 0;
        CreateDeviceInfoList(&num_devices);
        int num_controllers = 0;
        if (num_devices == 0) {
            return num_controllers;
        }

        auto ftdi_info_list = vector<FT_DEVICE_LIST_INFO_NODE>(num_devices);
        GetDeviceInfoList(ftdi_info_list.data(), &num_devices);

        for (WORD i = 0; i < num_devices; ++i) {
            auto ftdi_info = ftdi_info_list[i];
            if (ftdi_info.Type == FT_DEVICE_BM) {
                if ((search_type & LCC_TYPE_DC890) &&
                        ftdi_info.Description == string(DC890_DESCRIPTION)) {
                    ++num_controllers;
                } else if ((search_type & LCC_TYPE_DC718) && 
                        ftdi_info.Description == string(DC718_DESCRIPTION)) {
                    // DC718 and DC590 have same description, so need to open and query device
                    auto controller_info = 
                        Controller::MakeControllerInfo(Controller::Type::DC718, 
                        ftdi_info.Description, ftdi_info.SerialNumber, i);
                    Dc718 controller(*this, controller_info);
                    if (controller.VerifyId()) {
                        ++num_controllers;
                    }
                }
            } else if (ftdi_info.Type == FT_DEVICE_2232H && (search_type & LCC_TYPE_HIGH_SPEED)) {
                // The 2232H is actually two devices, we only count channel A
                auto serial_number = string(ftdi_info.SerialNumber);
                size_t last = serial_number.size() - 1;
                if (serial_number[last] == 'A') {
                    ++num_controllers;
                }
            }
            if (num_controllers >= max_controllers) {
                break;
            }
        }
        return num_controllers;
    }

    vector<LccControllerInfo> Ftdi::ListControllers(int search_type, int max_controllers) const {
        auto controller_info_list = vector<LccControllerInfo>();
        DWORD num_devices = 0;
        CreateDeviceInfoList(&num_devices);

        if (num_devices == 0) {
            return controller_info_list;
        }

        auto ftdi_info_list = vector<FT_DEVICE_LIST_INFO_NODE>(num_devices);
        GetDeviceInfoList(ftdi_info_list.data(), &num_devices);

        auto found_serial_numbers = unordered_map<string, size_t>();
        for (WORD i = 0; i < num_devices; ++i) {
            auto ftdi_info = ftdi_info_list[i];
            if (ftdi_info.Type == FT_DEVICE_BM) {
                if ((search_type & LCC_TYPE_DC890) &&
                        ftdi_info.Description == string(DC890_DESCRIPTION)) {
                    auto controller_info = Controller::MakeControllerInfo(Controller::Type::DC890,
                        ftdi_info.Description, ftdi_info.SerialNumber, i);
                    controller_info_list.push_back(controller_info);
                } else if ((search_type & LCC_TYPE_DC718) &&
                        ftdi_info.Description == string(DC718_DESCRIPTION)) {
                    // DC718 and DC590 have same description, so need to open and query device
                    auto controller_info =
                        Controller::MakeControllerInfo(Controller::Type::DC718,
                        ftdi_info.Description, ftdi_info.SerialNumber, i);
                    Dc718 controller(*this, controller_info);
                    if (controller.VerifyId()) {
                        controller_info_list.push_back(controller_info);
                    }
                }          
            } else if (ftdi_info.Type == FT_DEVICE_2232H && (search_type & LCC_TYPE_HIGH_SPEED)) {
                // The 2232H is actually two devices, so we need two indices to open it, they might
                // not be next to each other either.
                auto serial_number = string(ftdi_info.SerialNumber);
                size_t last = serial_number.size() - 1;
                bool is_a = serial_number[last] == 'A';
                serial_number = serial_number.substr(0, last);
                
                if (found_serial_numbers.count(serial_number) == 0) {
                    found_serial_numbers[serial_number] = controller_info_list.size();
                    auto description = string(ftdi_info.Description);
                    // the description gets a space and a letter, so take off two characters
                    description = description.substr(0, description.size() - 2);
                    auto controller_info =
                        Controller::MakeControllerInfo(Controller::Type::HIGH_SPEED, description,
                        serial_number, i, i);
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

    void Ftdi::LoadDll() {
#ifdef X64
        ftdi = LoadLibrary(L"ftd2xx64.dll");
#else
        ftdi = LoadLibrary(L"ftd2xx.dll");
#endif
        if (ftdi != nullptr) {
            close = reinterpret_cast<CloseFunction>(GetProcAddress(ftdi, "FT_Close"));

            create_device_info_list = reinterpret_cast<CreateDeviceInfoListFunction>(
                GetProcAddress(ftdi, "FT_CreateDeviceInfoList"));

            get_device_info_list = reinterpret_cast<GetDeviceInfoListFunction>(
                GetProcAddress(ftdi, "FT_GetDeviceInfoList"));

            open = reinterpret_cast<OpenFunction>(GetProcAddress(ftdi, "FT_Open"));

            open_ex = reinterpret_cast<OpenExFunction>(GetProcAddress(ftdi, "FT_OpenEx"));

            get_driver_version = reinterpret_cast<GetDriverVersionFunction>(
                GetProcAddress(ftdi, "FT_GetdllVersion"));

            get_library_version = reinterpret_cast<GetLibraryVersionFunction>
                (GetProcAddress(ftdi, "FT_GetLibraryVersion"));

            set_timeouts = reinterpret_cast<SetTimeoutsFunction>(
                GetProcAddress(ftdi, "FT_SetTimeouts"));

            set_usb_parameters = reinterpret_cast<SetUSBParametersFunction>(
                GetProcAddress(ftdi, "FT_SetUSBParameters"));

            write = reinterpret_cast<WriteFunction>(GetProcAddress(ftdi, "FT_Write"));

            read = reinterpret_cast<ReadFunction>(GetProcAddress(ftdi, "FT_Read"));

            purge = reinterpret_cast<PurgeFunction>(GetProcAddress(ftdi, "FT_Purge"));

            set_bit_mode = reinterpret_cast<SetBitModeFunction>(
                GetProcAddress(ftdi, "FT_SetBitMode"));

            set_latency_timer = reinterpret_cast<SetLatencyTimerFunction>(
                GetProcAddress(ftdi, "FT_SetLatencyTimer"));

            set_flow_control = reinterpret_cast<SetFlowControlFunction>(
                GetProcAddress(ftdi, "FT_SetFlowControl"));

            get_device_info = reinterpret_cast<GetDeviceInfoFunction>(
                GetProcAddress(ftdi, "FT_GetDeviceInfo"));

            get_status = reinterpret_cast<GetStatusFunction>(
                GetProcAddress(ftdi, "FT_GetStatus"));

            set_chars = reinterpret_cast<SetCharsFunction>(
                GetProcAddress(ftdi, "FT_SetChars"));
        }
    }

    void Ftdi::UnloadDll() {
        if (ftdi != nullptr) {
            FreeLibrary(ftdi);
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