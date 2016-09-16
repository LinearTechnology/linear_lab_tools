#pragma once
#include <memory>
#include <vector>
#include <string>
#include <cstdint>

namespace linear {

    class TcpClientSocket {
    public:
        TcpClientSocket(const char* url_or_ip, int port);
        TcpClientSocket(uint32_t ip, uint32_t port);
        TcpClientSocket(TcpClientSocket&& other) = default;
        TcpClientSocket(const TcpClientSocket& other) = delete;
        ~TcpClientSocket();
        TcpClientSocket& operator = (TcpClientSocket&& other) = default;
        TcpClientSocket& operator = (const TcpClientSocket& other) = delete;

        void send(const uint8_t* bytes, int num_to_write);
        void send_str(const char* str);
        std::vector<uint8_t> receive(int num_to_read);
        std::string receive_str(int num_to_read);
    private:
        void init(const char* url_or_ip, int port);
        struct Impl;
        std::unique_ptr<Impl> pimpl;
    };

}