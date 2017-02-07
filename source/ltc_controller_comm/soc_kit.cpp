#include <chrono>
#include <thread>
#include <Winsock2.h>
#include "soc_kit.hpp"

namespace linear {

    using namespace std::chrono_literals;

    typedef std::vector<uint8_t> Uint8Vec;
    typedef std::vector<uint32_t> Uint32Vec;

    static const uint32_t CHUNK_SIZE = 1 * 1024 * 2014;

    void SocKit::DataStartCollect(int total_samples, Trigger trigger) {
        WriteRegister(NUM_SAMPLES_BASE, total_samples);
        WriteRegister(CONTROL_BASE, CW_START);

        std::this_thread::sleep_for(100ms);

        WriteRegister(CONTROL_BASE, CW_EN_TRIG | CW_START);
        WriteRegister(CONTROL_BASE, CW_EN_TRIG);
        is_start_address_current = false;
        num_samples = total_samples;
    }

    bool SocKit::DataIsCollectDone() {
        if (!is_start_address_current) {
            if ((ReadRegister(DATA_READY_BASE) & 0x01) != 0) {
                is_start_address_current = true;
                WriteRegister(CONTROL_BASE, 0x00);
                auto stopaddress = ReadRegister(BUFFER_ADDRESS_BASE);
                start_address = stopaddress - num_samples * sizeof(uint32_t);
            }
        }
        return is_start_address_current;
    }
    void SocKit::DataCancelCollect() {
        WriteRegister(CONTROL_BASE, 0x00);
        is_start_address_current = false;
    }

    int SocKit::DataReceive(uint8_t data[], int total_bytes) {
        return ReceiveAdcData(reinterpret_cast<uint32_t*>(data), total_bytes / 2) * 
            sizeof(uint32_t);
    }
    int SocKit::DataReceive(uint16_t data[], int total_values) {
        return ReceiveAdcData(reinterpret_cast<uint32_t*>(data), total_values / 2) * 
            sizeof(uint32_t);
    }
    int SocKit::DataReceive(uint32_t data[], int total_values) {
        return ReceiveAdcData(data, total_values) * sizeof(uint32_t);
    }

    int SocKit::ReceiveAdcData(uint32_t values[], uint32_t num_values) {
        if (!is_start_address_current) {
            throw HardwareError(
                "Tried to read without a successful data capture, use DataIsCollectDone.");
        }
        if (num_values > num_samples) {
            num_values = num_samples;
        }
        auto result = ReadMemoryBlock(start_address, values, num_values);
        start_address += result;
        return result;
    }

    uint32_t SocKit::Read(uint32_t command, uint32_t address) {
        auto begin = reinterpret_cast<uint8_t*>(&address);
        auto packet = Packet::with_command(command, Uint8Vec{ begin, begin + sizeof(uint32_t) });
        packet = SendAndReceivePacket(packet);
        if (packet.payload.size() != sizeof(uint32_t)) {
            throw HardwareError("Unexpected payload size in packet");
        }
        return ToUint32(packet.payload.data());
    }

    int SocKit::ReadChunk(uint32_t command, uint32_t address, uint32_t values[], uint32_t num_values) {
        if (num_values > CHUNK_SIZE) {
            throw logic_error("Chunk Size too large");
        }
        uint32_t payload[] = { address, num_values };
        auto packet = Packet::with_command(command, ToUint8Vec(payload, 2));
        packet = SendAndReceivePacket(packet);
        for (uint32_t i = 0; i < packet.payload.size(); ++i) {
            values[i] = ntohl(packet.payload[i]);
        }
        return narrow<int>(packet.payload.size());
    }

    int SocKit::ReadBlock(uint32_t command, uint32_t address, uint32_t values[], uint32_t num_values) {
        while (num_values > 0) {
            auto num_chunk_values = num_values > CHUNK_SIZE ? CHUNK_SIZE : num_values;
            auto num_read = ReadChunk(command, address, values, num_chunk_values);
            values += num_read;
            num_values -= num_read;
        }
        return num_values;
    }

    void SocKit::Write(uint32_t command, uint32_t address, uint32_t value) {
        uint32_t payload[] = { address, value };
        auto packet = Packet::with_command(command, ToUint8Vec(payload, 2));
        SendAndReceivePacket(packet);
    }

    void SocKit::WriteChunk(uint32_t command, uint32_t address,
                            const uint32_t values[], uint32_t num_values) {
        uint32_t data_size = num_values * sizeof(uint32_t);
        Uint8Vec payload;
        payload.reserve(sizeof(uint32_t) + data_size);

        auto begin = reinterpret_cast<const uint8_t*>(&address);
        payload.insert(payload.end(), begin, begin + sizeof(address));

        begin = reinterpret_cast<const uint8_t*>(values);
        payload.insert(payload.end(), begin, begin + data_size);

        SwapBytesUint32(payload.data(), narrow<uint32_t>(payload.size()));
        SendAndReceivePacket(Packet::with_command(command, payload));
    }

    void SocKit::WriteBlock(uint32_t command, uint32_t address,
                            const uint32_t values[], uint32_t num_values) {
        while (num_values > 0) {
            auto num_chunk_values = num_values > CHUNK_SIZE ? CHUNK_SIZE : num_values;
            WriteChunk(command, address, values, num_chunk_values);
            num_values -= num_chunk_values;
            values += num_chunk_values;
        }
    }

    void SocKit::Shutdown() {
        constexpr uint32_t SHUTDOWN_PAYLOAD = "HALT"_as_u32;
        auto packet = Packet::with_command(Packet::SHUTDOWN, ToUint8Vec(&SHUTDOWN_PAYLOAD, 1));
        SendPacket(packet, TcpClientSocket(ip_address, PORT));
    }

    static const int MIN_PACKET_SIZE = 2 * sizeof(uint32_t);

    void SocKit::SendPacket(Packet packet, TcpClientSocket& client_socket) {
        Uint8Vec bytes;
        bytes.reserve(MIN_PACKET_SIZE + packet.payload.size());

        auto command_bytes = reinterpret_cast<uint8_t*>(&packet.command_word);
        for (int i = 0; i < sizeof(packet.command_word); ++i) {
            bytes.push_back(command_bytes[i]);
        }
        auto size = narrow<uint32_t>(packet.payload.size()) + MIN_PACKET_SIZE;
        auto size_bytes = reinterpret_cast<uint8_t*>(&size);
        for (int i = 0; i < sizeof(packet.command_word); ++i) {
            bytes.push_back(size_bytes[i]);
        }
        bytes.insert(bytes.end(), packet.payload.begin(), packet.payload.end());
        client_socket.send(bytes.data(), narrow<int>(bytes.size()));
    }

    Packet SocKit::SendAndReceivePacket(Packet packet) {
        TcpClientSocket client_socket(ip_address, PORT);
        SendPacket(packet, client_socket);
        auto response_command_and_size = client_socket.receive(MIN_PACKET_SIZE);

        auto command = ToUint32(response_command_and_size.data());
        auto size = ToUint32(response_command_and_size.data() + sizeof(uint32_t));

        size -= MIN_PACKET_SIZE;
        if (size > 0) {
            auto payload = client_socket.receive(size);
            return Packet(command, payload).check(packet.command_word);
        } else {
            return Packet(command, Uint8Vec()).check(packet.command_word);
        }
    }

    std::vector<uint8_t> SocKit::ToUint8Vec(const uint32_t values[], int num_values) {
        auto byte_pointer = reinterpret_cast<const uint8_t*>(values);
        return Uint8Vec{ byte_pointer, byte_pointer + num_values * sizeof(uint32_t) };
    }
}
