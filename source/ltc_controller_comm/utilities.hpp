#pragma once

#include <cctype>
#include <string>
#include <utility>
#include <vector>
#include <cstdint>
#include <stdexcept>
#ifdef max
#undef max
#endif
#include "gsl"
#include <cstdlib>
#include <experimental/filesystem>
#include <cstdarg>

namespace linear {

using std::string;
using std::pair;
using std::vector;
using std::invalid_argument;
using std::logic_error;
using gsl::narrow;
using std::experimental::filesystem::path;

#ifdef _WIN32
using std::wstring;
path GetPathFromRegistry(const wstring& key_name,
                         const wstring& key_value_name = L"Location");
inline path GetInstallPath() {
    return GetPathFromRegistry(L"SOFTWARE\\Linear Technology\\LinearLabTools");
}
string ToUtf8(const wstring& utf16);
wstring ToUtf16(const string& utf8);
#else
path GetPathFromEnvironment(const string& var_name);
inline path GetInstallPath() {
    return GetPathFromEnvironment("LINEAR_LAB_TOOLS_PATH");
}
#endif

template<size_t SIZE>
void safe_sprintf(char(&buffer)[SIZE], const char* format, ...) {
    memset(buffer, 0, SIZE);
    va_list argptr;
    va_start(argptr, format);
#ifdef _WIN32
    vsprintf_s(buffer, format, argptr);
#else
    vsnprintf(buffer, SIZE, format, argptr);
#endif
    va_end(argptr);
}

inline void safe_memcpy(void* dest, size_t dest_size, const void* source, size_t source_size) {
#ifdef _WIN32
    memcpy_s(dest, dest_size, source, source_size);
#else
    auto size = std::min(dest_size, source_size);
    memcpy(dest, source, size);
#endif
}

template <typename T, typename TCONTAINER>
T Last(TCONTAINER c) {
    return c[c.size() - 1];
}

bool CompareFileNameStart(const string& file_name, const string& prefix);
bool CompareFileName(const string& file_name_1, const string& file_name_2);
vector<path> ListFiles(path directory);

bool CompareI(const string& a, const string& b);

inline void SwapBytes(uint8_t*, int) { }
inline uint8_t SwapBytes(uint8_t value) { return value; }

inline void SwapBytes(uint16_t values[], int num_values) {
    uint16_t temp, value;
    for (int i = 0; i < num_values; ++i) {
        value = values[i];
        temp = value >> 8;
        value <<= 8;
        value |= temp;
        values[i] = value;
    }
}
inline uint16_t SwapBytes(uint16_t value) {
    uint16_t temp = value >> 8;
    value <<= 8;
    return value | temp;
}

inline void SwapBytes(uint32_t values[], int num_values) {
    uint8_t* byte_pointer = reinterpret_cast<uint8_t*>(values);
    for (int i = 0; i < num_values; ++i, byte_pointer += 4) {
        uint32_t value = values[i];
        uint8_t* value_pointer = reinterpret_cast<uint8_t*>(&value);
        byte_pointer[0] = value_pointer[3];
        byte_pointer[1] = value_pointer[2];
        byte_pointer[2] = value_pointer[1];
        byte_pointer[3] = value_pointer[0];
    }
}
inline uint32_t SwapBytes(uint32_t value) {
    uint32_t high = SwapBytes(static_cast<uint16_t>(value >> 16));
    uint32_t low = SwapBytes(static_cast<uint16_t>(value & 0xFFFF));
    return (low << 16) | high;
}

void SwapBytesUint16(uint8_t* values, uint32_t num_values);
void SwapBytesUint32(uint8_t* values, uint32_t num_values);

inline int HexCharToNybble(char hex) {
    if (hex >= '0' && hex <= '9') {
        return hex - '0';
    } else if (hex >= 'A' && hex <= 'F') {
        return hex - 'A' + 10;
    } else {
        return -1;
    }
}

inline int HexToBytes(const char* hex, uint8_t data[], int num_bytes) {
    for (int i = 0; i < num_bytes; ++i) {
        int left = HexCharToNybble(*hex);
        if (left < 0) {
            return -i;
        }
        ++hex;
        int right = HexCharToNybble(*hex);
        if (right < 0) {
            return -i;
        }
        ++hex;
        data[i] = static_cast<uint8_t>(left << 4 | right);
    }
    return num_bytes;
}

inline uint8_t HexToByte(const char hex[]) {
    int left = HexCharToNybble(hex[0]);
    if (left < 0) {
        throw invalid_argument("Not a valid hex string.");
    }
    int right = HexCharToNybble(hex[1]);
    if (right < 0) {
        throw invalid_argument("Not a valid hex string.");
    }
    return static_cast<uint8_t>(left << 4 | right);
}

inline uint16_t HexToUint16(const char hex[]) {
    uint16_t value;
    auto n = HexToBytes(hex, reinterpret_cast<uint8_t*>(&value), sizeof(uint16_t));
    if (n != sizeof(uint16_t)) {
        throw invalid_argument("Not a valid hex string.");
    }
    SwapBytes(value);
    return value;
}

inline uint32_t HexToUint32(const char hex[]) {
    uint32_t value;
    auto n = HexToBytes(hex, reinterpret_cast<uint8_t*>(&value), sizeof(uint32_t));
    if (n != sizeof(uint32_t)) {
        throw invalid_argument("Not a valid hex string.");
    }
    SwapBytes(value);
    return value;
}

inline string ToHex(uint8_t byte) {
    string hex = "00";
    uint8_t nybble = byte >> 4;
    if (nybble < 10) {
        hex[0] += nybble;
    } else {
        hex[0] = 'A' + nybble - 10;
    }
    nybble = byte & 0x0F;
    if (nybble < 10) {
        hex[1] += nybble;
    } else {
        hex[1] = 'A' + nybble - 10;
    }
    return hex;
}

inline string ToHex(uint16_t value) {
    return ToHex(static_cast<uint8_t>(value >> 8)) + ToHex(static_cast<uint8_t>(value & 0xFF));
}

inline string ToHex(uint32_t value) {
    return ToHex(uint16_t(value >> 16)) + ToHex(uint16_t(value & 0xFFFF));
}

inline void CopyToBuffer(char* buffer, int buffer_size, const string& source) {
    int num_copy = narrow<int>(source.size());
    if (num_copy >= buffer_size) {
        num_copy = buffer_size - 1; // leave a spot for \0
    }
    auto c_str = source.c_str();
    for (int i = 0; i < num_copy; ++i) {
        buffer[i] = c_str[i];
    }
    buffer[num_copy] = '\0';
}

vector<string> SplitString(const string& str, const char* delimiters = nullptr,
                           bool keep_empty_fields = false);
vector<string> SplitString(const string& str, char delimiter,
                                  bool keep_empty_fields = false);

inline constexpr uint32_t operator"" _swap_u32(unsigned long long int value) {
    return (value < 0x1'00'00'00'00) ?
        uint32_t((value << 24) | ((value << 8) & 0x00FF0000) | ((value >> 8) & 0x0000FF00) | (value >> 24)) :
        throw std::logic_error("Must be uint32_t");
}

inline constexpr uint32_t operator"" _swap_u16(unsigned long long int value) {
    return (value < 0x1'00'00) ? uint16_t((value << 8) | ((value >> 8) & 0x00FF)) :
        throw std::logic_error("Must be uint16_t");
}

inline constexpr uint32_t operator"" _as_u32(const char* value, size_t length) {
    return length == 4 ? (value[0] << 24) | (value[1] << 16) | (value[2] << 8) | value[3] :
        throw std::logic_error("Must be a 4 character string");
}

}

