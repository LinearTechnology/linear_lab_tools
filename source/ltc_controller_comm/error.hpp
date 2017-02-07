#pragma once
#include <string>
#include <exception>
#include <stdexcept>

#include "ltc_controller_comm.h"

namespace linear {

    using std::string;
    using std::exception;
    using std::runtime_error;
    using std::logic_error;
    using std::invalid_argument;
    using std::domain_error;

    class HardwareError : public runtime_error {
    public:
        HardwareError(const string& message, int error_code = 0) :
            runtime_error(message), error_code(error_code) { }
        virtual string FullMessage() { return what(); }
    protected:
        int error_code;
    };

    template <typename Func, typename T>
    int ToErrorCode(Func func, T& result, string& out_message) {
        try {
            result = func();
            return LCC_ERROR_OK;
        } catch (invalid_argument& err) {
            out_message = err.what();
            return LCC_ERROR_INVALID_ARG;
        } catch (domain_error& err) {
            out_message = err.what();
            return LCC_ERROR_NOT_SUPPORTED;
        } catch (logic_error& err) {
            out_message = err.what();
            return LCC_ERROR_LOGIC;
        } catch (HardwareError& err) {
            out_message = err.FullMessage();
            return LCC_ERROR_HARDWARE;
        } catch (exception& err) {
            out_message = err.what();
            return LCC_ERROR_UNKNOWN;
        } catch (...) {
            out_message = "An unknown error occurred.";
            return LCC_ERROR_UNKNOWN;
        }
    }

    template <typename Func>
    int ToErrorCode(Func func, string& out_message) {
        try {
            func();
            return LCC_ERROR_OK;
        } catch (invalid_argument& err) {
            out_message = err.what();
            return LCC_ERROR_INVALID_ARG;
        } catch (domain_error& err) {
            out_message = err.what();
            return LCC_ERROR_NOT_SUPPORTED;
        } catch (logic_error& err) {
            out_message = err.what();
            return LCC_ERROR_LOGIC;
        } catch (HardwareError& err) {
            out_message = err.FullMessage();
            return LCC_ERROR_HARDWARE;
        } catch (exception& err) {
            out_message = err.what();
            return LCC_ERROR_UNKNOWN;
        } catch (...) {
            out_message = "An unknown error occurred.";
            return LCC_ERROR_UNKNOWN;
        }
    }
}

#ifndef QUOTE
#define QUOTE_DETAIL(x) #x
#define QUOTE(x) QUOTE_DETAIL(x)
#endif

#define ASSERT_POSITIVE(arg)                                 \
if ((arg) < 1) {                                             \
    throw invalid_argument(QUOTE(arg) " must be positive."); \
}

#define ASSERT_NOT_NEGATIVE(arg)                                 \
if ((arg) < 0) {                                                 \
    throw invalid_argument(QUOTE(arg) " must not be negative."); \
}

#define ASSERT_SMALLER(arg, size)                                                      \
do {                                                                                   \
    auto MACRO_SIZE_ = size;                                                           \
    if ((arg) >= MACRO_SIZE_) {                                                        \
        throw invalid_argument(QUOTE(arg) " must be smaller than " + to_string(size)); \
    }                                                                                  \
} while(0)

#define ASSERT_NOT_SMALLER(arg, size)                                                      \
do {                                                                                       \
    auto MACRO_SIZE_ = size;                                                               \
    if ((arg) < MACRO_SIZE_) {                                                             \
        throw invalid_argument(QUOTE(arg) " must not be smaller than " + to_string(size)); \
    }                                                                                      \
} while(0)

#define ASSERT_LARGER(arg, size)                                                      \
do {                                                                                  \
    auto MACRO_SIZE_ = size;                                                          \
    if ((arg) <= MACRO_SIZE_) {                                                       \
        throw invalid_argument(QUOTE(arg) " must be larger than " + to_string(size)); \
    }                                                                                 \
} while(0)

#define ASSERT_NOT_LARGER(arg, size)                                                      \
do {                                                                                      \
    auto MACRO_SIZE_ = size;                                                              \
    if ((arg) > MACRO_SIZE_) {                                                            \
        throw invalid_argument(QUOTE(arg) " must not be larger than " + to_string(size)); \
    }                                                                                     \
} while(0)

#define ASSERT_NOT_NULL(arg)                                 \
if ((arg) == nullptr) {                                      \
    throw invalid_argument(QUOTE(arg) " must not be null."); \
}
