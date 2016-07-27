#include "utilities.hpp"

#define WINDOWS_LEAN_AND_MEAN
#include <Windows.h>
#include <stdexcept>
using std::runtime_error;

namespace linear {

using std::make_pair;

wstring GetPathFromRegistry(const wstring& key_name, const wstring& key_value_name) {
    HKEY key;
    auto result = RegOpenKeyExW(HKEY_LOCAL_MACHINE, key_name.c_str(), 0, KEY_READ, &key);
    if (result != ERROR_SUCCESS) {
        throw runtime_error("Error opening registry key (" + std::to_string(result) + ")");
    }

    wstring path(MAX_PATH, L'\0');
    auto size = Narrow<DWORD>(path.size());
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
    auto utf8_length = WideCharToMultiByte(CP_UTF8, 0, utf16.c_str(), Narrow<int>(utf16.size()),
                                           nullptr, 0, nullptr, nullptr);
    string utf8(utf8_length, '\0');
    WideCharToMultiByte(CP_UTF8, 0, utf16.c_str(), Narrow<int>(utf16.size()), &utf8[0], utf8_length, 0, 0);
    return utf8;
}
wstring ToUtf16(const string& utf8) {
    auto utf16_length = MultiByteToWideChar(CP_UTF8, 0, utf8.c_str(), Narrow<int>(utf8.size()), nullptr, 0);
    wstring utf16(utf16_length, '\0');
    MultiByteToWideChar(CP_UTF8, 0, utf8.c_str(), Narrow<int>(utf8.size()), &utf16[0], utf16_length);
    return utf16;
}

size_t GetFileSize(const wstring& file_name) {
    HANDLE file = CreateFileW(file_name.c_str(), GENERIC_READ,
                              FILE_SHARE_READ | FILE_SHARE_WRITE, nullptr, OPEN_EXISTING,
                              FILE_ATTRIBUTE_NORMAL, nullptr);
    if (file == INVALID_HANDLE_VALUE) {
        throw runtime_error("Could not open file '" + ToUtf8(file_name) + "'");
    }
    // Guarantee that the file is closed no matter what.
    auto raii_file = MakeRaiiCleanup([&file] { CloseHandle(file); });

    LARGE_INTEGER size;
    if (!GetFileSizeEx(file, &size)) {
        throw runtime_error("Could not get size of file '" + ToUtf8(file_name) + "'");
    }
    return Narrow<size_t>(size.QuadPart);
}

bool DoesFileExist(const wstring& file_name) {
    HANDLE file = CreateFileW(file_name.c_str(), GENERIC_READ,
                              FILE_SHARE_READ | FILE_SHARE_WRITE, nullptr, OPEN_EXISTING,
                              FILE_ATTRIBUTE_NORMAL, nullptr);
    if (file == INVALID_HANDLE_VALUE) {
        return false;
    } else {
        CloseHandle(file);
        return true;
    }
}

vector<wstring> ListFiles(wstring path) {
    vector<wstring> names;
    PathFixSeparator(path);
    if (path[path.size() - 1] != L'/') {
        path += L'/';
    }
    path += L"*.*";

    WIN32_FIND_DATAW find_data;
    HANDLE hFind = FindFirstFileW(path.c_str(), &find_data);
    if (hFind != INVALID_HANDLE_VALUE) {
        do {
            if (!(find_data.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY)) {
                names.push_back(find_data.cFileName);
            }
        } while (FindNextFileW(hFind, &find_data));
        FindClose(hFind);
    }
    return names;
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