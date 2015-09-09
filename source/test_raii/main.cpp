#include <iostream>
#include "ltc_controller_comm/utilities.hpp"

using linear::RaiiCleanup;
using linear::MakeRaiiCleanup;
using std::cout;

void twice(int& i) {
    i *= 2;
}

void cleanup(int* i) {
    cout << "Cleaning up i\n";
    *i = 0;
}

int main() {
    int i = 3;
    {
        auto ri = MakeRaiiCleanup([&i] { cleanup(&i); });
        cout << "i is " << i << "\n";
        twice(i);
        cout << "i is " << i << "\n";
    }
    cout << "i is " << i << "\n";
    return 0;
}