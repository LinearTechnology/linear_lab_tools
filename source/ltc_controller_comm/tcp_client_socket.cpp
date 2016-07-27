#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <winsock2.h>
#include <ws2tcpip.h>
#include <stdexcept>
#include <sstream>
#include <string>

#include "tcp_client_socket.hpp"
#include "../ltc_controller_comm/error.hpp"
#include "../ltc_controller_comm/utilities.hpp"

// Need to link with Ws2_32.lib, Mswsock.lib, and Advapi32.lib
#pragma comment (lib, "Ws2_32.lib")
#pragma comment (lib, "Mswsock.lib")
#pragma comment (lib, "AdvApi32.lib")

namespace linear {
    struct TcpClientSocket::Impl {
        WSADATA wsa_data;
        SOCKET native_socket = INVALID_SOCKET;
    };

    static void throw_message_and_code(const char* message, int code) {
        std::stringstream error_ss;
        error_ss << message << " with error: " << code;
        auto error_s = error_ss.str();
        throw HardwareError(error_s.c_str());
    }

    TcpClientSocket::TcpClientSocket(const char* url_or_ip, int port) :
            pimpl(std::make_unique<Impl>()) {
        init(url_or_ip, port);
    }

    TcpClientSocket::TcpClientSocket(uint32_t ip, uint32_t port) :
            pimpl(std::make_unique<Impl>()) {
        std::stringstream ss;
        ss << (ip >> 24) << '.' << ((ip >> 16) & 0xFF) << '.' << ((ip >> 8) & 0xFF) << '.' << (ip & 0xFF);
        init(ss.str().c_str(), port);
    }

    TcpClientSocket::~TcpClientSocket() {
        auto result = shutdown(pimpl->native_socket, SD_BOTH);
        closesocket(pimpl->native_socket);
        WSACleanup();
    }

    void TcpClientSocket::init(const char* url_or_ip, int port) {
        auto wsa_data = pimpl->wsa_data;
        auto result = WSAStartup(MAKEWORD(2, 2), &wsa_data);
        if (result != 0) {
            throw_message_and_code("WSAStartup failed", result);
        }

        addrinfo hints;
        ZeroMemory(&hints, sizeof(hints));
        hints.ai_family = AF_UNSPEC;
        hints.ai_socktype = SOCK_STREAM;
        hints.ai_protocol = IPPROTO_TCP;

        addrinfo* address_info;
        auto port_str = std::to_string(port);
        result = getaddrinfo(url_or_ip, port_str.c_str(), &hints, &address_info);
        if (result != 0) {
            WSACleanup();
            throw_message_and_code("getaddrinfo failed", result);
        }

        for (auto ptr = address_info; ptr != nullptr; ptr = ptr->ai_next) {
            pimpl->native_socket = socket(ptr->ai_family, ptr->ai_socktype, ptr->ai_protocol);
            if (pimpl->native_socket == INVALID_SOCKET) {
                WSACleanup();
                throw_message_and_code("socket failed", WSAGetLastError());
            }

            result = connect(pimpl->native_socket, ptr->ai_addr, (int)ptr->ai_addrlen);
            if (result == SOCKET_ERROR) {
                closesocket(pimpl->native_socket);
                pimpl->native_socket = INVALID_SOCKET;
                continue;
            }
            break;
        }
        freeaddrinfo(address_info);

        if (pimpl->native_socket == INVALID_SOCKET) {
            WSACleanup();
            throw std::runtime_error("Unable to connect to server");
        }
    }

    void TcpClientSocket::send(const uint8_t* bytes, int num_to_write) {
        auto result = ::send(pimpl->native_socket, (const char*)bytes, num_to_write, 0);
        if (result == SOCKET_ERROR) {
            throw_message_and_code("send failed", WSAGetLastError());
        }
    }

    void TcpClientSocket::send_str(const char* str) {
        auto result = ::send(pimpl->native_socket, str, Narrow<int>(strlen(str)), 0);
        if (result == SOCKET_ERROR) {
            throw_message_and_code("send failed", WSAGetLastError());
        }
    }

    std::vector<uint8_t> TcpClientSocket::receive(int num_to_read) {
        std::vector<uint8_t> bytes;
        bytes.resize(num_to_read);
        size_t offset = 0;
        while (num_to_read > 0) {
            auto result = recv(pimpl->native_socket,
                               reinterpret_cast<char*>(bytes.data() + offset), num_to_read, 0);
            if (result > 0) {
                num_to_read -= result;
                offset += result;
            } else if (result == 0) {
                bytes.resize(offset);
                break;
            } else {
                throw_message_and_code("receive failed", WSAGetLastError());
            }
        }
        return bytes;
    }

    std::string TcpClientSocket::receive_str(int num_to_read) {
        return std::string(reinterpret_cast<const char*>(receive(num_to_read).data()));
    }
}
