// This is the main DLL file.

#include "LtcControllerComm.h"
#include "..\ltc_controller_comm\high_speed.hpp"
#include "..\ltc_controller_comm\dc1371.hpp"
#include "..\ltc_controller_comm\dc718.hpp"
#include "..\ltc_controller_comm\dc890.hpp"

using linear::Dc1371;
using linear::Dc1371Error;
using linear::Dc718;
using linear::Dc890;
using linear::HighSpeed;
using linear::Ftdi;
using linear::FtdiError;

extern Ftdi ftdi;

namespace LtcControllerComm {

#define TRY(code)                                                               \
    try {                                                                       \
        code                                                                    \
    } catch (invalid_argument& err) {                                           \
        throw gcnew ArgumentException(marshal_as<String^>(err.what()));         \
    } catch (domain_error& err) {                                               \
        throw gcnew InvalidOperationException(marshal_as<String^>(err.what())); \
    } catch (logic_error& err) {                                                \
        throw gcnew LogicException(marshal_as<String^>(err.what()));            \
    } catch (linear::HardwareError & err) {                                     \
        throw gcnew HardwareException(marshal_as<String^>(err.what()));         \
    } catch (exception& err) {                                                  \
        throw gcnew Exception(marshal_as<String^>(err.what()));                 \
    } catch (...) {                                                             \
        throw gcnew Exception("An unknown error occurred.");                    \
    }

#define GET(ctrl, type)                                                   \
type* ctrl;                                                               \
do {                                                                      \
    ctrl = dynamic_cast<type*>(nativeController);                         \
    if (ctrl == nullptr) {                                                \
        throw gcnew NotSupportedException(                                \
            "This operation is not supported for this controller type");  \
    }                                                                     \
} while (0)

#undef MUST_NOT_BE_NULL

#define QUOTE(x) #x
#define MUST_NOT_BE_NULL(pointer)                                          \
if((pointer) == nullptr) {                                                 \
    throw gcnew ArgumentNullException(QUOTE(pointer) " must not be null"); \
}
#define MUST_BE_GREATER(a, b)                                                  \
if ((a) <= (b)) {                                                              \
    throw gcnew ArgumentException(QUOTE(a) " must be greater than " QUOTE(b)); \
}
#define MUST_NOT_BE_GREATER(a, b)                                                  \
if ((a) > (b)) {                                                                   \
    throw gcnew ArgumentException(QUOTE(a) " must not be greater than " QUOTE(b)); \
}
#define MUST_BE_LESS(a, b)                                                  \
if ((a) >= (b)) {                                                           \
    throw gcnew ArgumentException(QUOTE(a) " must be less than " QUOTE(b)); \
}
#define MUST_NOT_BE_LESS(a, b)                                                  \
if ((a) < (b)) {                                                                \
    throw gcnew ArgumentException(QUOTE(a) " must not be less than " QUOTE(b)); \
}
    array<Controller::Info>^ Controller::GetControllerList(Type acceptableTypes) {
        TRY({
            int acceptable_types = static_cast<int>(acceptableTypes);
            vector<LccControllerInfo> dc1371_info;
            vector<LccControllerInfo> ftdi_info;
            if ((acceptable_types & LCC_TYPE_DC1371) != 0) {
                dc1371_info = Dc1371::ListControllers(Dc1371::MAX_CONTROLLERS);
            }
            if ((acceptable_types & ~LCC_TYPE_DC1371) != 0) {
                ftdi_info = ftdi.ListControllers(acceptable_types, 20);
            }
            auto controllers = gcnew array<Controller::Info>(dc1371_info.size() + ftdi_info.size());
            int index = 0;
            for (auto& info : dc1371_info) {
                controllers[index] = Controller::Info(
                    static_cast<Controller::Type>(info.type),
                    marshal_as<String^>(info.description),
                    marshal_as<String^>(info.serial_number),
                    info.id);
                ++index;
            }
            for (auto& info : ftdi_info) {
                controllers[index] = Controller::Info(
                    static_cast<Controller::Type>(info.type),
                    marshal_as<String^>(info.description),
                    marshal_as<String^>(info.serial_number),
                    info.id);
                ++index;
            }
            return controllers;
        });
    }

