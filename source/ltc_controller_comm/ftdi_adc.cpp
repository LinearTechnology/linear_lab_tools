#include "ftdi_adc.hpp"
#include <chrono>
#include <thread>

using std::string;
using std::to_string;
using std::this_thread::sleep_for;
using std::chrono::milliseconds;

#ifdef min
#undef min
#endif

namespace linear {
const int MAX_CONTROLLER_BYTES = 512 * 1024;

void FtdiAdc::DataStartCollect(int total_samples, Trigger trigger) {
    ASSERT_NOT_SMALLER(sample_bytes, 2);
    int sample_multiplier = 1;
    if (GetType() == Type::DC718) {
        ASSERT_NOT_LARGER(sample_bytes, 3);
    } else {
        ASSERT_NOT_LARGER(sample_bytes, 8);
        sample_multiplier = sample_bytes / 2;
    }
    ASSERT_NOT_SMALLER(total_samples, 1024);
    auto total_bytes = sample_bytes * total_samples;
    ASSERT_NOT_LARGER(total_bytes, MAX_CONTROLLER_BYTES);
    if (total_samples % 1024 != 0) {
        throw invalid_argument("total_samples must be a multiple of 1024");
    }
    int trigger_value;
    switch (trigger) {
        case Trigger::NONE:
            trigger_value = LCC_TRIGGER_NONE;
            break;
        case Trigger::START_POSITIVE_EDGE:
            trigger_value = LCC_TRIGGER_START_POSITIVE_EDGE;
            break;
        case Trigger::DC890_START_NEGATIVE_EDGE:
            trigger_value = LCC_TRIGGER_DC890_START_NEGATIVE_EDGE;
            break;
        default:
            throw invalid_argument(
                    "trigger must be NONE, START_ON_POSITIVE_EDGE or "
                    "DC890_START_ON_NEGATIVE_EDGE.");
    }

    if (sample_bytes == 0) {
        throw invalid_argument(
                "SetDataCharacteristics must be called before calling DataStartCollect");
    }

    char buffer[100];
    safe_sprintf(buffer, "T %d\nL %d\nD %d\nW %c\nH %d\nC\n", trigger_value,
                 total_samples * sample_multiplier, sample_bytes > 2 ? 2 : 1,
                 is_sampled_on_positive_edge ? '+' : '-', is_multichannel ? 1 : 0);

    Write(buffer, narrow<DWORD>(strlen(buffer)));
    collect_was_read = false;
}

bool FtdiAdc::DataIsCollectDone() {
    char buffer[4] = "\0\0\0";
    auto num_read  = Read(buffer, sizeof(buffer));
    if (num_read == 0) {
        return false;
    } else if (strcmp(buffer, "ACK") == 0) {
        return true;
    } else {
        throw HardwareError("Got an unexpected response while checking for ACK.");
    }
}

void FtdiAdc::DataCancelCollect() { Reset(); }

int FtdiAdc::ReadBytes(uint8_t data[], int num_bytes) {
    const int MAX_BYTES_READ = 4 * 1024;

    if (!collect_was_read) {
        collect_was_read         = true;
        const char* read_command = is_multichannel ? "S 1\n" : "R 0\n";
        Write(read_command, narrow<DWORD>(strlen(read_command)));
    }

    ftdi.DisableEventChar(handle);
    SetTimeouts(1000);
    int total_read = 0;
    while (num_bytes > 0) {
        auto chunk_bytes = std::min(MAX_BYTES_READ, num_bytes);
        auto num_read    = Read(data, chunk_bytes);
        if (num_read != chunk_bytes) {
            Close();
            throw HardwareError("Tried to read " + std::to_string(chunk_bytes) + " bytes, got " +
                                std::to_string(num_read) + ".");
        }
        data += chunk_bytes;
        total_read += chunk_bytes;
        num_bytes -= chunk_bytes;
    }
    ftdi.EnableEventChar(handle);
    SetTimeouts();
    return total_read;
}
}