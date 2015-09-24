#include <iostream>
#include <string>
#include <exception>
#include <stdexcept>

using std::cout;
using std::invalid_argument;
using std::string;
using std::to_string;

#define QUOTE(x) #x
#define CAT(x, y) x ## y
#define THROW_MUST_BE_POSITIVE(arg) throw invalid_argument(CAT(QUOTE(arg), " must be a positive integer."))
#define THROW_MUST_BE_SMALLER(arg, size) throw invalid_argument(string(QUOTE(arg)) + " must be smaller than " + to_string(size))
#define THROW_MUST_NOT_BE_NULL(arg) throw invalid_argument(CAT(QUOTE(arg), " must not be null."))

int main() {
    try {
        THROW_MUST_BE_POSITIVE(i);
    } catch (invalid_argument& e) {
        cout << "Caught: " << e.what() << "\n";
    }

    try {
        THROW_MUST_BE_SMALLER(i, 1000/10);
    } catch (invalid_argument& e) {
        cout << "Caught: " << e.what() << "\n";
    }

    try {
        THROW_MUST_NOT_BE_NULL(i);
    } catch (invalid_argument& e) {
        cout << "Caught: " << e.what() << "\n";
    }

}