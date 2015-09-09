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
#define QUOTE(x) #x
#endif
#ifndef CAT
#define CAT(x, y) x ## y
#endif

#define MUST_BE_POSITIVE(arg)                                      \
if ((arg) < 1) {                                                   \
    throw invalid_argument(CAT(QUOTE(arg), " must be positive.")); \
}

#define MUST_NOT_BE_NEGATIVE(arg)                                      \
if ((arg) < 0) {                                                       \
    throw invalid_argument(CAT(QUOTE(arg), " must not be negative.")); \
}

#define MUST_BE_SMALLER(arg, size)                                                           \
do {                                                                                         \
    auto MACRO_SIZE_ = size;                                                                 \
    if ((arg) >= MACRO_SIZE_) {                                                              \
        throw invalid_argument(CAT(QUOTE(arg), " must be smaller than " + to_string(size))); \
    }                                                                                        \
} while(0)

#define MUST_NOT_BE_SMALLER(arg, size)                                                           \
do {                                                                                             \
    auto MACRO_SIZE_ = size;                                                                     \
    if ((arg) < MACRO_SIZE_) {                                                                   \
        throw invalid_argument(CAT(QUOTE(arg), " must not be smaller than " + to_string(size))); \
    }                                                                                            \
} while(0)

#define MUST_BE_LARGER(arg, size)                                                           \
do {                                                                                        \
    auto MACRO_SIZE_ = size;                                                                \
    if ((arg) <= MACRO_SIZE_) {                                                             \
        throw invalid_argument(CAT(QUOTE(arg), " must be larger than " + to_string(size))); \
    }                                                                                       \
} while(0)

#define MUST_NOT_BE_LARGER(arg, size)                                                           \
do {                                                                                            \
    auto MACRO_SIZE_ = size;                                                                    \
    if ((arg) > MACRO_SIZE_) {                                                                  \
        throw invalid_argument(CAT(QUOTE(arg), " must not be larger than " + to_string(size))); \
    }                                                                                           \
} while(0)

#define MUST_NOT_BE_NULL(arg)                                      \
if ((arg) == nullptr) {                                            \
    throw invalid_argument(CAT(QUOTE(arg), " must not be null.")); \
}
