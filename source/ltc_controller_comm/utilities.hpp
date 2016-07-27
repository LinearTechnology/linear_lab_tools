#pragma once

#include <string>
#include <utility>
#include <vector>
#include <cstdint>
#include <stdexcept>

namespace linear {

using std::string;
using std::wstring;
using std::pair;
using std::vector;
using std::invalid_argument;
using std::logic_error;

template <typename T>
T Min(T a, T b) {
    return a > b ? b : a;
}

template <typename T>
T Max(T a, T b) {
    return a > b ? a : b;
}

template<class T, class U>
T Narrow(U u) { T t = static_cast<T>(u); if (static_cast<U>(t) != u) { throw logic_error("Typecast resulted in value change."); } return t; }

template <typename T, typename TCONTAINER>
T Last(TCONTAINER c) {
    return c[c.size() - 1];
}

inline  bool CompareI(const string& a, const string& b) {
    return _stricmp(a.c_str(), b.c_str()) == 0;
}

inline bool CompareI(const wstring& a, const wstring& b) {
    return _wcsicmp(a.c_str(), b.c_str()) == 0;
}

inline bool CompareI(const string& a, const string& b, int n) {
    return _strnicmp(a.c_str(), b.c_str(), n) == 0;
}

inline bool CompareI(const wstring& a, const wstring& b, int n) {
    return _wcsnicmp(a.c_str(), b.c_str(), n) == 0;
}

inline bool StartsWith(const wstring& full_string, const wstring& start_string) {
    if (full_string.size() < start_string.size()) { return false; }
    return wcsncmp(full_string.c_str(), start_string.c_str(), start_string.size()) == 0;
}

inline bool StartsWith(const string& full_string, const string& start_string) {
    if (full_string.size() < start_string.size()) { return false; }
    return strncmp(full_string.c_str(), start_string.c_str(), start_string.size()) == 0;
}

inline bool StartsWithI(const wstring& full_string, const wstring& start_string) {
    if (full_string.size() < start_string.size()) { return false; }
    return CompareI(full_string, start_string, Narrow<int>(start_string.size()));
}

inline bool StartsWithI(const string& full_string, const string& start_string) {
    if (full_string.size() < start_string.size()) { return false; }
    return CompareI(full_string, start_string, Narrow<int>(start_string.size()));
}

inline void PathFixSeparator(wstring& path) {
    for (auto& ch : path) {
        if (ch == L'\\') {
            ch = L'/';
        }
    }
}

class Path {
public:
    Path(wstring folder_in, wstring base_name_in, wstring extension_in) : folder(folder_in),
        base_name(base_name_in), extension(extension_in) {
        PathFixSeparator(folder);
        if (folder[folder.size() - 1] != L'/') {
            folder += L'/';
        }
        if (extension.size() > 0 && extension[0] != '.') {
            extension.insert(0, 1, L'.');
        }
        if (base_name.find_first_of(L"/\\") != base_name.npos) {
            throw invalid_argument("base_name cannot have separators in it.");
        }
        if (extension.find_first_of(L"/\\") != extension.npos) {
            throw invalid_argument("extension cannot have separators in it.");
        }
    }
    Path(wstring path) {
        size_t extension_index = path.npos;
        size_t j = 0;
        for (size_t i = path.size(); i > 0; --i) {
            j = i - 1;
            if (extension_index == path.npos && path[j] == L'.') {
                extension_index = j;
                extension = path.substr(extension_index);
            }
            if (path[j] == L'/' || path[j] == L'\\') {
                break;
            }
        }
        if (j == 0) {
            folder = L"";
            base_name = path.substr(0, extension_index);
            return;
        }
        ++j;
        base_name = path.substr(j, extension_index - j);
        folder = path.substr(0, j);
        PathFixSeparator(folder);
    }
    wstring Fullpath() {
        auto result = folder + base_name + extension;
        return result;
    }
    wstring Folder() { return folder; }
    wstring BaseName() { return base_name; }
    wstring Extension() { return extension; }
private:
    wstring folder;
    wstring base_name;
    wstring extension;
};

size_t GetFileSize(const wstring& file_name);

bool DoesFileExist(const wstring& file_name);

vector<wstring> ListFiles(wstring path);

wstring GetPathFromRegistry(const wstring& key_name,
                            const wstring& key_value_name = L"Location");
string ToUtf8(const wstring& utf16);
wstring ToUtf16(const string& utf8);

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
    int num_copy = Narrow<int>(source.size() + 1);
    if (num_copy > buffer_size) {
        num_copy = buffer_size;
    }
    memcpy_s(buffer, buffer_size, source.c_str(), num_copy);
    buffer[buffer_size - 1] = '\0';
}

template <typename Func>
class RaiiCleanup {
    Func cleanup;
    bool run_cleanup = true;
    RaiiCleanup(const RaiiCleanup&) = delete;
public:
    RaiiCleanup(Func cleanup) : cleanup(cleanup) { }
    RaiiCleanup(RaiiCleanup&& other) : cleanup(other.cleanup) {
        other.run_cleanup = false;
    }
    ~RaiiCleanup() { if (run_cleanup) { cleanup(); } }
    void Cancel() { run_cleanup = false; }
};

template <typename Func>
inline RaiiCleanup<Func> MakeRaiiCleanup(Func cleanup) {
    return RaiiCleanup<Func>(cleanup);
}

inline vector<string> SplitString(const string& str, const char* delimiters = nullptr,
                                  bool keep_empty_fields = false) {
    if (delimiters == nullptr) {
        delimiters = " \t\n\r\v\f";
    }
    vector<string> strs;
    size_t next = -1;
    do {
        auto current = next + 1;
        next = str.find_first_of(delimiters, current);
        auto field = str.substr(current, next - current);
        if (keep_empty_fields || field.size() > 0) {
            strs.push_back(field);
        }
    } while (next != string::npos);
    return strs;
}
inline vector<string> SplitString(const string& str, char delimiter,
                                  bool keep_empty_fields = false) {
    vector<string> strs;
    size_t next = -1;
    do {
        auto current = next + 1;
        next = str.find(delimiter, current);
        auto field = str.substr(current, next - current);
        if (keep_empty_fields || field.size() > 0) {
            strs.push_back(field);
        }
    } while (next != string::npos);
    return strs;
}

inline vector<wstring> SplitString(const wstring& str, const wchar_t* delimiters = nullptr,
                                   bool keep_empty_fields = false) {
    if (delimiters == nullptr) {
        delimiters = L" \t\n\r\v\f";
    }
    vector<wstring> strs;
    size_t next = -1;
    do {
        auto current = next + 1;
        next = str.find_first_of(delimiters, current);
        auto field = str.substr(current, next - current);
        if (keep_empty_fields || field.size() > 0) {
            strs.push_back(field);
        }
    } while (next != string::npos);
    return strs;
}
inline vector<wstring> SplitString(const wstring& str, wchar_t delimiter,
                                   bool keep_empty_fields = false) {
    vector<wstring> strs;
    size_t next = -1;
    do {
        auto current = next + 1;
        next = str.find(delimiter, current);
        auto field = str.substr(current, next - current);
        if (keep_empty_fields || field.size() > 0) {
            strs.push_back(field);
        }
    } while (next != string::npos);
    return strs;
}

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

