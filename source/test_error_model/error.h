#pragma once
#include <string>
#include <exception>
#include <stdexcept>

using std::string;
using std::to_string;
using std::exception;
using std::runtime_error;
using std::logic_error;
using std::invalid_argument;

class HardwareError : public runtime_error {
public:
    HardwareError(const string& message, int error_code): 
        runtime_error(message), error_code(error_code) { }
    virtual string FullMessage() = 0;
protected:
    int error_code = 0;
};
class Dc1371Error : public HardwareError {
public:
    Dc1371Error(const string& message, int error_code) : HardwareError(message, error_code) { }
    string FullMessage() override {
        if (error_code < BAD_NEGATIVE) {
            error_code = BAD_NEGATIVE;
        } else if (error_code > BAD_TOO_LARGE) {
            error_code = BAD_TOO_LARGE;
        }
        return (string(what()) + " (DC1371 error code: " + strings[error_code + 1] + ")");
    }
private:
#define ENUM_DECLARATION       \
    ENUM_START                 \
    ENUM(BAD_NEGATIVE,   -1),  \
    ENUM(OK,              0),  \
    ENUM(GOT_ACK,         1),  \
    ENUM(GOT_NAK,         2),  \
    ENUM(ABORTED,         3),  \
    ENUM(BAD_FOUR,        4),  \
    ENUM(BAD_FIVE,        5),  \
    ENUM(BAD_SIX,         6),  \
    ENUM(BAD_SEVEN,       7),  \
    ENUM(PHASE_ERROR,     8),  \
    ENUM(BAD_SIGNATURE,   9),  \
    ENUM(BAD_PASSWORD,    10), \
    ENUM(ILLEGAL_COMMAND, 11), \
    ENUM(GENERIC_ERROR,   12), \
    ENUM(FPGA_LOAD_ERROR, 13), \
    ENUM(FPGA_ID_ERROR,   14), \
    ENUM(FPGA_PLL_ERROR,  15), \
    ENUM(COLLECT_ERROR,   16), \
    ENUM(BAD_TOO_LARGE,   17), \
    }
#define ENUM_START enum {
#define ENUM(name, value) name = value
    ENUM_DECLARATION;
    static const int NUM_ERRORS = BAD_TOO_LARGE + 2; // (+2 is for BAD_NEGATIVE and OK)
    static const string strings[NUM_ERRORS];
};

class FtdiError : public HardwareError {
public:
    FtdiError(const string& message, int error_code) : HardwareError(message, error_code) { }
    string FullMessage() override {
        return (string(what()) + " (FTDI error code: " + to_string(error_code) + ")");
    }
};

template <typename Func, typename T>
int ToErrorCode(Func func, T& result, string& out_message) {
    try {
        result = func();
        return 0;
    } catch (invalid_argument& err) {
        out_message = err.what();
        return -2;
    } catch (logic_error& err) {
        out_message = err.what();
        return -3;
    }
    catch (HardwareError& err) {
        out_message = err.FullMessage();
        return -1;
    } catch (exception& err) {
        out_message = err.what();
        return -4;
    } catch (...) {
        out_message = "An unknown error occurred.";
        return -4;
    }
}

template <typename Func>
int ToErrorCode(Func func, string& out_message) {
    try {
        func();
        return 0;
    } catch (invalid_argument& err) {
        out_message = err.what();
        return -2;
    } catch (logic_error& err) {
        out_message = err.what();
        return -3;
    } catch (HardwareError& err) {
        out_message = err.FullMessage();
        return -1;
    } catch (exception& err) {
        out_message = err.what();
        return -4;
    } catch (...) {
        out_message = "An unknown error occurred.";
        return -4;
    }
}

