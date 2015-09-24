#pragma once
#include <vector>
#include <string>
#include <cstdint>
#include "i_close.hpp"
#include "i_collect.hpp"
#include "i_reset.hpp"
#include "i_data_endian.hpp"
#include "i_data_receive.hpp"
#include "controller.hpp"
#include "ftdi.hpp"

namespace linear {

    using std::string;
    using std::vector;

    class FtdiAdc : public ICollect, IReset, IDataEndian, IDataReceive, IClose {
    public:
        FtdiAdc(const Ftdi& ftdi, const LccControllerInfo& info) : ftdi(ftdi), 
            description(info.description), serial_number(info.serial_number), index(info.id),
            type(Controller::Type(info.type)) { }
        virtual ~FtdiAdc() { Close(); }

        Type GetType() override { return type; }

        string GetDescription() override { return description; }
        string GetSerialNumber() override { return serial_number; }

        void DataSetCharacteristics(bool is_multiple_channels, int bytes_per_sample, 
                bool is_positive_clock) { 
            is_multichannel = is_multiple_channels;
            sample_bytes = bytes_per_sample;
            is_sampled_on_positive_edge = is_positive_clock;
        }
        void DataStartCollect(int total_samples, Trigger trigger) override;
        bool DataIsCollectDone() override;
        void DataCancelCollect() override;
        void DataSetHighByteFirst() override { swap_bytes = true; }
        void DataSetLowByteFirst() override { swap_bytes = false; }
        
        int  DataReceive(uint8_t data[], int num_bytes) override { return ReadBytes(data, num_bytes); }
        int  DataReceive(uint16_t data[], int num_values) override {
            return Controller::DataRead(*this, swap_bytes, data, num_values);
        }
        int DataReceive(uint32_t data[], int num_values) override {
            return Controller::DataRead(*this, swap_bytes, data, num_values);
        }

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
        void SetTimeouts(ULONG read_timeout = DEFAULT_READ_TIMEOUT,
                ULONG write_timeout = DEFAULT_WRITE_TIMEOUT) {
            OpenIfNeeded();
            ftdi.SetTimeouts(handle, read_timeout, write_timeout);
        }
    private:
        static const int DEFAULT_READ_TIMEOUT = 100;
        static const int DEFAULT_WRITE_TIMEOUT = 50;
        Type type;
        friend class Controller;
        bool OpenByIndex();
        void OpenBySerialNumber();
        void OpenIfNeeded();
        int ReadBytes(uint8_t data[], int total_bytes);
        const Ftdi& ftdi;
        string description;
        string serial_number;
        int index;
        FT_HANDLE handle = nullptr;
        bool swap_bytes = true;
        bool is_sampled_on_positive_edge = true;
        int sample_bytes = 2;
        bool is_multichannel = false;
        bool collect_was_read = true;
    };
}

