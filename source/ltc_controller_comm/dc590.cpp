#include "dc590.hpp"

namespace linear {

inline static void ThrowOnMissingData(bool is_send, int num_expected, int num_actual) {
    if (num_expected != num_actual) {
        auto message = string("Tried to ") + (is_send ? "send" : "receive") +
                       std::to_string(num_expected) + " bytes, " + (is_send ? "sent" : "got") +
                       std::to_string(num_actual);
        throw HardwareError(message);
    }
}

inline void Dc590::WriteThenReadBytes(const string& send_str, uint8_t values[], int num_values) {
    int num_sent = Write(send_str.c_str(), send_str.size());
    ThrowOnMissingData(true, send_str.size(), num_sent);

    vector<char> recv_str(num_values * 2 + 1);  // +1 for newline due to Z

    int num_recv = Read(&recv_str[0], recv_str.size());
    ThrowOnMissingData(false, recv_str.size(), num_recv);

    HexToBytes(recv_str.data(), values, num_values);
}

void Dc590::SpiSend(uint8_t values[], int num_values) {
    string send_str = "X";
    send_str.reserve(3 * num_values + 2);
    for (int i = 0; i < num_values; ++i) {
        send_str += 'S';
        send_str += ToHex(values[i]);
    }
    send_str += 'X';

    int num_sent = Write(send_str.c_str(), send_str.size());
    ThrowOnMissingData(true, send_str.size(), num_sent);
}

void Dc590::SpiReceive(uint8_t values[], int num_values) {
    WriteThenReadBytes("x" + string(num_values, 'R') + "XZ", values, num_values);
}

void Dc590::SpiTransceive(uint8_t send_values[], uint8_t receive_values[], int num_values) {
    string send_str = "x";
    send_str.reserve(3 * num_values + 1 + 2);  // Z, x, X
    for (int i = 0; i < num_values; ++i) {
        send_str += 'T';
        send_str += ToHex(send_values[i]);
    }
    send_str += "XZ";

    WriteThenReadBytes(send_str, receive_values, num_values);
}

void Dc590::SpiSendAtAddress(uint8_t address, uint8_t values[], int num_values) {
    vector<uint8_t> data;
    data.reserve(num_values + 1);
    data[0] = address;
    data.insert(data.end(), values, values + num_values);
    SpiSend(data.data(), data.size());
}

void Dc590::SpiReceiveAtAddress(uint8_t address, uint8_t values[], int num_values) {
    WriteThenReadBytes("xS" + ToHex(address) + string(num_values, 'R') + "XZ", values, num_values);
}

void Dc590::SpiSetCsState(SpiCsState chip_select_state) {
    char x = chip_select_state == SpiCsState::HIGH ? 'X' : 'x';

    int num_sent = Write(&x, 1);
    ThrowOnMissingData(true, 1, num_sent);
}

void Dc590::SpiSendNoChipSelect(uint8_t values[], int num_values) {
    string send_str;
    send_str.reserve(3 * num_values);
    for (int i = 0; i < num_values; ++i) {
        send_str += 'S';
        send_str += ToHex(values[i]);
    }

    int num_sent = Write(send_str.c_str(), send_str.size());
    ThrowOnMissingData(true, send_str.size(), num_sent);
}

void Dc590::SpiReceiveNoChipSelect(uint8_t values[], int num_values) {
    WriteThenReadBytes(string(num_values, 'R') + 'Z', values, num_values);
}

void Dc590::SpiTransceiveNoChipSelect(uint8_t send_values[],
                                      uint8_t receive_values[],
                                      int     num_values) {
    string send_str;
    send_str.reserve(3 * num_values + 1);
    for (int i = 0; i < num_values; ++i) {
        send_str += 'T';
        send_str += ToHex(send_values[i]);
    }
    send_str += 'Z';

    WriteThenReadBytes(send_str, receive_values, num_values);
}

void Dc590::SetEventChar(bool enable) { ftdi.EnableEventChar(handle, enable); }
}