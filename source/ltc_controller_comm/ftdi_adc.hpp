#pragma once
#include <vector>
#include <string>
#include <cstdint>
#include "i_close.hpp"
#include "i_collect.hpp"
#include "i_timeout.hpp"
#include "i_reset.hpp"
#include "i_data_endian.hpp"
#include "i_data_receive.hpp"
#include "controller.hpp"
#include "ftdi.hpp"

namespace linear {

    using std::string;
    using std::vector;

    class FtdiAdc : public ICollect, ITimeout, IReset, IDataEndian, IDataReceive, IClose {
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
        void DataCancelReceive() override;

        void EepromReadString(char* buffer, int buffer_size) override;

        void Flush();
        void Reset() override;
        void Close() override;
        void SetTimeouts(ULONG read_timeout, ULONG write_timeout) override;
        pair<ULONG, ULONG> GetTimeouts() override {
            return std::make_pair(saved_read_timeout, saved_write_timeout); 
        }

    protected:
        int Write(const BYTE* data, DWORD data_length);
        // There is a char* version of Ftdi::Write, but it is still easier to do this:
        int Write(const char* data, DWORD data_length) {
            return Write(reinterpret_cast<const BYTE*>(data), data_length);
        }
        int Read(BYTE* buffer, DWORD buffer_length);
        // There is a char* version of Ftdi::Read, but it is still easier to do this:
        int Read(char* buffer, DWORD buffer_length) {
            return Read(reinterpret_cast<BYTE*>(buffer), buffer_length);
        }

    private:
        Type type;
        friend class Controller;
        bool OpenByIndex();
        void OpenBySerialNumber();
        void OpenIfNeeded();
        template <typename Func>
        void OpenAndTry(Func func) {
            OpenIfNeeded();
            try {
                func();
            } catch (HardwareError&) {
                Close();
                throw;
            }
        }
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
        ULONG saved_read_timeout = 100;
        ULONG saved_write_timeout = 50;
        bool collect_was_read = true;
        // We are making two assumptions here that are not guaranteed by the standard:
        // 1. Reads and writes are atomic on bool (true "everywhere" in C++)
        // 2. 'volatile' makes cache coherency issues go away (true on all versions of Windows)
        // To be totally correct, we should use a mutex or interlock whenever we touch these in
        // a multithreaded context, but practically speaking it isn't necessary so we opt out
        // of the needed overhead.
        volatile bool abort_read = false;
        volatile bool is_reading = false;
    };
}