    Controller::Controller(Info controllerInfo) {
        TRY({
            LccControllerInfo info;
            info.type = static_cast<int>(controllerInfo.type);
            memcpy_s(info.description, LCC_MAX_DESCRIPTION_SIZE,
                     marshal_as<std::string>(controllerInfo.description).c_str(),
                     controllerInfo.description->Length);
            memcpy_s(info.serial_number, LCC_MAX_SERIAL_NUMBER_SIZE,
                     marshal_as<std::string>(controllerInfo.serial_number).c_str(),
                     controllerInfo.serial_number->Length);
            info.id = controllerInfo.id;
            switch (controllerInfo.type) {
                case Controller::Type::Dc1371:
                    nativeController = new linear::Dc1371(info);
                    return;
                case Controller::Type::Dc718:
                    nativeController = new linear::Dc718(ftdi, info);
                    return;
                case Controller::Type::Dc890:
                    nativeController = new linear::Dc890(ftdi, info);
                case Controller::Type::HighSpeed:
                    nativeController = new linear::HighSpeed(ftdi, info);
                default:
                    throw gcnew ArgumentException("Invalid controller type");
            }
        });
    }

    String^ Controller::GetDescription() {
        TRY({
            return marshal_as<String^>(nativeController->GetDescription()); 
        });
    }

    String^ Controller::GetSerialNumber() {
        TRY({
            return marshal_as<String^>(nativeController->GetSerialNumber());
        });
    }

    void Controller::Reset() {
        GET(controller, linear::IReset);
        TRY({controller->Reset();});
    }

    void Controller::Close() {
        GET(controller, linear::IClose);
        TRY({ controller->Close(); });
    }

    void Controller::DataSetHighByteFirst() {
        GET(controller, linear::IDataEndian);
        TRY({ controller->DataSetHighByteFirst(); });
    }

    void Controller::DataSetLowByteFirst() {
        GET(controller, linear::IDataEndian);
        TRY({ controller->DataSetLowByteFirst(); });
    }

    int Controller::DataSend(array<Byte>^ data, int start, int length) {
        MUST_NOT_BE_NULL(data);
        MUST_NOT_BE_LESS(start, 0);
        if (length < 1) {
            length = data->Length - start;
        }
        MUST_NOT_BE_GREATER(start + length, data->Length);
        GET(controller, linear::IDataSend);
        TRY({
            pin_ptr<Byte> pinned_data = &data[start];
            return controller->DataSend(pinned_data, length);
        });
    }

    int Controller::DataSend(array<UInt16>^ data, int start, int length) {
        MUST_NOT_BE_NULL(data);
        MUST_NOT_BE_LESS(start, 0);
        if (length < 1) {
            length = data->Length - start;
        }
        MUST_NOT_BE_GREATER(start + length, data->Length);
        GET(controller, linear::IDataSend);
        TRY({
            pin_ptr<UInt16> pinned_data = &data[start];
            return controller->DataSend(pinned_data, length);
        });
    }

    int Controller::DataSend(array<UInt32>^ data, int start, int length) {
        MUST_NOT_BE_NULL(data);
        MUST_NOT_BE_LESS(start, 0);
        if (length < 1) {
            length = data->Length - start;
        }
        MUST_NOT_BE_GREATER(start + length, data->Length);
        GET(controller, linear::IDataSend);
        TRY({
            pin_ptr<UInt32> pinned_data = &data[start];
            return controller->DataSend(pinned_data, length);
        });
    }

    int Controller::DataReceive(array<Byte>^ data, int start, int length) {
        MUST_NOT_BE_NULL(data);
        MUST_NOT_BE_LESS(start, 0);
        if (length < 1) {
            length = data->Length - start;
        }
        MUST_NOT_BE_GREATER(start + length, data->Length);
        GET(controller, linear::IDataReceive);
        TRY({
            pin_ptr<Byte> pinned_data = &data[start];
            return controller->DataReceive(pinned_data, length);
        });
    }

    int Controller::DataReceive(array<UInt16>^ data, int start, int length) {
        MUST_NOT_BE_NULL(data);
        MUST_NOT_BE_LESS(start, 0);
        if (length < 1) {
            length = data->Length - start;
        }
        MUST_NOT_BE_GREATER(start + length, data->Length);
        GET(controller, linear::IDataReceive);
        TRY({
            pin_ptr<UInt16> pinned_data = &data[start];
            return controller->DataReceive(pinned_data, length);
        });
    }

    int Controller::DataReceive(array<UInt32>^ data, int start, int length) {
        MUST_NOT_BE_NULL(data);
        MUST_NOT_BE_LESS(start, 0);
        if (length < 1) {
            length = data->Length - start;
        }
        MUST_NOT_BE_GREATER(start + length, data->Length);
        GET(controller, linear::IDataReceive);
        TRY({
            pin_ptr<UInt32> pinned_data = &data[start];
            return controller->DataReceive(pinned_data, length);
        });
    }

    void Controller::DataStartCollect(int totalSamples, Trigger trigger) {
        GET(controller, linear::ICollect);
        TRY({
            controller->DataStartCollect(totalSamples,
                static_cast<linear::ICollect::Trigger>(trigger));
        });
    }

    bool Controller::DataIsCollectDone() {
        GET(controller, linear::ICollect);
        TRY({
            return controller->DataIsCollectDone();
        });

    }

