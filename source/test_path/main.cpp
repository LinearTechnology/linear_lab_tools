#include <iostream>
#include "../ltc_controller_comm/utilities.hpp"

using linear::Path;
using std::wstring;
using std::wcout;


int main() {
    wstring folder = L"this/is/a";
    wstring base_name = L"test";
    wstring extension = L"ext";

    Path path(folder, base_name, extension);
    wcout << L"full path is '" << path.Fullpath() << L"'\n";

    auto path2 = Path(L"/another/full/path.txt");

    wcout << L"folder is '" << path.Folder() << "'\n";
    wcout << L"base_name is '" << path.BaseName() << "'\n";
    wcout << L"extension is '" << path.Extension() << "'\n";

    auto path3 = Path(L"\\this\\one\\has\\back.slashes");
    wcout << L"full path is '" << path3.Fullpath() << L"'\n";

    try {
        auto bad_path = Path(L"bad", L"/path", L".ext");
    } catch (std::invalid_argument) {
        wcout << L"Caught invalid argument.\n";
    }
}