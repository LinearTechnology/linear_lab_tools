// LtcControllerComm.h

#pragma once
#include <msclr\marshal_cppstd.h>
#include <stdexcept>
#include "../ltc_controller_comm/controller.hpp"

using namespace System;
using namespace System::Text;
using std::logic_error;
using std::domain_error;
using std::runtime_error;
using std::invalid_argument;
using std::exception;

using msclr::interop::marshal_as;

namespace LtcControllerComm {

public
ref class HardwareException : Exception {
   public:
    HardwareException() : Exception() {}
    HardwareException(String ^ message) : Exception(message) {}
    HardwareException(String ^ message, Exception ^ inner) : Exception(message, inner) {}
};

public
ref class LogicException : Exception {
   public:
    LogicException() : Exception() {}
    LogicException(String ^ message) : Exception(message) {}
    LogicException(String ^ message, Exception ^ inner) : Exception(message, inner) {}
};

public
ref class Controller : IDisposable {
   public:
    [FlagsAttribute] enum class Type : int {
        None      = 0,
        Dc1371    = 1,
        Dc718     = 2,
        Dc890     = 4,
        HighSpeed = 8,
        SocKit    = 16,
        Unknown   = -1
    };

    enum class ChipSelectState : int { Low = 0, High = 1 };

    enum class Trigger : int {
        None                   = 0,
        StartPositiveEdge      = 1,
        Dc890StartNegativeEdge = 2,
        Dc1371StopNegativeEdge = 3
    };

    enum class BitMode : int { Mpsse = 0x02, Fifo = 0x40 };

    enum class ChipSelect : int { One = 1, Two = 2 };

    internal : static const int MaxDescriptionSize  = 64;
    static const int            MaxSerialNumberSize = 16;

   public:
    value struct Info {
       public:
        property Controller::Type Type {
            Controller::Type get() { return type; }
        }
        property String ^ Description { String ^ get() { return description; } } property String ^
                SerialNumber { String ^ get() { return serial_number; } }

                internal : Info(Controller::Type type,
                                String ^ description,
                                String ^ serial_number,
                                UInt32 id)
                : type(type),
                description(description), serial_number(serial_number), id(id) {}
        Controller::Type type;
        String ^ description;
        String ^ serial_number;
        UInt32 id;
    };

    static array<Controller::Info> ^ GetControllerList(Type acceptableTypes);

    Controller(Info controllerInfo);

    String ^ GetDescription();

    String ^ GetSerialNumber();

    void Reset();

    void Close();

    void DataSetHighByteFirst();

    void DataSetLowByteFirst();

    int DataSend(array<Byte> ^ data, int start, int length);
    int DataSend(array<Byte> ^ data, int start) { return DataSend(data, start, 0); }
    int DataSend(array<Byte> ^ data) { return DataSend(data, 0, 0); }

    int DataSend(array<UInt16> ^ data, int start, int length);
    int DataSend(array<UInt16> ^ data, int start) { return DataSend(data, start, 0); }
    int DataSend(array<UInt16> ^ data) { return DataSend(data, 0, 0); }

    int DataSend(array<Int16> ^ data, int start, int length);
    int DataSend(array<Int16> ^ data, int start) { return DataSend(data, start, 0); }
    int DataSend(array<Int16> ^ data) { return DataSend(data, 0, 0); }

    int DataSend(array<UInt32> ^ data, int start, int length);
    int DataSend(array<UInt32> ^ data, int start) { return DataSend(data, start, 0); }
    int DataSend(array<UInt32> ^ data) { return DataSend(data, 0, 0); }

    int DataSend(array<Int32> ^ data, int start, int length);
    int DataSend(array<Int32> ^ data, int start) { return DataSend(data, start, 0); }
    int DataSend(array<Int32> ^ data) { return DataSend(data, 0, 0); }

    int DataReceive(array<Byte> ^ data, int start, int length);
    int DataReceive(array<Byte> ^ data, int start) { return DataSend(data, start, 0); }
    int DataReceive(array<Byte> ^ data) { return DataSend(data, 0, 0); }

    int DataReceive(array<UInt16> ^ data, int start, int length);
    int DataReceive(array<UInt16> ^ data, int start) { return DataSend(data, start, 0); }
    int DataReceive(array<UInt16> ^ data) { return DataSend(data, 0, 0); }

    int DataReceive(array<Int16> ^ data, int start, int length);
    int DataReceive(array<Int16> ^ data, int start) { return DataSend(data, start, 0); }
    int DataReceive(array<Int16> ^ data) { return DataSend(data, 0, 0); }

    int DataReceive(array<UInt32> ^ data, int start, int length);
    int DataReceive(array<UInt32> ^ data, int start) { return DataSend(data, start, 0); }
    int DataReceive(array<UInt32> ^ data) { return DataSend(data, 0, 0); }

    int DataReceive(array<Int32> ^ data, int start, int length);
    int DataReceive(array<Int32> ^ data, int start) { return DataSend(data, start, 0); }
    int DataReceive(array<Int32> ^ data) { return DataSend(data, 0, 0); }

    void DataStartCollect(int totalSamples, Trigger trigger);

    bool DataIsCollectDone();

    void DataCancelCollect();

    void DataSetCharacteristics(bool isMultichannel, int sampleBytes, bool isPositiveClock);

    void SpiSend(array<Byte> ^ values);

    array<Byte> ^ SpiReceive(int numBytes);

    array<Byte> ^ SpiTransceive(array<Byte> ^ sendValues);

    void SpiSendAtAddress(Byte address, Byte value);

    void SpiSendAtAddress(Byte address, array<Byte> ^ values);

    Byte SpiReceiveAtAddress(Byte address);

    array<Byte> ^ SpiReceiveAtAddress(Byte address, int numBytes);

    void SpiSetCsState(ChipSelectState state);

    void SpiSendNoChipSelect(array<Byte> ^ values);

    array<Byte> ^ SpiReceiveNoChipSelect(int numBytes);

    array<Byte> ^ SpiTransceiveNoChipSelect(array<Byte> ^ sendValues);

    bool FpgaGetIsLoaded(String ^ fpgaFile);

    void FpgaLoadFile(String ^ fpgaFile);

    int FpgaLoadFileChunked(String ^ fpgaFile);

    void FpgaCancelLoad();

    String ^ EepromReadString();

    void HsPurgeIo();

    void HsSetBitMode(BitMode mode);

    void HsFpgaToggleReset();

    void HsFpgaWriteAddress(Byte address);

    void HsFpgaWriteData(Byte data);

    Byte HsFpgaReadData();

    void HsFpgaWriteDataAtAddress(Byte address, Byte data);

    Byte HsFpgaReadDataAtAddress(Byte address);

    void HsGpioWriteHighByte(Byte value);

    Byte HsGpioReadHighByte();

    void HsGpioWriteLowByte(Byte value);

    Byte HsGpioReadLowByte();

    void MpsseEnableDivideBy5(bool enable);

    void MpsseSetClkDivider(uint16_t divider);

    void HsFpgaEepromSetBitBangRegister(Byte registerAddress);

    void Dc1371SetGenericConfig(UInt32 genericConfig);

    void Dc1371SetDemoConfig(UInt32 demoConfig);

    void Dc1371SpiChooseChipSelect(ChipSelect chipSelect);

    void Dc890GpioSetByte(Byte data);

    void Dc890GpioSpiSetBits(int csBit, int sckBit, int sdiBit);

    void Dc890Flush();

    int Dc590Write(String ^ tppStr);
    int Dc590Write(array<Byte> ^ buffer);

    String ^ Dc590Read(int numChars);
    int Dc590Read(array<Byte> ^ buffer);

    void Dc590Flush();

    void Dc590SetEventChar(bool enable);

    ~Controller() {
        Cleanup();
        GC::SuppressFinalize(this);
    }

    !Controller() { Cleanup(); }

   protected:
    virtual void Cleanup() {
        delete nativeController;
        nativeController = nullptr;
    }

   private:
    linear::Controller* nativeController = nullptr;
};
}
