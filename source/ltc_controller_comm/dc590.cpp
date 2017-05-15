#include "dc590.hpp"

namespace linear {

void Dc590::SpiSend(uint8_t values[], int num_values) {
    string send_str;
    send_str.reserve(3 * num_values + 2);
    send_str += 'x';
    for (int i = 0; i < num_values; ++i) {
        send_str += 'S';
        send_str += ToHex(values[i]);
    }
    send_str += 'X';
    Write(send_str.c_str(), send_str.size());
}
void Dc590::SpiReceive(uint8_t values[], int num_values) {
    string send_str(num_values + 2, 'R');
    send_str[0]              = 'x';
    send_str[num_values + 1] = 'X';
    Write(send_str.c_str(), send_str.size());
    vector<char> recv_str(num_values * 2);
    auto         num_recv = Read(&recv_str[0], recv_str.size());
    if (num_recv / 2 < num_values) { num_values = num_recv / 2; }
    HexToBytes(recv_str.data(), values, num_values);
}
void Dc590::SpiTransceive(uint8_t send_values[], uint8_t receive_values[], int num_values) {
    string send_str;
    send_str.reserve(3 * num_values + 1 + 2);  // Z, x, X
    send_str += 'x';
    for (int i = 0; i < num_values; ++i) {
        send_str += 'S';
        send_str += ToHex(send_values[i]);
    }
    send_str += 'X';
    send_str += 'Z';
    Write(send_str.c_str(), send_str.size());
    vector<char> recv_str(num_values * 2 + 1);
    auto         num_recv = Read(&recv_str[0], recv_str.size()) - 1;
    if (num_recv / 2 < num_values) { num_values = num_recv / 2; }
    HexToBytes(recv_str.data() + 1, receive_values, num_values);
}

void Dc590::SpiSendAtAddress(uint8_t address, uint8_t* values, int num_values) {
    vector<uint8_t> data;
    data.reserve(num_values + 1);
    data[0] = address;
    for (int i = 0; i < num_values; ++i) { data[i + 1] = values[i]; }
    SpiSend(data.data(), data.size());
}
void Dc590::SpiSendAtAddress(uint8_t address, uint8_t value) {
    SpiSendAtAddress(address, &value, 1);
}
void Dc590::SpiReceiveAtAddress(uint8_t address, uint8_t* values, int num_values) {
    SpiSetCsState(SpiCsState::LOW);
    SpiSendNoChipSelect(&address, 1);
    SpiReceiveNoChipSelect(values, num_values);
    SpiSetCsState(SpiCsState::HIGH);
}
uint8_t Dc590::SpiReceiveAtAddress(uint8_t address) {
    uint8_t send[2];
    send[0] = address;
    send[1] = 0;
    uint8_t recv[2];
    SpiTransceive(send, recv, 2);
    return recv[1];
}

void Dc590::SpiSetCsState(SpiCsState chip_select_state) {
    char x = chip_select_state == SpiCsState::HIGH ? 'X' : 'x';
    Write(&x, 2);
}
void Dc590::SpiSendNoChipSelect(uint8_t values[], int num_values) {
    string send_str;
    send_str.reserve(3 * num_values);
    for (int i = 0; i < num_values; ++i) {
        send_str += 'S';
        send_str += ToHex(values[i]);
    }
    Write(send_str.c_str(), send_str.size());
}
void Dc590::SpiReceiveNoChipSelect(uint8_t values[], int num_values) {
    string send_str(num_values, 'R');
    Write(send_str.c_str(), send_str.size());
    vector<char> recv_str(num_values * 2);
    auto         num_recv = Read(&recv_str[0], recv_str.size());
    if (num_recv / 2 < num_values) { num_values = num_recv / 2; }
    HexToBytes(recv_str.data(), values, num_values);
}
void Dc590::SpiTransceiveNoChipSelect(uint8_t send_values[],
                                      uint8_t receive_values[],
                                      int     num_values) {
    string send_str;
    send_str.reserve(3 * num_values + 1);
    for (int i = 0; i < num_values; ++i) {
        send_str += 'S';
        send_str += ToHex(send_values[i]);
    }
    send_str += 'Z';
    Write(send_str.c_str(), send_str.size());
    vector<char> recv_str(num_values * 2 + 1);
    auto         num_recv = Read(&recv_str[0], recv_str.size()) - 1;
    if (num_recv / 2 < num_values) { num_values = num_recv / 2; }
    HexToBytes(recv_str.data() + 1, receive_values, num_values);
}

void Dc590::SetEventChar(bool enable) { ftdi.EnableEventChar(handle, enable); }
}