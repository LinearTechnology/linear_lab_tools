#pragma once
#include "basic_ftdi_controller.hpp"
#include "i_collect.hpp"
#include "i_data_endian.hpp"
#include "i_data_receive.hpp"

namespace linear {

using std::string;
using std::vector;

class FtdiAdc : public BasicFtdiController,
                public ICollect,
                public IDataEndian,
                public IDataReceive {
   public:
    FtdiAdc(const Ftdi& ftdi, const LccControllerInfo& info) : BasicFtdiController(ftdi, info) {}
    virtual ~FtdiAdc() {}

    void DataSetCharacteristics(bool is_multiple_channels,
                                int  bytes_per_sample,
                                bool is_positive_clock) {
        is_multichannel = is_multiple_channels;
        if (bytes_per_sample < 2 || bytes_per_sample > 4) {
            throw invalid_argument("bytes_per_sample must be between 2 and 4");
        }
        sample_bytes                = bytes_per_sample;
        is_sampled_on_positive_edge = is_positive_clock;
    }
    void DataStartCollect(int total_samples, Trigger trigger) override;
    bool DataIsCollectDone() override;
    void DataCancelCollect() override;
    void DataSetHighByteFirst() override { swap_bytes = true; }
    void DataSetLowByteFirst() override { swap_bytes = false; }

    int DataReceive(uint8_t data[], int num_bytes) override { return ReadBytes(data, num_bytes); }
    int DataReceive(uint16_t data[], int num_values) override {
        return Controller::DataRead(*this, swap_bytes, data, num_values);
    }
    int DataReceive(uint32_t data[], int num_values) override {
        return Controller::DataRead(*this, swap_bytes, data, num_values);
    }

    void Reset() override {
        collect_was_read = true;
        BasicFtdiController::Reset();
    }

    Controller::Type GetType() override { return BasicFtdiController::GetType(); }
    string           GetDescription() override { return BasicFtdiController::GetDescription(); }
    string           GetSerialNumber() override { return BasicFtdiController::GetSerialNumber(); }
    void             EepromReadString(char* buffer, int buffer_size) override {
        return BasicFtdiController::EepromReadString(buffer, buffer_size);
    }

   private:
    friend class Controller;
    int  ReadBytes(uint8_t data[], int total_bytes);
    bool swap_bytes                  = true;
    bool is_sampled_on_positive_edge = true;
    int  sample_bytes                = 0;
    bool is_multichannel             = false;
    bool collect_was_read            = true;
};
}
