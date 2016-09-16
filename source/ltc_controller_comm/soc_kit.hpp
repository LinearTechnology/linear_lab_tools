#pragma once
#include <vector>
#include <string>
#include <cstdint>
#include "i_close.hpp"
#include "i_data_endian.hpp"
#include "i_data_send.hpp"
#include "i_data_receive.hpp"
#include "i_spi.hpp"
#include "i_collect.hpp"
#include "controller.hpp"
#include "tcp_client_socket.hpp"
#include "error.hpp"

namespace linear {

    using std::string;
    using std::vector;

    class Packet {
    public:
        static constexpr uint32_t REG_READ         = 0x01;
        static constexpr uint32_t REG_WRITE        = 0x02;
        static constexpr uint32_t MEM_READ         = 0x03;
        static constexpr uint32_t MEM_WRITE        = 0x04;
        static constexpr uint32_t REG_READ_BLOCK   = 0x05;
        static constexpr uint32_t REG_WRITE_BLOCK  = 0x06;
        static constexpr uint32_t MEM_READ_BLOCK   = 0x07;
        static constexpr uint32_t MEM_WRITE_BLOCK  = 0x08;
        static constexpr uint32_t MEM_TO_FILE      = 0x09;
        static constexpr uint32_t MEM_FROM_FILE    = 0x0A;
        static constexpr uint32_t REG_WRITE_LUT    = 0x0B;
        static constexpr uint32_t IDENTIFY         = 0x0C;
        static constexpr uint32_t LOAD_FPGA        = 0x0D;
        static constexpr uint32_t SET_DEFAULT_FPGA = 0x0E;
        static constexpr uint32_t SEND_FILE        = 0x0F;

        static constexpr uint32_t SHUTDOWN         = 0x04'00;

        static constexpr uint32_t ERROR_BIT        = 0x80'00'00'00;
        static constexpr uint32_t COMMAND_BIT      = 0x40'00'00'00;
        static constexpr uint32_t RESPONSE_BIT     = 0x20'00'00'00;
        static constexpr uint32_t DUMMY_BIT        = 0x10'00'00'00;

        uint32_t command_word;
        std::vector<uint8_t> payload;

        Packet(uint32_t command_word, std::vector<uint8_t> payload) :
            command_word(command_word), payload(payload) { }

        Packet(const Packet& other) = default;
        Packet(Packet&& other) = default;
        Packet& operator=(const Packet& other) = default;
        ~Packet() = default;

        static Packet with_command(uint32_t command_word, const std::vector<uint8_t>& payload) {
            return Packet(command_word | COMMAND_BIT, payload);
        }

        Packet& check(uint32_t command_word) {
            if ((this->command_word & RESPONSE_BIT) == 0) {
                throw HardwareError("Not a response packet");
            } else if ((command_word & ~COMMAND_BIT) != (this->command_word & ~RESPONSE_BIT)) {
                throw HardwareError("Wrong command word");
            } else if ((this->command_word & ERROR_BIT) != 0) {
                throw HardwareError("Received error packet");
            }
            return *this;
        }
    };

    class SocKit : public IDataReceive, public ICollect {

    public:
        static const uint32_t EXPANDER_CTRL_BASE    = 0x00;
        static const uint32_t REV_ID_BASE           = 0x10;
        static const uint32_t CONTROL_BASE          = 0x20;
        static const uint32_t DATA_READY_BASE       = 0x30;
        static const uint32_t LED_BASE              = 0x40;
        static const uint32_t NUM_SAMPLES_BASE      = 0x50;
        static const uint32_t PID_KP_BASE           = 0x60;
        static const uint32_t PID_KI_BASE           = 0x70;
        static const uint32_t PID_KD_BASE           = 0x80;
        static const uint32_t PULSE_LOW_BASE        = 0x90;
        static const uint32_t PULSE_HIGH_BASE       = 0xA0;
        static const uint32_t PULSE_VAL_BASE        = 0xB0;
        static const uint32_t SYSTEM_CLOCK_BASE     = 0xC0;
        static const uint32_t DATAPATH_CONTROL_BASE = 0xD0;
        static const uint32_t LUT_ADDR_DATA_BASE    = 0xE0;
        static const uint32_t TUNING_WORD_BASE      = 0xF0;

        static const uint32_t BUFFER_ADDRESS_BASE   = 0x01'00;
        static const uint32_t SPI_PORT_BASE         = 0x08'00;

        static const uint32_t SPI_RXDATA            = 0x00;
        static const uint32_t SPI_TXDATA            = 0x04;
        static const uint32_t SPI_STATUS            = 0x08;
        static const uint32_t SPI_CONTROL           = 0x0C;
        static const uint32_t SPI_SS                = 0x14;

        static const uint32_t CW_EN_TRIG = 0x02;
        static const uint32_t CW_START   = 0x01;

        static const int PORT = 1992;

        SocKit(LccControllerInfo info):ip_address(info.id) { }
        ~SocKit() { };
        SocKit(const SocKit& other) = delete;
        SocKit& operator=(const SocKit& other) = delete;
        SocKit(SocKit&& other) = default;
        SocKit& operator=(SocKit&& other) = default;

