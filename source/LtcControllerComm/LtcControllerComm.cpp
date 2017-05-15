// This is the main DLL file.
#include "LtcControllerComm.h"
#include "..\ltc_controller_comm\dc1371.hpp"
#include "..\ltc_controller_comm\dc590.hpp"
#include "..\ltc_controller_comm\dc718.hpp"
#include "..\ltc_controller_comm\dc890.hpp"
#include "..\ltc_controller_comm\high_speed.hpp"
#include "..\ltc_controller_comm\soc_kit.hpp"
#include "..\ltc_controller_comm\utilities.hpp"

using linear::Dc1371;
using linear::Dc1371Error;
using linear::Dc590;
using linear::Dc718;
using linear::Dc890;
using linear::HighSpeed;
using linear::Ftdi;
using linear::FtdiError;
using linear::SocKit;
using linear::safe_memcpy;

extern Ftdi ftdi;

namespace LtcControllerComm {

#ifdef ASSERT_NOT_NULL
#undef ASSERT_NOT_NULL
#endif

#ifdef QUOTE
#undef QUOTE
#endif
#define QUOTE(x) #x
#define ASSERT_NOT_NULL(pointer)                                               \
    \
if((pointer) == nullptr) {                                                     \
        throw gcnew ArgumentNullException(QUOTE(pointer) " must not be null"); \
    \
}
#define ASSERT_GREATER(a, b)                                                       \
    \
if((a) <= (b)) {                                                                   \
        throw gcnew ArgumentException(QUOTE(a) " must be greater than " QUOTE(b)); \
    \
}
#define ASSERT_NOT_GREATER(a, b)                                                       \
    \
if((a) > (b)) {                                                                        \
        throw gcnew ArgumentException(QUOTE(a) " must not be greater than " QUOTE(b)); \
    \
}
#define ASSERT_LESS(a, b)                                                       \
    \
if((a) >= (b)) {                                                                \
        throw gcnew ArgumentException(QUOTE(a) " must be less than " QUOTE(b)); \
    \
}
#define ASSERT_NOT_LESS(a, b)                                                       \
    \
if((a) < (b)) {                                                                     \
        throw gcnew ArgumentException(QUOTE(a) " must not be less than " QUOTE(b)); \
    \
}

#define TRY(code)                                                                \
    try {                                                                        \
        code                                                                     \
    } catch (invalid_argument & err) {                                           \
        throw gcnew ArgumentException(marshal_as<String ^>(err.what()));         \
    } catch (domain_error & err) {                                               \
        throw gcnew InvalidOperationException(marshal_as<String ^>(err.what())); \
    } catch (logic_error & err) {                                                \
        throw gcnew LogicException(marshal_as<String ^>(err.what()));            \
    } catch (linear::HardwareError & err) {                                      \
        throw gcnew HardwareException(marshal_as<String ^>(err.what()));         \
    } catch (exception & err) {                                                  \
        throw gcnew Exception(marshal_as<String ^>(err.what()));                 \
    } catch (...) { throw gcnew Exception("An unknown error occurred."); }

#define GET(ctrl, type)                                                          \
    \
type* ctrl;                                                                      \
    \
do {                                                                             \
        ASSERT_NOT_NULL(nativeController);                                       \
        ctrl = dynamic_cast<type*>(nativeController);                            \
        if (ctrl == nullptr) {                                                   \
            throw gcnew NotSupportedException(                                   \
                    "This operation is not supported for this controller type"); \
        }                                                                        \
    \
}                                                                         \
    while (0)

array<Controller::Info> ^ Controller::GetControllerList(Type acceptableTypes) {
    TRY({
        int                       acceptable_types = static_cast<int>(acceptableTypes);
        vector<LccControllerInfo> dc1371_info;
        vector<LccControllerInfo> ftdi_info;
        if ((acceptable_types & LCC_TYPE_DC1371) != 0) {
            dc1371_info = Dc1371::ListControllers(Dc1371::MAX_CONTROLLERS);
        }
        if ((acceptable_types & ~LCC_TYPE_DC1371) != 0) {
            ftdi_info = ftdi.ListControllers(acceptable_types, 20);
        }
        auto controllers = gcnew array<Controller::Info>(
                linear::narrow<int>(dc1371_info.size() + ftdi_info.size()));
        int index = 0;
        for (auto& info : dc1371_info) {
            controllers[index] =
                    Controller::Info(static_cast<Controller::Type>(info.type),
                                     marshal_as<String ^>(info.description),
                                     marshal_as<String ^>(info.serial_number), info.id);
            ++index;
        }
        for (auto& info : ftdi_info) {
            controllers[index] =
                    Controller::Info(static_cast<Controller::Type>(info.type),
                                     marshal_as<String ^>(info.description),
                                     marshal_as<String ^>(info.serial_number), info.id);
            ++index;
        }
        return controllers;
    });
}

Controller::Controller(Info controllerInfo) {
    TRY({
        LccControllerInfo info;
        info.type = static_cast<int>(controllerInfo.type);
        safe_memcpy(info.description, LCC_MAX_DESCRIPTION_SIZE,
                    marshal_as<std::string>(controllerInfo.description).c_str(),
                    controllerInfo.description->Length);
        info.description[controllerInfo.description->Length] = '\0';
        safe_memcpy(info.serial_number, LCC_MAX_SERIAL_NUMBER_SIZE,
                    marshal_as<std::string>(controllerInfo.serial_number).c_str(),
                    controllerInfo.serial_number->Length);
        info.serial_number[controllerInfo.serial_number->Length] = '\0';
        info.id                                                  = controllerInfo.id;
        switch (controllerInfo.type) {
            case Controller::Type::Dc1371:
                nativeController = new linear::Dc1371(info);
                return;
            case Controller::Type::Dc718:
                nativeController = new linear::Dc718(ftdi, info);
                return;
            case Controller::Type::Dc890:
                nativeController = new linear::Dc890(ftdi, info);
                return;
            case Controller::Type::HighSpeed:
                nativeController = new linear::HighSpeed(ftdi, info);
                return;
            case Controller::Type::SocKit:
                nativeController = new linear::SocKit(info);
            default:
                throw invalid_argument("Invalid controller type");
        }
    });
}

String ^ Controller::GetDescription() {
    TRY({ return marshal_as<String ^>(nativeController->GetDescription()); });
}

String ^ Controller::GetSerialNumber() {
    TRY({ return marshal_as<String ^>(nativeController->GetSerialNumber()); });
}

void Controller::Reset() {
    GET(controller, linear::IReset);
    TRY({ controller->Reset(); });
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

int Controller::DataSend(array<Byte> ^ data, int start, int length) {
    ASSERT_NOT_NULL(data);
    ASSERT_NOT_LESS(start, 0);
    if (length < 1) { length = data->Length - start; }
    ASSERT_NOT_GREATER(start + length, data->Length);
    GET(controller, linear::IDataSend);
    TRY({
        pin_ptr<Byte> pinned_data = &data[start];
        return controller->DataSend(pinned_data, length);
    });
}

int Controller::DataSend(array<UInt16> ^ data, int start, int length) {
    ASSERT_NOT_NULL(data);
    ASSERT_NOT_LESS(start, 0);
    if (length < 1) { length = data->Length - start; }
    ASSERT_NOT_GREATER(start + length, data->Length);
    GET(controller, linear::IDataSend);
    TRY({
        pin_ptr<UInt16> pinned_data = &data[start];
        return controller->DataSend(pinned_data, length);
    });
}

int Controller::DataSend(array<Int16> ^ data, int start, int length) {
    ASSERT_NOT_NULL(data);
    ASSERT_NOT_LESS(start, 0);
    if (length < 1) { length = data->Length - start; }
    ASSERT_NOT_GREATER(start + length, data->Length);
    GET(controller, linear::IDataSend);
    TRY({
        pin_ptr<Int16> pinned_data = &data[start];
        return controller->DataSend((unsigned short*)pinned_data, length);
    });
}

int Controller::DataSend(array<UInt32> ^ data, int start, int length) {
    ASSERT_NOT_NULL(data);
    ASSERT_NOT_LESS(start, 0);
    if (length < 1) { length = data->Length - start; }
    ASSERT_NOT_GREATER(start + length, data->Length);
    GET(controller, linear::IDataSend);
    TRY({
        pin_ptr<UInt32> pinned_data = &data[start];
        return controller->DataSend(pinned_data, length);
    });
}

int Controller::DataSend(array<Int32> ^ data, int start, int length) {
    ASSERT_NOT_NULL(data);
    ASSERT_NOT_LESS(start, 0);
    if (length < 1) { length = data->Length - start; }
    ASSERT_NOT_GREATER(start + length, data->Length);
    GET(controller, linear::IDataSend);
    TRY({
        pin_ptr<Int32> pinned_data = &data[start];
        return controller->DataSend((unsigned int*)pinned_data, length);
    });
}

int Controller::DataReceive(array<Byte> ^ data, int start, int length) {
    ASSERT_NOT_NULL(data);
    ASSERT_NOT_LESS(start, 0);
    if (length < 1) { length = data->Length - start; }
    ASSERT_NOT_GREATER(start + length, data->Length);
    GET(controller, linear::IDataReceive);
    TRY({
        pin_ptr<Byte> pinned_data = &data[start];
        return controller->DataReceive(pinned_data, length);
    });
}

int Controller::DataReceive(array<UInt16> ^ data, int start, int length) {
    ASSERT_NOT_NULL(data);
    ASSERT_NOT_LESS(start, 0);
    if (length < 1) { length = data->Length - start; }
    ASSERT_NOT_GREATER(start + length, data->Length);
    GET(controller, linear::IDataReceive);
    TRY({
        pin_ptr<UInt16> pinned_data = &data[start];
        return controller->DataReceive(pinned_data, length);
    });
}

int Controller::DataReceive(array<Int16> ^ data, int start, int length) {
    ASSERT_NOT_NULL(data);
    ASSERT_NOT_LESS(start, 0);
    if (length < 1) { length = data->Length - start; }
    ASSERT_NOT_GREATER(start + length, data->Length);
    GET(controller, linear::IDataReceive);
    TRY({
        pin_ptr<Int16> pinned_data = &data[start];
        return controller->DataReceive((unsigned short*)pinned_data, length);
    });
}

int Controller::DataReceive(array<UInt32> ^ data, int start, int length) {
    ASSERT_NOT_NULL(data);
    ASSERT_NOT_LESS(start, 0);
    if (length < 1) { length = data->Length - start; }
    ASSERT_NOT_GREATER(start + length, data->Length);
    GET(controller, linear::IDataReceive);
    TRY({
        pin_ptr<UInt32> pinned_data = &data[start];
        return controller->DataReceive(pinned_data, length);
    });
}

int Controller::DataReceive(array<Int32> ^ data, int start, int length) {
    ASSERT_NOT_NULL(data);
    ASSERT_NOT_LESS(start, 0);
    if (length < 1) { length = data->Length - start; }
    ASSERT_NOT_GREATER(start + length, data->Length);
    GET(controller, linear::IDataReceive);
    TRY({
        pin_ptr<Int32> pinned_data = &data[start];
        return controller->DataReceive((unsigned int*)pinned_data, length);
    });
}

void Controller::DataStartCollect(int totalSamples, Trigger trigger) {
    GET(controller, linear::ICollect);
    TRY({
        controller->DataStartCollect(totalSamples, static_cast<linear::ICollect::Trigger>(trigger));
    });
}

bool Controller::DataIsCollectDone() {
    GET(controller, linear::ICollect);
    TRY({ return controller->DataIsCollectDone(); });
}

void Controller::DataCancelCollect() {
    GET(controller, linear::ICollect);
    TRY({ controller->DataCancelCollect(); });
}

void Controller::DataSetCharacteristics(bool isMultichannel,
                                        int  sampleBytes,
                                        bool isPositiveClock) {
    GET(controller, linear::FtdiAdc);
    TRY({ controller->DataSetCharacteristics(isMultichannel, sampleBytes, isPositiveClock); });
}

void Controller::SpiSend(array<Byte> ^ values) {
    ASSERT_NOT_NULL(values);
    GET(controller, linear::ISpiSendOnly);
    TRY({
        pin_ptr<Byte> pinned_values = &values[0];
        controller->SpiSend(pinned_values, values->Length);
    });
}

array<Byte> ^ Controller::SpiReceive(int numBytes) {
    ASSERT_NOT_LESS(numBytes, 1);
    auto data = gcnew array<Byte>(numBytes);
    GET(controller, linear::ISpi);
    TRY({
        pin_ptr<Byte> pinned_values = &data[0];
        controller->SpiReceive(pinned_values, numBytes);
        return data;
    });
}

array<Byte> ^ Controller::SpiTransceive(array<Byte> ^ sendValues) {
    ASSERT_NOT_NULL(sendValues);
    int  length       = sendValues->Length;
    auto receive_data = gcnew array<Byte>(length);
    GET(controller, linear::ISpi);
    TRY({
        pin_ptr<Byte> pinned_send    = &sendValues[0];
        pin_ptr<Byte> pinned_receive = &receive_data[0];
        controller->SpiTransceive(pinned_send, pinned_receive, length);
        return receive_data;
    });
}

void Controller::SpiSendAtAddress(Byte address, Byte value) {
    GET(controller, linear::ISpiSendOnly);
    TRY({ controller->SpiSendAtAddress(address, value); });
}

void Controller::SpiSendAtAddress(Byte address, array<Byte> ^ values) {
    ASSERT_NOT_NULL(values);
    GET(controller, linear::ISpiSendOnly);
    TRY({
        pin_ptr<Byte> pinned_values = &values[0];
        controller->SpiSendAtAddress(address, pinned_values, values->Length);
    });
}

Byte Controller::SpiReceiveAtAddress(Byte address) {
    GET(controller, linear::ISpi);
    TRY({ return controller->SpiReceiveAtAddress(address); });
}

array<Byte> ^ Controller::SpiReceiveAtAddress(Byte address, int numBytes) {
    ASSERT_NOT_LESS(numBytes, 1);
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
    TRY({ controller->SpiSetCsState(static_cast<linear::ISpiSendOnly::SpiCsState>(state)); });
}

void Controller::SpiSendNoChipSelect(array<Byte> ^ values) {
    ASSERT_NOT_NULL(values);
    GET(controller, linear::ISpiSendOnly);
    TRY({
        pin_ptr<Byte> pinned_data = &values[0];
        controller->SpiSendNoChipSelect(pinned_data, values->Length);
    });
}

array<Byte> ^ Controller::SpiReceiveNoChipSelect(int numBytes) {
    ASSERT_NOT_LESS(numBytes, 1);
    auto data = gcnew array<Byte>(numBytes);
    GET(controller, linear::ISpi);
    TRY({
        pin_ptr<Byte> pinned_values = &data[0];
        controller->SpiReceiveNoChipSelect(pinned_values, numBytes);
        return data;
    });
}

array<Byte> ^ Controller::SpiTransceiveNoChipSelect(array<Byte> ^ sendValues) {
    ASSERT_NOT_NULL(sendValues);
    int  length       = sendValues->Length;
    auto receive_data = gcnew array<Byte>(length);
    GET(controller, linear::ISpi);
    TRY({
        pin_ptr<Byte> pinned_send    = &sendValues[0];
        pin_ptr<Byte> pinned_receive = &receive_data[0];
        controller->SpiTransceiveNoChipSelect(pinned_send, pinned_receive, length);
        return receive_data;
    });
}

bool Controller::FpgaGetIsLoaded(String ^ fpgaFile) {
    ASSERT_NOT_NULL(fpgaFile);
    GET(controller, linear::IFpgaLoad);
    TRY({ return controller->FpgaGetIsLoaded(marshal_as<std::string>(fpgaFile)); });
}

void Controller::FpgaLoadFile(String ^ fpgaFile) {
    ASSERT_NOT_NULL(fpgaFile);
    GET(controller, linear::IFpgaLoad);
    TRY({ controller->FpgaLoadFile(marshal_as<std::string>(fpgaFile)); });
}

int Controller::FpgaLoadFileChunked(String ^ fpgaFile) {
    ASSERT_NOT_NULL(fpgaFile);
    GET(controller, linear::IFpgaLoad);
    TRY({ return controller->FpgaLoadFileChunked(marshal_as<std::string>(fpgaFile)); });
}

void Controller::FpgaCancelLoad() {
    GET(controller, linear::IFpgaLoad);
    TRY({ controller->FpgaCancelLoad(); });
}

String ^ Controller::EepromReadString() {
    GET(controller, linear::Controller);
    TRY({
        const int MAX_EEPROM_SIZE = 512;
        char      buffer[MAX_EEPROM_SIZE];
        controller->EepromReadString(buffer, MAX_EEPROM_SIZE);
        return marshal_as<String ^>(std::string(buffer));
    });
}

void Controller::HsPurgeIo() {
    GET(controller, HighSpeed);
    TRY({ controller->PurgeIo(); });
}

void Controller::HsSetBitMode(BitMode mode) {
    GET(controller, HighSpeed);
    TRY({ controller->SetBitMode(static_cast<HighSpeed::BitMode>(mode)); });
}

void Controller::HsFpgaToggleReset() {
    GET(controller, HighSpeed);
    TRY({ controller->FpgaToggleReset(); });
}

void Controller::HsFpgaWriteAddress(Byte address) {
    GET(controller, HighSpeed);
    TRY({ controller->FpgaWriteAddress(address); });
}

void Controller::HsFpgaWriteData(Byte data) {
    GET(controller, HighSpeed);
    TRY({ controller->FpgaWriteData(data); });
}

Byte Controller::HsFpgaReadData() {
    GET(controller, HighSpeed);
    TRY({ return controller->FpgaReadData(); });
}

void Controller::HsFpgaWriteDataAtAddress(Byte address, Byte data) {
    GET(controller, HighSpeed);
    TRY({ controller->FpgaWriteDataAtAddress(address, data); });
}

Byte Controller::HsFpgaReadDataAtAddress(Byte address) {
    GET(controller, HighSpeed);
    TRY({ return controller->FpgaReadDataAtAddress(address); });
}

void Controller::HsGpioWriteHighByte(Byte value) {
    GET(controller, HighSpeed);
    TRY({ controller->GpioWriteHighByte(value); });
}

Byte Controller::HsGpioReadHighByte() {
    GET(controller, HighSpeed);
    TRY({ return controller->GpioReadHighByte(); });
}

void Controller::HsGpioWriteLowByte(Byte value) {
    GET(controller, HighSpeed);
    TRY({ controller->GpioWriteLowByte(value); });
}

Byte Controller::HsGpioReadLowByte() {
    GET(controller, HighSpeed);
    TRY({ return controller->GpioReadLowByte(); });
}

void Controller::HsFpgaEepromSetBitBangRegister(Byte registerAddress) {
    GET(controller, HighSpeed);
    TRY({ controller->FpgaEepromSetBitBangRegister(registerAddress); });
}

void Controller::MpsseEnableDivideBy5(bool enable) {
    GET(controller, HighSpeed);
    TRY({ controller->MpsseEnableDivideBy5(enable); });
}

void Controller::MpsseSetClkDivider(uint16_t divider) {
    GET(controller, HighSpeed);
    TRY({ controller->MpsseSetClkDivider(divider); });
}

void Controller::Dc1371SetGenericConfig(UInt32 genericConfig) {
    GET(controller, Dc1371);
    TRY({ controller->SetGenericConfig(genericConfig); });
}

void Controller::Dc1371SetDemoConfig(UInt32 demoConfig) {
    GET(controller, Dc1371);
    TRY({ controller->SetDemoConfig(demoConfig); });
}

void Controller::Dc1371SpiChooseChipSelect(ChipSelect chipSelect) {
    GET(controller, Dc1371);
    TRY({ controller->SpiChooseChipSelect(static_cast<Dc1371::ChipSelect>(chipSelect)); });
}

void Controller::Dc890GpioSetByte(Byte data) {
    GET(controller, Dc890);
    TRY({ controller->GpioSetByte(data); });
}

void Controller::Dc890GpioSpiSetBits(int csBit, int sckBit, int sdiBit) {
    GET(controller, Dc890);
    TRY({ controller->GpioSpiSetBits(csBit, sckBit, sdiBit); });
}

void Controller::Dc890Flush() {
    GET(controller, Dc890);
    TRY({ controller->Flush(); });
}

int Controller::Dc590Write(String ^ tppStr) {
    ASSERT_NOT_NULL(tppStr);
    GET(controller, Dc590);
    TRY({
        auto str = marshal_as<std::string>(tppStr);
        return controller->Write(str.c_str(), str.size());
    });
}

int Controller::Dc590Write(array<Byte> ^ buffer) {
    ASSERT_NOT_NULL(buffer);
    GET(controller, Dc590);
    TRY({
        pin_ptr<Byte> pinned_data = &buffer[0];
        return controller->Write(pinned_data, buffer->Length);
    });
}

String ^ Controller::Dc590Read(int numChars) {
    GET(controller, Dc590);
    TRY({
        vector<char> buffer(numChars);
        int          num_read   = controller->Read(&buffer[0], numChars);
        auto         buffer_str = string(buffer.data(), num_read);
        return marshal_as<String ^>(buffer_str);
    });
}

int Controller::Dc590Read(array<Byte> ^ buffer) {
    GET(controller, Dc590);
    TRY({
        pin_ptr<Byte> pinned_data = &buffer[0];
        return controller->Read(pinned_data, buffer->Length);
    });
}

void Controller::Dc590Flush() {
    GET(controller, Dc590);
    TRY({ controller->Flush(); });
}

void Controller::Dc590SetEventChar(bool enable) {
    GET(controller, Dc590);
    TRY({ controller->SetEventChar(enable); });
}
}
