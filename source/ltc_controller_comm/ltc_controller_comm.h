#pragma once
// Header file for the LtcControllerComm DLL
// This library provides functions and some constants used to communicate with the DC1371A,
// DC718C, DC890B, and high speed commercial FPGA demo-boards used as controllers for
// Linear Technology device demo-boards. Note that there is no
// open command, the device is opened automatically as needed. There is a close method, but
// it is not necessary to call it, the cleanup method will close the handle.If there is an
// error or the close method is called, the device will again be opened automatically as
// needed.
// To connect (in C) do something like this:
// #include <stdlib.h>
// #include <stdio.h>
// #include "ltc_controller_comm.h"
//
// int num_devices = 0;
// int status = LccCreateDeviceList(&num_devices);
// if (status != LCC_ERROR_OK) {
//     return status;
// }
//
// LccControllerInfo* device_info = malloc(num_devices * sizeof(LccControllerInfo));
// status = LccGetDeviceList(device_info, num_devices);
// if (status != LCC_ERROR_OK) {
//     return status;
// }
//
// int device_index;
// for (device_index = 0; device_index < num_devices; ++device_index) {
//     // in here do one of the following:
//     // 1. Just take the first one (loop is unecessary then)
//     // 2. Check for desired description or serial number
//     // 3. Open up the device and talk to it to find out if it is the one you want, then
//     //    close it again.
//     if (this_is_the_right_device) {
//         break;
//     }
// }
//
// if (device_index == num_devices) {
//     printf("No LTC controller board was detected\n");
//     return -1;
// }
//
// LccHandle handle = NULL;
// status = LccInitDevice(&handle, device_info[device_index]);
// if (status != LCC_ERROR_OK) {
//     return status;
// }
//
// // Now you can talk to your LTC controller board.


#include <stdint.h>
#include <stdbool.h>

#ifndef LTC_CONTROLLER_COMM_API
#define LTC_CONTROLLER_COMM_API __declspec(dllimport)
#endif

// Controller types
const int LCC_TYPE_NONE       = 0x00000000;
const int LCC_TYPE_DC1371     = 0x00000001;
const int LCC_TYPE_DC718      = 0x00000002;
const int LCC_TYPE_DC890      = 0x00000004;
const int LCC_TYPE_HIGH_SPEED = 0x00000008;
const int LCC_TYPE_SOC_KIT    = 0x00000010;
const int LCC_TYPE_UNKNOWN    = 0xFFFFFFFF;

// SPI Chip select state
const int LCC_SPI_CS_STATE_LOW  = 0;
const int LCC_SPI_CS_STATE_HIGH = 1;

// Trigger modes
const int LCC_TRIGGER_NONE                      = 0;
const int LCC_TRIGGER_START_POSITIVE_EDGE       = 1;
const int LCC_TRIGGER_DC890_START_NEGATIVE_EDGE = 2;
const int LCC_TRIGGER_DC1371_STOP_NEGATIVE_EDGE = 3;

// Convenient constants for buffer sizes
const int LCC_MAX_DESCRIPTION_SIZE   = 64;
const int LCC_MAX_SERIAL_NUMBER_SIZE = 16;

// Possible error return values, use LccGetErrorInfo for specific information.
const int LCC_ERROR_OK            =  0; // No error.
const int LCC_ERROR_HARDWARE      = -1; // A hardware error (controller I/O, maybe unplugged or no
// power?) this may have a device specific error code.
const int LCC_ERROR_INVALID_ARG   = -2; // User passed in an invalid argument or did something bad.
const int LCC_ERROR_LOGIC         = -3; // The DLL did something wrong.
const int LCC_ERROR_NOT_SUPPORTED = -4; // The particular device does not support the operation.
const int LCC_ERROR_UNKNOWN       = -5; // Caught an unexpected exception.

// For high speed FPGA demo-board based controllers only.
// mode argument to set_mode. For FIFO communication use BIT_MODE_FIFO, for
// everything else use BIT_MODE_MPSSE
const int LCC_HS_BIT_MODE_MPSSE = 0x02;
const int LCC_HS_BIT_MODE_FIFO  = 0x40;