    void Controller::DataCancelCollect() {
        GET(controller, linear::ICollect);
        TRY({
            controller->DataCancelCollect();
        });
    }

    void Controller::DataSetCharacteristics(bool isMultichannel, int sampleBytes, bool isPositiveClock) {
        GET(controller, linear::FtdiAdc);
        TRY({
            controller->DataSetCharacteristics(isMultichannel, sampleBytes, isPositiveClock);
        });
    }

    void Controller::SpiSend(array<Byte>^ values) {
        MUST_NOT_BE_NULL(values);
        GET(controller, linear::ISpiSendOnly);
        TRY({
            pin_ptr<Byte> pinned_values = &values[0];
            controller->SpiSend(pinned_values, values->Length);
        });
    }

    array<Byte>^ Controller::SpiReceive(int numBytes) {
        MUST_NOT_BE_LESS(numBytes, 1);
        auto data = gcnew array<Byte>(numBytes);
        GET(controller, linear::ISpi);
        TRY({
            pin_ptr<Byte> pinned_values = &data[0];
            controller->SpiReceive(pinned_values, numBytes);
            return data;
        });
    }

    array<Byte>^ Controller::SpiTransceive(array<Byte>^ sendValues) {
        MUST_NOT_BE_NULL(sendValues);
        int length = sendValues->Length;
        auto receive_data = gcnew array<Byte>(length);
        GET(controller, linear::ISpi);
        TRY({
            pin_ptr<Byte> pinned_send = &sendValues[0];
            pin_ptr<Byte> pinned_receive = &receive_data[0];
            controller->SpiTransceive(pinned_send, pinned_receive, length);
            return receive_data;
        });
    }

    void Controller::SpiSendAtAddress(Byte address, Byte value) {
        GET(controller, linear::ISpiSendOnly);
        TRY({
            controller->SpiSendAtAddress(address, value);
        });
    }

    void Controller::SpiSendAtAddress(Byte address, array<Byte>^ values) {
        MUST_NOT_BE_NULL(values);
        GET(controller, linear::ISpiSendOnly);
        TRY({
            pin_ptr<Byte> pinned_values = &values[0];
            controller->SpiSendAtAddress(address, pinned_values, values->Length);
        });
    }

    Byte Controller::SpiReceiveAtAddress(Byte address) {
        GET(controller, linear::ISpi);
        TRY({
            return controller->SpiReceiveAtAddress(address);
        });
    }

    array<Byte>^ Controller::SpiReceiveAtAddress(Byte address, int numBytes) {
        MUST_NOT_BE_LESS(numBytes, 1);
        GET(controller, linear::ISpi);
        auto data = gcnew array<Byte>(numBytes);
        TRY({
            pin_ptr<Byte> pinned_data = &data[0];
            controller->SpiReceiveAtAddress(address, pinned_data, numBytes);
            return data;
        });
    }

    void Controller::SpiSetCsState(ChipSelectState state) {
        GET(controller, linear::ISpiSendOnly);
        TRY({
            controller->SpiSetCsState(static_cast<linear::ISpiSendOnly::SpiCsState>(state));
        });
    }

    void Controller::SpiSendNoChipSelect(array<Byte>^ values) {
        MUST_NOT_BE_NULL(values);
        GET(controller, linear::ISpiSendOnly);
        TRY({
            pin_ptr<Byte> pinned_data = &values[0];
            controller->SpiSendNoChipSelect(pinned_data, values->Length);
        });
    }

    array<Byte>^ Controller::SpiReceiveNoChipSelect(int numBytes) {
        MUST_NOT_BE_LESS(numBytes, 1);
        auto data = gcnew array<Byte>(numBytes);
        GET(controller, linear::ISpi);
        TRY({
            pin_ptr<Byte> pinned_values = &data[0];
        controller->SpiReceiveNoChipSelect(pinned_values, numBytes);
        return data;
        });
    }

    array<Byte>^ Controller::SpiTransceiveNoChipSelect(array<Byte>^ sendValues) {
        MUST_NOT_BE_NULL(sendValues);
        int length = sendValues->Length;
        auto receive_data = gcnew array<Byte>(length);
        GET(controller, linear::ISpi);
        TRY({
            pin_ptr<Byte> pinned_send = &sendValues[0];
        pin_ptr<Byte> pinned_receive = &receive_data[0];
        controller->SpiTransceiveNoChipSelect(pinned_send, pinned_receive, length);
        return receive_data;
        });
    }

    bool Controller::FpgaGetIsLoaded(String^ fpgaFile) {
        MUST_NOT_BE_NULL(fpgaFile);
        GET(controller, linear::IFpgaLoad);
        TRY({
            return controller->FpgaGetIsLoaded(marshal_as<std::string>(fpgaFile));
        });
    }

