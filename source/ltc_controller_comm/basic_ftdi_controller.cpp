#include "basic_ftdi_controller.hpp"
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

void BasicFtdiController::Flush() {
    SetTimeouts(50);
    BYTE z = 'Z';
    Write(&z, 1);
    const int NUM_TO_READ = 64;
    BYTE      buffer[NUM_TO_READ];
    int       num_read;
    do { num_read = Read(buffer, NUM_TO_READ); } while (num_read == NUM_TO_READ);
    SetTimeouts();
}

void BasicFtdiController::Reset() {
    const int NUM_DATA       = 8;
    BYTE      data[NUM_DATA] = { 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, '\n' };
    bool      success        = false;
    for (int i = 0; i < 3; ++i) {
        OpenIfNeeded();
        SetTimeouts(300);

        // the first time around, we send 8 chars, the second 264. This is so that the DC890
        // will respond even if reading a RAM load (256-char blocks)
        int num_sends = 1;
        if (i > 0) { num_sends = 33; }
        for (int j = 0; j < num_sends; ++j) { Write(data, NUM_DATA); }

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
        DWORD unused            = 0;
        ftdi.GetStatus(handle, &num_receive_bytes, &unused, &unused);

        for (int j = 0; num_receive_bytes < 6 && j < 3; j++) {
            sleep_for(milliseconds(100));
            ftdi.GetStatus(handle, &num_receive_bytes, &unused, &unused);
        }

        char hello_string[7] = "\0\0\0\0\0\0";
        Read(hello_string, 6);

        SetTimeouts();

        if (strcmp("hello\n", hello_string) == 0) {
            success = true;
        } else {
            Close();
        }
    }
    if (!success) { throw HardwareError("Reset failed"); }
}

void BasicFtdiController::EepromReadString(char* buffer, int buffer_size) {
    const int EEPROM_SIZE = Ftdi::EEPROM_ID_STRING_SIZE;  // get around gcc weirdness
    Write("I\n", 2);
    buffer_size                                 = std::min(EEPROM_SIZE, buffer_size);
    auto num_read                               = Read(buffer, buffer_size);
    buffer[std::min(num_read, EEPROM_SIZE - 1)] = '\0';
    if (num_read != buffer_size) {
        Close();
        throw HardwareError("Not all EEPROM bytes received.");
    } else if (num_read != EEPROM_SIZE) {
        Flush();
    }
}

void BasicFtdiController::Close() {
    if (handle != nullptr) {
        ftdi.Close(handle);
        handle = nullptr;
    }
}

bool BasicFtdiController::OpenByIndex() {
    ftdi.OpenByIndex(index, &handle);
    FT_DEVICE device;
    DWORD     id;
    char      serial_number[LCC_MAX_SERIAL_NUMBER_SIZE];
    char      description[LCC_MAX_DESCRIPTION_SIZE];
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

void BasicFtdiController::OpenBySerialNumber() {
    ftdi.OpenBySerialNumber(serial_number.c_str(), &handle);
}

void BasicFtdiController::OpenIfNeeded() {
    if (handle != nullptr) { return; }

    auto is_same = OpenByIndex();
    if (!is_same) {
        auto info_list = ftdi.ListControllers(narrow<int>(GetType()), 100);
        for (auto info_iter = info_list.begin(); info_iter != info_list.end(); ++info_iter) {
            if (info_iter->type == FT_DEVICE_BM &&
                (serial_number.substr(0, serial_number.size() - 1) == info_iter->serial_number) &&
                (description == info_iter->description)) {
                index = info_iter->id;
                OpenIfNeeded();
                return;
            }
        }
    }
    SetTimeouts();
    ftdi.EnableEventChar(handle);
}
}