        virtual Type GetType() { return Type::SOC_KIT; }
        virtual string GetDescription() { return "Cyclone V SoC Board"; }
        virtual string GetSerialNumber() { throw logic_error("Not implemented"); }
        virtual void EepromReadString(char* buffer, int buffer_size) { throw logic_error("Not implemented"); }

        void DataStartCollect(int total_samples, Trigger trigger) override;
        bool DataIsCollectDone() override;
        void DataCancelCollect() override;

        int DataReceive(uint8_t data[],  int total_bytes)  override;
        int DataReceive(uint16_t data[], int total_values) override;
        int DataReceive(uint32_t data[], int total_values) override;

        uint32_t ReadRegister(uint32_t register_address) {
            return Read(Packet::REG_READ, register_address);
        }
        int ReadRegisterBlock(uint32_t register_address, uint32_t values[], uint32_t num_values) {
            return ReadBlock(Packet::REG_READ_BLOCK, register_address, values, num_values);
        }
        void WriteRegister(uint32_t register_address, uint32_t value) {
            Write(Packet::REG_WRITE, register_address, value);
        }
        void WriteRegisterBlock(uint32_t register_address,
                                const uint32_t values[], uint32_t num_values) {
            WriteBlock(Packet::REG_WRITE_BLOCK, register_address, values, num_values);
        }

        uint32_t ReadMemory(uint32_t memory_address) {
            return Read(Packet::MEM_READ, memory_address);
        }
        int ReadMemoryBlock(uint32_t memory_address, uint32_t values[], uint32_t num_values) {
            return ReadBlock(Packet::MEM_READ_BLOCK, memory_address, values, num_values);
        }
        void WriteMemory(uint32_t memory_address, uint32_t value) {
            Write(Packet::MEM_WRITE, memory_address, value);
        }
        void WriteMemoryBlock(uint32_t memory_address,
                              const uint32_t values[], uint32_t num_values) {
            WriteBlock(Packet::MEM_WRITE_BLOCK, memory_address, values, num_values);
        }

        uint32_t ReadRegisterDummy(uint32_t register_address) {
            return Read(Packet::REG_READ | Packet::DUMMY_BIT, register_address);
        }
        int ReadRegisterBlockDummy(uint32_t register_address, uint32_t values[], uint32_t num_values) {
            return ReadBlock(Packet::REG_READ_BLOCK | Packet::DUMMY_BIT, register_address,
                             values, num_values);
        }
        void WriteRegisterDummy(uint32_t register_address, uint32_t value) {
            Write(Packet::REG_WRITE | Packet::DUMMY_BIT, register_address, value);
        }
        void WriteRegisterBlockDummy(uint32_t register_address,
                                     const uint32_t values[], uint32_t num_values) {
            WriteBlock(Packet::REG_WRITE_BLOCK | Packet::DUMMY_BIT, register_address,
                       values, num_values);
        }

        uint32_t ReadMemoryDummy(uint32_t memory_address) {
            return Read(Packet::MEM_READ | Packet::DUMMY_BIT, memory_address);
        }
        int ReadMemoryBlockDummy(uint32_t memory_address, uint32_t values[], uint32_t num_values) {
            return ReadBlock(Packet::MEM_READ_BLOCK | Packet::DUMMY_BIT, memory_address,
                             values, num_values);
        }
        void WriteMemoryDummy(uint32_t memory_address, uint32_t value) {
            Write(Packet::MEM_WRITE | Packet::DUMMY_BIT, memory_address, value);
        }
        void WriteMemoryBlockDummy(uint32_t memory_address,
                                   const uint32_t values[], uint32_t num_values) {
            WriteBlock(Packet::MEM_WRITE_BLOCK | Packet::DUMMY_BIT, memory_address,
                       values, num_values);
        }

        void Shutdown();

    private:
        void SendPacket(Packet packet, TcpClientSocket& client_socket);
        Packet SendAndReceivePacket(Packet packet);

        uint32_t Read(uint32_t command, uint32_t address);
        void Write(uint32_t command, uint32_t address, uint32_t value);

        int ReadBlock(uint32_t command, uint32_t address, uint32_t values[], uint32_t num_values);
        void WriteBlock(uint32_t command, uint32_t address,
                        const uint32_t values[], uint32_t num_values);

        int ReadChunk(uint32_t command, uint32_t address, uint32_t values[], uint32_t num_values);
        void WriteChunk(uint32_t command, uint32_t address,
                        const uint32_t values[], uint32_t num_values);

        int ReceiveAdcData(uint32_t values[], uint32_t num_values);

        uint32_t ToUint32(uint8_t values[]) { return *reinterpret_cast<uint32_t*>(values); }
        std::vector<uint8_t> ToUint8Vec(const uint32_t values[], int num_values);

        bool is_start_address_current = false;
        uint32_t start_address        = 0;
        uint32_t num_samples          = 0; 
        uint32_t ip_address;
    };


}