#include "utilities.hpp"
#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN
#include <Windows.h>
#undef min
#undef max
#endif
#include <stdexcept>


using std::runtime_error;

namespace linear {

#ifdef _WIN32
#define FIX_CHAR(c) tolower(c)
#else
#define FIX_CHAR(c) c
#endif
bool CompareFileNameStart(const string& file_name, const string& prefix) {
    if (prefix.size() > file_name.size()) { return false; }
    std::string::const_iterator a = file_name.begin();
    for (std::string::const_iterator b = prefix.begin(); b != prefix.end(); ++a, ++b) {
        if (FIX_CHAR(*a) != FIX_CHAR(*b)) {
            return false;
        }
    }
    return true;
}

bool CompareFileName(const string& file_name_1, const string& file_name_2) {
    if (file_name_1.size() != file_name_2.size()) { return false; }
    std::string::const_iterator a = file_name_1.begin();
    for (std::string::const_iterator b = file_name_2.begin(); b != file_name_2.end(); ++a, ++b) {
        if (FIX_CHAR(*a) != FIX_CHAR(*b)) {
            return false;
        }
    }
    return true;
}

bool CompareI(const string& str_a, const string& str_b) {
    if (str_a.size() != str_b.size()) { return false; }
    std::string::const_iterator a = str_a.begin();
    for (std::string::const_iterator b = str_b.begin(); b != str_b.end(); ++a, ++b) {
        if (tolower(*a) != tolower(*b)) {
            return false;
        }
    }
    return true;
}

#ifdef _WIN32
path GetPathFromRegistry(const wstring& key_name, const wstring& key_value_name) {
    HKEY key;
    auto result = RegOpenKeyExW(HKEY_LOCAL_MACHINE, key_name.c_str(), 0, KEY_READ, &key);
    if (result != ERROR_SUCCESS) {
        throw runtime_error("Error opening registry key (" + std::to_string(result) + ")");
    }

    wstring path(MAX_PATH, L'\0');
    auto size = narrow<DWORD>(path.size());
    result = RegQueryValueExW(key, key_value_name.c_str(), 0, nullptr, reinterpret_cast<BYTE*>(&path[0]), &size);
    RegCloseKey(key);

    if (result != ERROR_SUCCESS) {
        throw runtime_error("Error querying registry key (" + std::to_string(result) + ")");
    } else {
        path.resize(wcsnlen_s(path.c_str(), path.size()));
        return path;
    }
}

string ToUtf8(const wstring& utf16) {
    auto utf8_length = WideCharToMultiByte(CP_UTF8, 0, utf16.c_str(), narrow<int>(utf16.size()),
                                           nullptr, 0, nullptr, nullptr);
    string utf8(utf8_length, '\0');
    WideCharToMultiByte(CP_UTF8, 0, utf16.c_str(), narrow<int>(utf16.size()), &utf8[0], utf8_length, 0, 0);
    return utf8;
}

wstring ToUtf16(const string& utf8) {
    auto utf16_length = MultiByteToWideChar(CP_UTF8, 0, utf8.c_str(), narrow<int>(utf8.size()), nullptr, 0);
    wstring utf16(utf16_length, '\0');
    MultiByteToWideChar(CP_UTF8, 0, utf8.c_str(), narrow<int>(utf8.size()), &utf16[0], utf16_length);
    return utf16;
}

#else
#include <cstdlib>
path GetPathFromEnvironment(const string& var_name) {
    auto path_str = std::getenv(var_name.c_str());
    return path(path_str);
}
#endif

vector<path> ListFiles(path directory) {
    vector<path> file_names;
    
    return file_names;
}

vector<string> SplitString(const string& str, const char* delimiters, bool keep_empty_fields) {
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

vector<string> SplitString(const string& str, char delimiter, bool keep_empty_fields) {
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

void SwapBytesUint32(uint8_t* values, uint32_t num_values) {
    if ((num_values % sizeof(uint32_t)) != 0) {
        throw logic_error("bad size for uint8 array");
    }
    for (uint32_t i = 0; i < num_values; i += sizeof(uint32_t)) {
        uint8_t temp = values[i];
        values[i] = values[i + 3];
        values[i + 3] = temp;
        temp = values[i + 1];
        values[i + 1] = values[i + 2];
        values[i + 2] = temp;
    }
}

void SwapBytesUint16(uint8_t* values, uint32_t num_values) {
    // yes uint32_t, this is a limitation of the controller
    if ((num_values % sizeof(uint32_t)) != 0) {
        throw logic_error("bad size for uint8 array");
    }
    for (uint32_t i = 0; i < num_values; i += sizeof(uint16_t)) {
        uint8_t temp = values[i];
        values[i] = values[i + 1];
        values[i + 1] = temp;
    }
}
}
