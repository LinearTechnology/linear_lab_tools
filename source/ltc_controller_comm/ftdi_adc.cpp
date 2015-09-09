#include <chrono>
#include <thread>
#include "ftdi_adc.hpp"

using std::string;
using std::to_string;
using std::this_thread::sleep_for;
using std::chrono::milliseconds;

namespace linear {
    const int MAX_CONTROLLER_BYTES_PER_CHANNEL = 128 * 1024;
    const int MAX_CONTROLLER_BYTES = 2 * MAX_CONTROLLER_BYTES_PER_CHANNEL;

    void FtdiAdc::DataStartCollect(int total_bytes, Trigger trigger) {
        MUST_NOT_BE_SMALLER(total_bytes, 1024);
        if (is_multichannel) {
            MUST_NOT_BE_LARGER(total_bytes, MAX_CONTROLLER_BYTES);
        } else {
            MUST_NOT_BE_LARGER(total_bytes, MAX_CONTROLLER_BYTES_PER_CHANNEL);
        }
        if (total_bytes % 1024 != 0) {
            throw invalid_argument("total_bytes must be a multiple of 1024");
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
                "trigger must be NONE, START_ON_POSITIVE_EDGE or DC890_START_ON_NEGATIVE_EDGE.");
        }

        char buffer[100];
        sprintf_s(buffer, "T %d\nL %d\nD %d\nW %c\nH %d\nC\n", trigger_value, total_bytes,
            is_wide_samples ? 2 : 1, is_sampled_on_positive_edge ? '+' : '-',
            is_multichannel ? 1 : 0);
        Write(buffer, strlen(buffer));
    }
    bool FtdiAdc::DataIsCollectDone() {
        char buffer[4] = "\0\0\0";
        auto num_read = Read(buffer, sizeof(buffer));
        if (num_read == 0) {
            return false;
        } else if (strcmp(buffer, "ACK") == 0) {
            return true;
        } else {
            throw HardwareError("Got an unexpected response while checking for ACK.");
        }
    }

    void FtdiAdc::Flush() {
        // set timeout, but remember saved timeout
        auto timeout = saved_read_timeout;
        SetTimeouts(50, saved_write_timeout);
        saved_read_timeout = timeout;

        BYTE z = 'Z';
        Write(&z, 1);
        const int NUM_TO_READ = 64;
        BYTE buffer[NUM_TO_READ];
        int num_read;
        do {
            num_read = Read(buffer, NUM_TO_READ);
        } while (num_read == NUM_TO_READ);
        SetTimeouts(saved_read_timeout, saved_write_timeout);
    }

    void FtdiAdc::Reset() {
        OpenIfNeeded();
        try {
            // don't use the public SetTimeouts because we want to preserve the saved timeout values
            // so if any thing goes wrong the user gets the expected timeout when they reconnect.
            ftdi.SetTimeouts(handle, 300, 50);

            const int NUM_DATA = 8;
            BYTE data[NUM_DATA] = { 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, '\n' };
            for (int i = 0; i < 3; ++i) {
                // the first time around, we send 8 chars, the second 264. This is so that the DC890
                // will respond even if reading a RAM load (256-char blocks)
                int num_sends = 1;
                if (i > 0) {
                    num_sends = 33;
                }
                for (int j = 0; j < num_sends; ++j) {
                    Write(data, NUM_DATA);
                }

                // RESET
                // This purge clears the downstream FIFO while the PIC is asleep,
                // causing the  hardware to reset the PIC
                ftdi.Purge(handle, FT_PURGE_TX | FT_PURGE_RX);

                // now send a NOOP as a work-around for the FTDI bug which causes a single char to be
                // lost after a purge. I think this bug is actually fixed now.
                BYTE noop = 0x81;
                Write(&noop, 1);

                // the PIC has an internal reset timeout - wait it out
                sleep_for(milliseconds(300));

                // we should have 6 chars ("hello\n") in the input buff.
                // If not all there, delay 100ms and try again. We repeat 6
                // times to give FastDAAQS a chance to load FPGA
                DWORD num_receive_bytes = 0;
                DWORD unused = 0;
                ftdi.GetStatus(handle, &num_receive_bytes, &unused, &unused);

                for (int j = 0; num_receive_bytes < 6 && j < 3; j++) {
                    sleep_for(milliseconds(100));
                    ftdi.GetStatus(handle, &num_receive_bytes, &unused, &unused);
                }

                char hello_string[7] = "\0\0\0\0\0\0";
                Read(hello_string, 6);

                SetTimeouts(saved_read_timeout, saved_write_timeout);

                if (strcmp("hello\n", hello_string) != 0)
                    throw HardwareError("Reset failed");
            }
        } catch (HardwareError) {
            Close();
            throw;
        }
    }

    void FtdiAdc::DataCancelCollect() {
        Reset();
    }
    
    int FtdiAdc::ReadBytes(uint8_t data[], int total_bytes) {
        const char* read_command = is_multichannel ? "S 1\n" : "R 0\n";
        Write(read_command, strlen(read_command));

        const int MAX_BYTES_READ = 2 * 1024;
        static BYTE buffer[MAX_BYTES_READ];

        // set timeout, but remember saved timeout
        auto timeout = saved_read_timeout;
        SetTimeouts(1000, saved_write_timeout);
        saved_read_timeout = timeout;
        int total_read = 0;
        while (total_bytes > 0) {
            auto num_bytes = Min(MAX_BYTES_READ, total_bytes);
            auto num_read = Read(buffer, num_bytes);
            if (num_read != num_bytes) {
                throw HardwareError("Tried to read " + std::to_string(num_bytes) + " bytes, got " +
                    std::to_string(num_read) + ".");
            }
            memcpy_s(data, total_bytes, buffer, num_bytes);
            data += num_bytes;
            total_read += num_bytes;
            total_bytes -= num_bytes;
        }

        SetTimeouts(saved_read_timeout, saved_write_timeout);
        return total_read;
    }

    void FtdiAdc::DataCancelReceive() {
        abort_read = true;
        int i;
        for (i = 0; is_reading && i < 1000; ++i) {
            sleep_for(milliseconds(5));
        }
        abort_read = false;
        if (i == 1000) {
            try {
                Reset();
            } catch (...) { }
            Close();
            throw HardwareError("Abort operation timed out.");
        } else {
            Reset();
        }
    }

    void FtdiAdc::EepromReadString(char* buffer, int buffer_size) {
        Write("I\n", 2);
        buffer_size = Min(Ftdi::EEPROM_ID_STRING_SIZE, buffer_size);
        auto num_read = Read(buffer, buffer_size);
        if (num_read != buffer_size) {
            Close();
            throw HardwareError("Not all EEPROM bytes received.");
        } else if (num_read != Ftdi::EEPROM_ID_STRING_SIZE) {
            Flush();
        }
    }

    void FtdiAdc::Close() {
        if (handle != nullptr) {
            ftdi.Close(handle);
            handle = nullptr;
        }
    }

    bool FtdiAdc::OpenByIndex() {
        ftdi.OpenByIndex(index, &handle);
        FT_DEVICE device;
        DWORD id;
        char serial_number[LCC_MAX_SERIAL_NUMBER_SIZE];
        char description[LCC_MAX_DESCRIPTION_SIZE];
        try {
            ftdi.GetDeviceInfo(handle, &device, &id, serial_number, description);
            if (device != FT_DEVICE_BM || string(serial_number) != serial_number) {
                ftdi.Close(&handle);
                return false;
            }
            return true;
        } catch (...) {
            ftdi.Close(&handle);
            throw;
        }
    }

    void FtdiAdc::OpenBySerialNumber() {
        ftdi.OpenBySerialNumber(serial_number.c_str(), &handle);
    }

    void FtdiAdc::OpenIfNeeded() {
        if (handle != nullptr) { return; }

        auto is_same = OpenByIndex();
        if (!is_same) {
            auto info_list = ftdi.ListControllers(int(GetType()), 100);
            for (auto info_iter = info_list.begin(); info_iter != info_list.end(); ++info_iter) {
                if (info_iter->type == FT_DEVICE_BM &&
                    (serial_number.substr(0, serial_number.size() - 1) ==
                    info_iter->serial_number) && (description == info_iter->description)) {
                    index = info_iter->id;
                    return OpenIfNeeded();
                }
            }
        }
        SetTimeouts(saved_read_timeout, saved_write_timeout);
    }

    void FtdiAdc::SetTimeouts(ULONG read_timeout, ULONG write_timeout) {
        saved_read_timeout = read_timeout;
        saved_write_timeout = write_timeout;
        OpenAndTry([&]() { ftdi.SetTimeouts(handle, read_timeout, write_timeout); });
    }
    int FtdiAdc::Write(const BYTE* data, DWORD data_length) {
        int num_written;
        OpenAndTry([&]() { num_written = ftdi.Write(handle, data, data_length); });
        return num_written;
    }
    int FtdiAdc::Read(BYTE* buffer, DWORD buffer_length) {
        int num_read;
        OpenAndTry([&]() { num_read = ftdi.Read(handle, buffer, buffer_length); });
        return num_read;
    }
}