    void Controller::FpgaLoadFile(String^ fpgaFile) {
        MUST_NOT_BE_NULL(fpgaFile);
        GET(controller, linear::IFpgaLoad);
        TRY({
            controller->FpgaLoadFile(marshal_as<std::string>(fpgaFile));
        });
    }

    int Controller::FpgaLoadFileChunked(String^ fpgaFile) {
        MUST_NOT_BE_NULL(fpgaFile);
        GET(controller, linear::IFpgaLoad);
        TRY({
            return controller->FpgaLoadFileChunked(marshal_as<std::string>(fpgaFile));
        });
    }

    void Controller::FpgaCancelLoad() {
        GET(controller, linear::IFpgaLoad);
        TRY({
            controller->FpgaCancelLoad();
        });
    }

    String^ Controller::EepromReadString() {
        GET(controller, linear::Controller);
        TRY({
            const int MAX_EEPROM_SIZE = 512;
            char buffer[MAX_EEPROM_SIZE];
            controller->EepromReadString(buffer, MAX_EEPROM_SIZE);
            return marshal_as<String^>(std::string(buffer));
        });
    }

    void Controller::HsPurgeIo() {
        GET(controller, HighSpeed);
        TRY({
            controller->PurgeIo();
        });
    }

    void Controller::HsSetBitMode(BitMode mode) {
        GET(controller, HighSpeed);
        TRY({
            controller->SetBitMode(static_cast<HighSpeed::BitMode>(mode));
        });
    }

    void Controller::HsFpgaToggleReset() {
        GET(controller, HighSpeed);
        TRY({
            controller->FpgaToggleReset();
        });
    }

    void Controller::HsFpgaWriteAddress(Byte address) {
        GET(controller, HighSpeed);
        TRY({
            controller->FpgaWriteAddress(address);
        });
    }

    void Controller::HsFpgaWriteData(Byte data) {
        GET(controller, HighSpeed);
        TRY({
            controller->FpgaWriteData(data);
        });
    }

    Byte Controller::HsFpgaReadData() {
        GET(controller, HighSpeed);
        TRY({
            return controller->FpgaReadData();
        });
    }

    void Controller::HsFpgaWriteDataAtAddress(Byte address, Byte data) {
        GET(controller, HighSpeed);
        TRY({
            controller->FpgaWriteDataAtAddress(address, data);
        });
    }

    Byte Controller::HsFpgaReadDataAtAddress(Byte address) {
        GET(controller, HighSpeed);
        TRY({
            return controller->FpgaReadDataAtAddress(address);
        });
    }

    void Controller::HsGpioWriteHighByte(Byte value) {
        GET(controller, HighSpeed);
        TRY({
            controller->GpioWriteHighByte(value);
        });
    }

    Byte Controller::HsGpioReadHighByte() {
        GET(controller, HighSpeed);
        TRY({
            return controller->GpioReadHighByte();
        });
    }

    void Controller::HsGpioWriteLowByte(Byte value) {
        GET(controller, HighSpeed);
        TRY({
            controller->GpioWriteLowByte(value);
        });
    }

    Byte Controller::HsGpioReadLowByte() {
        GET(controller, HighSpeed);
        TRY({
            return controller->GpioReadLowByte();
        });
    }

    void Controller::HsFpgaEepromSetBitBangRegister(Byte registerAddress) {
        GET(controller, HighSpeed);
        TRY({
            controller->FpgaEepromSetBitBangRegister(registerAddress);
        });
    }

    void Controller::Dc1371SetGenericConfig(UInt32 genericConfig) {
        GET(controller, Dc1371);
        TRY({
            controller->SetGenericConfig(genericConfig);
        });
    }

    void Controller::Dc1371SetDemoConfig(UInt32 demoConfig) {
        GET(controller, Dc1371);
        TRY({
            controller->SetDemoConfig(demoConfig);
        });
    }

    void Controller::Dc1371SpiChooseChipSelect(ChipSelect chipSelect) {
        GET(controller, Dc1371);
        TRY({
            controller->SpiChooseChipSelect(static_cast<Dc1371::ChipSelect>(chipSelect));
        });
    }

    void Controller::Dc890GpioSetByte(Byte data) {
        GET(controller, Dc890);
        TRY({
            controller->GpioSetByte(data);
        });
    }

    void Controller::Dc890GpioSpiSetBits(int csBit, int sckBit, int sdiBit) {
        GET(controller, Dc890);
        TRY({
            controller->GpioSpiSetBits(csBit, sckBit, sdiBit);
        });
    }

    void Controller::Dc890Flush() {
        GET(controller, Dc890);
        TRY({
            controller->Flush();
        });
    }
}