// For DC1371A controllers only.
// Chip select, usually should be 1 (default)
const int LCC_1371_CHIP_SELECT_ONE = 1;
const int LCC_1371_CHIP_SELECT_TWO = 2;

// Info for a found controller
typedef struct LccControllerInfoStruct {
    int type;
    char description[LCC_MAX_DESCRIPTION_SIZE];
    char serial_number[LCC_MAX_SERIAL_NUMBER_SIZE];
    uint32_t id;
} LccControllerInfo;

// Opaque handle to High Speed Comm interface
typedef void* LccHandle;

#ifdef __cplusplus
extern "C" {
#endif

// Device list functions

// Get the number of controllers plugged in, but see comments for next function.
LTC_CONTROLLER_COMM_API int LccGetNumControllers(int controller_types, int max_controllers,
                                                 int* num_controllers);

// Using the number of devices from above, allocate an array of LccDeviceInfo structures,
// they will be filled with information for each device. It is not necessary to call
// LccGetNumDevices; if you know you want the first device, just create a single
// LccDeviceInfo structure and pass a pointer to it into the the function and use 1 for
// num_devices, otherwise make an array of at least as many structures as you have devices
// plugged in.
LTC_CONTROLLER_COMM_API int LccGetControllerList(int controller_types,
                                                 LccControllerInfo* controller_info_list, int num_controllers);

// Returns a single LccController info given the type and ID of the controller. Cannot be used
// with multiple types
LTC_CONTROLLER_COMM_API int LccGetControllerInfoFromId(int controller_type, const char* id,
                                                       LccControllerInfo* controller_info);

// General functions.

// Given a LccControllerInfo struct and a pointer to an LccHandle, this function initializes the
// controller and sets the handle.
LTC_CONTROLLER_COMM_API int LccInitController(LccHandle* handle,
                                              LccControllerInfo* controller_info);

// This function MUST be called before the program exits to clean up the internal data structures.
// It takes a pointer to the handle and zeros the handle to help prevent accidental reuse.
LTC_CONTROLLER_COMM_API int LccCleanup(LccHandle* handle);

// Get controller description
LTC_CONTROLLER_COMM_API int LccGetDescription(LccHandle handle, char* description_buffer,
                                              int description_buffer_size);

// Get controller serial number
LTC_CONTROLLER_COMM_API int LccGetSerialNumber(LccHandle handle, char* serial_number_buffer,
                                               int serial_number_buffer_size);

// Reset the controller
// Not used with HighSpeed Controllers
LTC_CONTROLLER_COMM_API int LccReset(LccHandle handle);

// Close the device but keep the handle valid; if a function is called that requires the device
// to be open, it will be opened automatically.
// Not used with DC1371
LTC_CONTROLLER_COMM_API int LccClose(LccHandle handle);

// Call with buffer_size == 0 and message_buffer == NULL to cause this function to return the
// size of the latest error message. Then allocate a char array and call again to get the
// actual error. Or just use a biggish string (256 should be good). Make sure you pass in the
// actual size of the string for buffer_size to prevent overflows.
LTC_CONTROLLER_COMM_API int LccGetErrorInfo(LccHandle handle, char* message_buffer,
                                            int buffer_size);

// Bulk data transfer functions

// Enables byte swapping on data send and receive functions so that data that is transferred
// Most Significant Byte first is stored correctly. (Default) Note that this assumes a
// little-endian machine (which currently includes all Windows desktops.)
LTC_CONTROLLER_COMM_API int LccDataSetHighByteFirst(LccHandle handle);

// Disables byte swapping on data send and receive functions so that data that is transferred
// Least Significant Byte first is stored correctly. Note that this assumes a little-endian
// machine (which currently includes all Windows desktops.)
LTC_CONTROLLER_COMM_API int LccDataSetLowByteFirst(LccHandle handle);

// Send a stream of bytes.
// Only used with HighSpeed controllers.
LTC_CONTROLLER_COMM_API int LccDataSendBytes(LccHandle handle, uint8_t* values, int num_values,
                                             int* num_sent);

// Receive a stream of bytes.
LTC_CONTROLLER_COMM_API int LccDataReceiveBytes(LccHandle handle, uint8_t* values,
                                                int num_values, int* num_received);

// Send a stream of 16 bit values.
// Only used with HighSpeed controllers.
LTC_CONTROLLER_COMM_API int LccDataSendUint16Values(LccHandle handle, uint16_t* values,
                                                    int num_values, int* num_bytes_sent);

// Receive a stream of 16 bit values.
LTC_CONTROLLER_COMM_API int LccDataReceiveUint16Values(LccHandle handle, uint16_t* values,
                                                       int num_values, int* num_bytes_received);

// Send a stream of 32 bit values.
// Only used with HighSpeed controllers.
LTC_CONTROLLER_COMM_API int LccDataSendUint32Values(LccHandle handle, uint32_t* values,
                                                    int num_values, int* num_bytes_sent);

// Receive a stream of 32 bit values.
LTC_CONTROLLER_COMM_API int LccDataReceiveUint32Values(LccHandle handle, uint32_t* values,
                                                       int num_values, int* num_bytes_received);

// Start an ADC collection, works with DC1371, DC890, DC718
LTC_CONTROLLER_COMM_API int LccDataStartCollect(LccHandle handle, int total_samples,
                                                int trigger);

// Check if the ADC collection (DC1371, DC890, DC718)
// returns an error if you didn't call LccDataStartCollect first
LTC_CONTROLLER_COMM_API int LccDataIsCollectDone(LccHandle handle, bool* is_done);

// Cancel a pending collection, note this function must be called to cancel a pending collect
// OR if a collect has finished but you do not read the full collection of data.
LTC_CONTROLLER_COMM_API int LccDataCancelCollect(LccHandle handle);

// ADC collection characteristics (DC718 and DC890 only)
LTC_CONTROLLER_COMM_API int LccDataSetCharacteristics(LccHandle handle, bool is_multichannel,
                                                      int sample_bytes, bool is_positive_clock);

// SPI functions
// The next three functions lower chip select, perform their function, and raise chip select.

// Send arbitrary bytes over SPI
// Not used with DC718. Will cause a bunch of ineffective I2C traffic on a DC890 if the
// demo-board does not have an I/O expander.
LTC_CONTROLLER_COMM_API int LccSpiSendBytes(LccHandle handle, uint8_t* values, int num_values);

// Receive arbitrary bytes over SPI
// Not used with DC718 or DC890.
LTC_CONTROLLER_COMM_API int LccSpiReceiveBytes(LccHandle handle, uint8_t* values,
                                               int num_values);

// Transceive arbitrary bytes over SPI
// Not used with DC718 or DC890.
LTC_CONTROLLER_COMM_API int LccSpiTransceiveBytes(LccHandle handle, uint8_t* send_values,
                                                  uint8_t* receive_values, int num_values);

// Convenience SPI functions with address
// Many (but not all) LTC products with a SPI interface use a "register map" convention where
// SPI commands are used to set a value in one of several registers. In this case the SPI
// command starts with the register address. These functions make it easy to send a single
// address byte and one or more data bytes without having to concatenate them first. Note
// that some parts have a read/write bit as the most significant bit in the address, while
// others have it in the least significant bit. These functions require the user to do any
// shifting and masking of bits to get the correct address byte. It is recomended that code
// for specific parts make new functions that do the masking of the address bytes and then
// delegate to these functions. These functions also handle chip select at the begining and
// end of the transaction.

// Send an address byte and data byte over SPI
// Not used with DC718. Will cause a bunch of ineffective I2C traffic on a DC890 if the
// demo-board does not have an I/O expander.
LTC_CONTROLLER_COMM_API int LccSpiSendByteAtAddress(LccHandle handle, uint8_t address,
                                                    uint8_t value);

// Send an address byte and multiple data bytes over SPI
// Not used with DC718. Will cause a bunch of ineffective I2C traffic on a DC890 if the
// demo-board does not have an I/O expander.
LTC_CONTROLLER_COMM_API int LccSpiSendBytesAtAddress(LccHandle handle, uint8_t address,
                                                     uint8_t* values, int num_values);

// Send an address byte and receive a data byte over SPI
// Not used with DC718 or DC890
LTC_CONTROLLER_COMM_API int LccSpiReceiveByteAtAddress(LccHandle handle, uint8_t address,
                                                       uint8_t* value);

// Send an address byte and receive multiple data bytes over SPI
// Not used with DC718 or DC890
LTC_CONTROLLER_COMM_API int LccSpiReceiveBytesAtAddress(LccHandle handle, uint8_t address,
                                                        uint8_t* values, int num_values);

// Low level SPI functions
// All the above SPI functions are built on top of these three functions, they allow full
// control over chip select, independent of the transactions.

// Set the SPI chip select high or low
// Not used with DC718. Will cause a bunch of ineffective I2C traffic on a DC890 if the
// demo-board does not have an I/O expander.
LTC_CONTROLLER_COMM_API int LccSpiSetCsState(LccHandle handle, int chip_select_state);

// Send arbitrary bytes over SPI
// Not used with DC718. Will cause a bunch of ineffective I2C traffic on a DC890 if the
// demo-board does not have an I/O expander.
LTC_CONTROLLER_COMM_API int LccSpiSendNoChipSelect(LccHandle handle, uint8_t* values,
                                                   int num_values);

// Receive arbitrary bytes over SPI
// Not used with DC718 or DC890.
LTC_CONTROLLER_COMM_API int LccSpiReceiveNoChipSelect(LccHandle handle, uint8_t* values,
                                                      int num_values);

// Transceive arbitrary bytes over SPI
// Not used with DC718 or DC890.
LTC_CONTROLLER_COMM_API int LccSpiTransceiveNoChipSelect(LccHandle handle,
                                                         uint8_t * send_values, uint8_t* receive_values, int num_values);

// Fpga functions

// Check if a particular FPGA file is loaded. fpga_filename is the base name, without extension
// and without a revision ('r' followed by a number) so it ends up being something like 'DCMOS'
// or 'S2175' (case insensitive)
// Not used with HighSpeed controllers or DC718
LTC_CONTROLLER_COMM_API int LccFpgaGetIsLoaded(LccHandle handle, const char* fpga_filename,
                                               bool* is_loaded);

// Load a particular FPGA file. fpga_filename is the base name, without extension
// and without a revision ('r' followed by a number) so it ends up being something like 'DCMOS'
// or 'S2175' (case insensitive)
LTC_CONTROLLER_COMM_API int LccFpgaLoadFile(LccHandle handle, const char* fpga_filename);

// Load a particular FPGA file a chunk at a time. fpga_filename is the base name, without
// extension and without a revision ('r' followed by a number) so it ends up being something
// like 'DCMOS' or 'S2175' (case insensitive).
// The first call sets progress to a number, each subsequent call will cause progress to be set
// to a SMALLER number. The process is finished when progress is 0.
LTC_CONTROLLER_COMM_API int LccFpgaLoadFileChunked(LccHandle handle, const char* fpga_filename,
                                                   int* progress);

// Call this function if you abandon loading the FPGA file before all chunks are loaded.
LTC_CONTROLLER_COMM_API int LccFpgaCancelLoad(LccHandle handle);

// Read the demo-board EEPROM
LTC_CONTROLLER_COMM_API
int LccEepromReadString(LccHandle handle, char* buffer, int buffer_size);

///////////////////////////////////////////////////////////////////////////
// Functions for high speed commercial FPGA demo-board based controllers //
///////////////////////////////////////////////////////////////////////////

// Clear any data in the I/O buffers.
LTC_CONTROLLER_COMM_API int LccHsPurgeIo(LccHandle handle);

// For FIFO communication use BIT_MODE_FIFO, for everything else use BIT_MODE_MPSSE.
LTC_CONTROLLER_COMM_API int LccHsSetBitMode(LccHandle handle, int mode);

// Before communicating with FPGA registers this function must be called to initialize the
// FPGA
LTC_CONTROLLER_COMM_API int LccHsFpgaToggleReset(LccHandle handle);

// Sets the FPGA address for all future reads and writes, until set to something else.
LTC_CONTROLLER_COMM_API int LccHsFpgaWriteAddress(LccHandle handle, uint8_t address);

// Writes a byte to the previously set FPGA address
LTC_CONTROLLER_COMM_API int LccHsFpgaWriteData(LccHandle handle, uint8_t value);

// Reads a byte from the previously set FPGA address
LTC_CONTROLLER_COMM_API int LccHsFpgaReadData(LccHandle handle, uint8_t* value);

// Sets the address and writes a byte to it. Subsequent reads and writes will continue to go
// to the new address.
LTC_CONTROLLER_COMM_API int LccHsFpgaWriteDataAtAddress(LccHandle handle, uint8_t address,
                                                        uint8_t value);

// Sets the address and reads a byte from it. Subsequent reads and writes will continue to go
// to the new address.
LTC_CONTROLLER_COMM_API int LccHsFpgaReadDataAtAddress(LccHandle handle, uint8_t address,
                                                       uint8_t* value);

// GPIO functions
// These function are generally not used because the GPIO lines are used for SPI and FPGA
// communication.

LTC_CONTROLLER_COMM_API int LccHsGpioWriteHighByte(LccHandle handle, uint8_t value);

LTC_CONTROLLER_COMM_API int LccHsGpioReadHighByte(LccHandle handle, uint8_t* value);

LTC_CONTROLLER_COMM_API int LccHsGpioWriteLowByte(LccHandle handle, uint8_t value);

LTC_CONTROLLER_COMM_API int LccHsGpioReadLowByte(LccHandle handle, uint8_t* value);

// Default FPGA register for the bit-banged I2C is 0x11 use this function to change it.
LTC_CONTROLLER_COMM_API int LccHsFpgaEepromSetBitBangRegister(LccHandle handle,
                                                              uint8_t register_address);

///////////////////////////
// Functions for DC1371A //
///////////////////////////

// This is always 0, so you never need to call this function
LTC_CONTROLLER_COMM_API int Lcc1371SetGenericConfig(LccHandle handle, uint32_t generic_config);

// The value for demo_config is demo-board dependent.
LTC_CONTROLLER_COMM_API int Lcc1371SetDemoConfig(LccHandle handle, uint32_t demo_config);

// Set the chip select used to be LCC_1371_CHIP_SELECT_ONE or LCC_1371_CHIP_SELECT_TWO
// ONE is the most common value and is used if this function is never called.
LTC_CONTROLLER_COMM_API int Lcc1371SpiChooseChipSelect(LccHandle handle, int new_chip_select);

/////////////////////////
// Functions for DC890 //
/////////////////////////

// These functions control the I2C I/O expander present on some DC890 compatible demo-boards
// They are used to set certain lines, and the SPI functions use them under the hood to do
// bit-banged SPI. (The DC890 doesn't actually have a SPI interface.)

// Set the base-byte. This can be used to set the GPIO outputs and is also used by the
// bit-banged SPI commands, all bits besides CS, SCK and SDI are set according to this byte
// at all times during the SPI transaction.
LTC_CONTROLLER_COMM_API int Lcc890GpioSetByte(LccHandle handle, uint8_t byte);

// Tells the bit-banged SPI routine which bit to use for CS, SCK and SDI. This MUST be called
// before any SPI routines are called when using the DC890.
LTC_CONTROLLER_COMM_API int Lcc890GpioSpiSetBits(LccHandle handle, int cs_bit,
                                                 int sck_bit, int sdi_bit);

// Flush commands and clear IO buffers
LTC_CONTROLLER_COMM_API int Lcc890Flush(LccHandle handle);

#ifdef __cplusplus
}
#endif