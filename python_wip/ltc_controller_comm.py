"""This module is a wrapper around ltc_controller_comm.dll

This library provides functions and some constants used to communicate
with the DC1371A, DC718C, DC890B, and high speed commercial FPGA demo-boards
used as controllers for Linear Technology device demo-boards. Note that
there is no open command, the controller is opened automatically as needed.
There is a close method, (except for DC1371) but it is not necessary to call
it, the cleanup method will close the handle. If there is an error or the
close method is called, the device will again be opened automatically as
needed.

To connect do something like this:
    import ltc_controller_comm as lcc
    
    controller_info = None
    for info in lcc.list_controllers():
        # if you know the serial number you want, you could check that here
        # or description like this:
        if info.get_description() == DESIRED_DESCRIPTION:
            # you could use a with statement like the one below to open the
            # device and query it to make sure it is the one you want here
            # or just use the one that matches the serial number or description
            # like this:
            controller_info = info
            break
    if controller_info is None:
        raise HardwareError("could not find compatible controller")

    # you can access and save the description and serial number
    serial_number = controller_info.get_serial_number()
    print serial_number
    
    # open and use the device
    with lcc.Controller(controller_info) as controller:
        # user your controller now
"""

import ctypes as ct
import _winreg
import sys

ERROR_BUFFER_SIZE = 256
SERIAL_NUMBER_BUFFER_SIZE = 16
DESCRIPTION_BUFFER_SIZE = 64

TYPE_NONE = 0x00000000
TYPE_DC1371 = 0x00000001
TYPE_DC718 = 0x00000002
TYPE_DC890 = 0x00000004
TYPE_HIGH_SPEED = 0x00000008
TYPE_UNKNOWN = 0xFFFFFFFF

SPI_CS_STATE_LOW = 0
SPI_CS_STATE_HIGH = 1

TRIGGER_NONE = 0
TRIGGER_START_POSITIVE_EDGE = 1
TRIGGER_DC890_START_NEGATIVE_EDGE = 2
TRIGGER_DC1371_STOP_NEGATIVE_EDGE = 3

DC1371_CHIP_SELECT_ONE = 1
DC1371_CHIP_SELECT_TWO = 2

# mode argument to set_mode. For data (FIFO) communication use BIT_MODE_FIFO, for
# everything else use BIT_MODE_MPSSE
HS_BIT_MODE_MPSSE = 0x02
HS_BIT_MODE_FIFO = 0x40


# non-public method to map a type string to the appropriate c_types type
def _ctype_from_string(type_string):
    if type_string == "Bytes":
        return ct.c_ubyte
    elif type_string == "Uint16Values":
        return ct.c_uint16
    elif type_string == "Uint32Values":
        return ct.c_uint32
    else:
        raise ValueError("Invalid type string")


class HardwareError(RuntimeError):
    """
    Represents errors returned by the controller hardware

    The most common causes are no power, no clock, weak clock, incorrect clock
    and other setup errors.
    """
    pass


class NotSupportedError(HardwareError):
    """
    Raised when a function is called that is not supported by a particular
    controller.
    """
    pass


class LogicError(Exception):
    """
    Raised when a programming error in the python wrapper or dll itself is
    detected. Contact your FAE or FSE to get it resolved.
    """
    pass


class ControllerInfo(ct.Structure):
    """
    Controller info returned by list_controllers
    int type;
    char description[LCC_MAX_DESCRIPTION_SIZE];
    char serial_number[LCC_MAX_SERIAL_NUMBER_SIZE];
    unsigned long id;
    """

    _fields_ = [
        ("_type", ct.c_int),
        ("_description", ct.c_char * DESCRIPTION_BUFFER_SIZE),
        ("_serial_number", ct.c_char * SERIAL_NUMBER_BUFFER_SIZE),
        ("_id", ct.c_ulong)
    ]

    def get_type(self):
        return self._type

    def get_serial_number(self):
        return self._serial_number[:SERIAL_NUMBER_BUFFER_SIZE]

    def get_description(self):
        return self._description[:DESCRIPTION_BUFFER_SIZE]

# non-public DLL loading stuff
_reg_key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\Linear Technology\\LinearLabTools")
_dll_file, _ = _winreg.QueryValueEx(_reg_key, "Location")
_dll_file += "ltc_controller_comm"
_is_64_bit = sys.maxsize > 2 ** 32
if _is_64_bit:
    _dll_file += "64.dll"
else:
    _dll_file += ".dll"

_dll = ct.CDLL(_dll_file)

def list_controllers(controller_type):
    """Returns a list of ControllerInfo structures
    Looks for all attached controllers matching controller_type and puts their info in the list
    controller_type can be a bitwise OR combination of TYPE_* values
    """
    num_controllers = ct.c_int()
    if _dll.LccGetNumControllers(ct.c_int(controller_type), ct.c_int(100),
                                 ct.byref(num_controllers)) != 0:
        raise HardwareError("Could not create controller info list")
    num_controllers = num_controllers.value
    if num_controllers == 0:
        return None
    controller_info_list = (ControllerInfo * num_controllers)()
    if _dll.LccGetControllerList(ct.c_int(controller_type), controller_info_list,
                                 num_controllers) != 0:
        raise HardwareError("Could not get device info list, or no device found")
    return controller_info_list


class Controller(object):
    """This class wraps up the interface to the native DLL.
    
    It manages references to LccHandle and LccControllerInfo and makes all their
    functions available as methods.
    """

    def __init__(self, controller_info):
        """Initialize the controller described by controller_info
        """
        self._handle = ct.c_void_p(None)
        self._c_error_buffer = ct.create_string_buffer(ERROR_BUFFER_SIZE)
        self._c_array = None
        self._c_array_type = "none"
        self._dll = _dll
        if self._dll.LccInitController(ct.byref(self._handle), ct.byref(controller_info)) != 0:
            raise HardwareError("Error initializing the device")

    # support "with" semantics
    def __enter__(self):
        return self

    # support "with" semantics
    def __exit__(self, vtype, value, traceback):
        del vtype
        del value
        del traceback
        self.cleanup()

    # call the C function and raise an exception if the return code indicates an error
    def _call(self, func_name, *args):
        func = getattr(self._dll, 'Lcc' + func_name)
        error_code = func(self._handle, *args)
        if error_code != 0:
            self._dll.LccGetErrorInfo(self._handle, self._c_error_buffer, ERROR_BUFFER_SIZE)
            if error_code == -1:
                raise HardwareError(self._c_error_buffer.value)
            elif error_code == -2:
                raise ValueError(self._c_error_buffer.value)
            elif error_code == -3:
                raise LogicError(self._c_error_buffer.value)
            elif error_code == -4:
                raise NotSupportedError(self._c_error_buffer.value)
            else:
                raise RuntimeError(self._c_error_buffer.value)

    def cleanup(self):
        """Clean up (close and delete) all resources."""
        if self._handle is not None:
            self._dll.LccCleanup(ct.byref(self._handle))
            self._handle = None

    def get_serial_number(self):
        """Return the current controller's serial number."""
        c_serial_number = ct.create_string_buffer(SERIAL_NUMBER_BUFFER_SIZE)
        self._call('GetSerialNumber', c_serial_number, SERIAL_NUMBER_BUFFER_SIZE)
        return c_serial_number.value

    def get_description(self):
        """Return the current controller's description."""
        c_description = ct.create_string_buffer(DESCRIPTION_BUFFER_SIZE)
        self._call('GetDescription', c_description, DESCRIPTION_BUFFER_SIZE)
        return c_description.value

    def reset(self):
        """Reset the controller, not used with High Speed controllers"""
        self._call('Reset')

    def close(self):
        """Close device. Device will be automatically re-opened when needed."""
        self._call('Close')

    def data_set_high_byte_first(self):
        """Make calls to data_[send/receive]_uint[16/32]_values send/receive high byte first.
        
        Enables byte swapping on data send and receive functions so that data that is transferred
        Most Significant Byte first is stored correctly. (Default) Note that this assumes a
        little-endian machine (which currently includes all Windows desktops.)"""
        self._call('DataSetHighByteFirst')

    def data_set_low_byte_first(self):
        """Make calls to data_[send/receive]_uint[16/32]_values send/receive low byte first.
        Disables byte swapping on data send and receive functions so that data that is transferred
        Least Significant Byte first is stored correctly. Note that this assumes a little-endian 
        machine (which currently includes all Windows desktops.)
        """
        self._call('DataSetLowByteFirst')

    # send data of various types
    def _data_send_by_type(self, type_string, values, start, end):
        if start < 0:
            raise ValueError("start must be >= 0")
        if end < 0:
            end = len(values) + end + 1
        if end <= start:
            raise ValueError("end must be > start")

        num_values = end - start

        if self._c_array_type != type_string or len(self._c_array) < num_values:
            ctype = _ctype_from_string(type_string)
            c_array_type = ctype * num_values
            # noinspection PyCallingNonCallable
            self._c_array = c_array_type()
            self._c_array_type = type_string

        for i in xrange(0, num_values):
            self._c_array[i] = values[i + start]

        c_num_values = ct.c_int(num_values)
        c_num_transfered = ct.c_int()

        self._call('DataSend' + type_string, self._c_array, c_num_values, ct.byref(c_num_transfered))

        return c_num_transfered.value

    def data_send_bytes(self, values, start=0, end=-1):
        """Send elements of values[start:end] as bytes.
        
        Only used with high_speed controllers.
        Defaults for start and end and interpretation of negative values is
        the same as for slices.
        """
        return self._data_send_by_type("Bytes", values, start, end)

    def data_send_uint16_values(self, values, start=0, end=-1):
        """Send elements of values[start:end] as 16-bit values.
        
        Only used with high_speed controllers.
        Defaults for start and end and interpretation of negative values is
        the same as for slices.
        """
        return self._data_send_by_type("Uint16Values", values, start, end)

    def data_send_uint32_values(self, values, start=0, end=-1):
        """Send elements of values[start:end] as 32-bit values.
        
        Only used with high_speed controllers.
        Defaults for start and end and interpretation of negative values is
        the same as for slices.
        """
        return self._data_send_by_type("Uint32Values", values, start, end)

    # receive FIFO data of various types
    def _data_receive_by_type(self, type_string, values, start, end):
        if values is None and end < 0:
            raise ValueError("If values is None, end cannot be negative")
        if values is None and start != 0:
            raise ValueError("If values is None, start must be 0")
        if start < 0:
            raise ValueError("start must be >= 0")
        if end < 0:
            end = len(values) + end + 1
        if end <= start:
            raise ValueError("end must be > start")

        num_values = end - start

        if self._c_array_type != type_string or len(self._c_array) < num_values:
            ctype = _ctype_from_string(type_string)
            c_array_type = ctype * num_values
            # noinspection PyCallingNonCallable
            self._c_array = c_array_type()
            self._c_array_type = type_string

        c_num_values = ct.c_int(num_values)
        c_num_transfered = ct.c_int()

        self._call('DataReceive' + type_string, self._c_array, c_num_values, ct.byref(c_num_transfered))

        if values is None:
            values = [self._c_array[i + start] for i in xrange(0, num_values)]
        else:
            for i in xrange(0, num_values):
                values[i + start] = int(self._c_array[i])

        return c_num_transfered.value, values

    def data_receive_bytes(self, values=None, start=0, end=-1):
        """Fill values[start:end] with bytes received.
        
        If values is None (default) create a new list. Defaults for start and
        end and interpretation of negative values is the same as for slices.
        Return a reference to values.
        """
        return self._data_receive_by_type("Bytes", values, start, end)

    def data_receive_uint16_values(self, values=None, start=0, end=-1):
        """Fill values[start:end] with 16-bit values received.
        
        If values is None (default) create a new list. Defaults for start and
        end and interpretation of negative values is the same as for slices.
        Return a reference to values.
        """
        return self._data_receive_by_type("Uint16Values", values, start, end)

    def data_receive_uint32_values(self, values=None, start=0, end=-1):
        """Fill values[start:end] with 32-bit values received.
        
        If values is None (default) create a new list. Defaults for start and
        end and interpretation of negative values is the same as for slices.
        Return a reference to values.
        """
        return self._data_receive_by_type("Uint32Values", values, start, end)

    def data_start_collect(self, total_samples, trigger):
        """
        Start an ADC collect into memory, works with DC1371, DC890, DC718.
        total_samples -- Number of samples to collect
        trigger -- Trigger type
        """
        self._call('DataStartCollect', ct.c_int(total_samples), ct.c_int(trigger))

    def data_is_collect_done(self):
        """
        Check if an ADC collect is done, works with DC1371, DC890, DC718
        :return: True if collect done, False otherwise
        """
        is_done = ct.c_bool()
        self._call('DataIsCollectDone', ct.byref(is_done))
        return is_done.value

    def data_cancel_collect(self):
        """Cancel any ADC collect, works with DC1371, DC890, DC718
        Note this function must be called to cancel a pending collect
        OR if a collect has finished but you do not read the full collection of data.
        """
        self._call('DataCancelCollect')

    def data_set_characteristics(self, is_multichannel, sample_bytes, is_positive_clock):
        """
        ADC collection characteristics for DC718 and DC890
        is_multichannel -- True if the ADC has 2 or more channels
        sample_bytes -- The total number of bytes occupied by a sample including
                        alignment and meta data
        is_positive_clock -- True if data is sampled on positive (rising) clock edges
        """
        self._call('DataSetCharacteristics', ct.c_bool(is_multichannel), ct.c_int(sample_bytes),
                   ct.c_bool(is_positive_clock))

    def spi_send_bytes(self, values, start=0, end=-1):
        """Send elements of values[start:end] via SPI controlling chip-select.
        
        Not used with DC718. Will cause a bunch of ineffective I2C traffic on a DC890 if the
        demo-board does not have an I/O expander.
        Defaults for start and end and interpretation of negative values is
        the same as for slices.
        """
        if start < 0:
            raise ValueError("start must be >= 0")
        if end < 0:
            end = len(values) + end + 1
        elif end < start:
            raise ValueError("end must be >= start")

        num_values = end - start

        if self._c_array_type != "ubyte" or len(self._c_array) < num_values:
            # noinspection PyCallingNonCallable
            self._c_array = (ct.c_ubyte * num_values)()

        for i in xrange(0, num_values):
            self._c_array[i] = values[i + start]

        c_num_values = ct.c_int(num_values)
        self._call('SpiSendBytes', self._c_array, c_num_values)

    def spi_receive_bytes(self, values=None, start=0, end=-1):
        """Fill values[start:end] with bytes received via SPI controlling chip-select.
        
        Not used with DC718 or DC890.
        If values is None (default) create a new list. Defaults for start and
        end and interpretation of negative values is the same as for slices.
        Return a reference to values.
        """
        if values is None and end < 0:
            raise ValueError("If values is None, end cannot be -1")
        if values is None and start != 0:
            raise ValueError("If values is None, start must be 0")
        if start < 0:
            raise ValueError("start must be >= 0")
        if end < 0:
            end = len(values) + end + 1
        elif end < start:
            raise ValueError("end must be >= start")

        num_values = end - start

        if self._c_array_type != "ubyte" or len(self._c_array) < num_values:
            # noinspection PyCallingNonCallable
            self._c_array = (ct.c_ubyte * num_values)()

        c_num_values = ct.c_int(num_values)
        self._call('SpiReceiveBytes', self._c_array, c_num_values)

        if values is None:
            values = [self._c_array[i + start] for i in xrange(0, num_values)]
        else:
            for i in xrange(0, num_values):
                values[i + start] = int(self._c_array[i])

        return values

    def spi_transceive_bytes(self, send_values, send_start=0, send_end=-1,
                             receive_values=None, receive_start=0):
        """Transceive bytes via SPI controlling chip-select.
        
        Not used with DC718 or DC890.
        Simultaneously send send_values[send_start:send_end] and fill 
        receive_values[receive_start:receive_end] with bytes received via
        SPI. If receive_values is None (default) create a new list. Defaults
        for (send_/receive_)start and (send_/receive_)end and interpretation
        of negative values are the same as for slices. Return a reference to
        values.
        """
        if send_start < 0:
            raise ValueError("send_start must be >= 0")
        if send_end < 0:
            send_end = len(send_values) + send_end + 1
        if send_end < send_start:
            raise ValueError("send_end must be >= send_start")

        num_values = send_end - send_start

        if receive_start < 0:
            raise ValueError("receive_start must be >= 0")

        if self._c_array_type != "ubyte" or len(self._c_array) < num_values:
            # noinspection PyCallingNonCallable
            self._c_array = (ct.c_ubyte * num_values)()
        for i in xrange(0, num_values):
            self._c_array[i] = send_values[i + send_start]

        c_num_values = ct.c_int(num_values)
        self._call('SpiTransceiveBytes', self._c_array, self._c_array, c_num_values)

        if receive_values is None:
            receive_values = [self._c_array[i + receive_start] for i in xrange(0, num_values)]
        else:
            for i in xrange(0, num_values):
                receive_values[i + receive_start] = int(self._c_array[i])

        return receive_values

    def spi_send_byte_at_address(self, address, value):
        """Write an address and a value via SPI.
        
        Not used with DC718. Will cause a bunch of ineffective I2C traffic on a DC890 if the
        demo-board does not have an I/O expander.
        Many SPI devices adopt a convention similar to I2C addressing, where a
        byte is sent indicating which register address the rest of the data
        pertains to. Often there is a read-write bit in the address, this
        function will not shift or set any bits in the address, it basically
        just writes two bytes, the address byte and data byte one after the
        other.
        """
        c_address = ct.c_uint32(address)
        c_value = ct.c_ubyte(value)
        self._call('SpiSendByteAtAddress', c_address, c_value)

    def spi_send_bytes_at_address(self, address, values, start=0, end=-1):
        """Write an address byte and values[start:end] via SPI.
        
        Not used with DC718. Will cause a bunch of ineffective I2C traffic on a DC890 if the
        demo-board does not have an I/O expander.
        Many SPI devices adopt a convention similar to I2C addressing, where a
        byte is sent indicating which register address the rest of the data
        pertains to. Often there is a read-write bit in the address, this
        function will not shift or set any bits in the address, it basically
        just writes the address byte and data bytes one after the other.
        Defaults for start and end and interpretation of negative values
        are the same as for slices.
        """
        if start < 0:
            raise ValueError("start must be >= 0")
        if end < 0:
            end = len(values) + end + 1
        elif end < start:
            raise ValueError("end must be >= start")

        num_values = end - start

        if self._c_array_type != "ubyte" or len(self._c_array) < num_values:
            # noinspection PyCallingNonCallable
            self._c_array = (ct.c_ubyte * num_values)()
        for i in xrange(0, num_values):
            self._c_array[i] = values[i + start]

        c_num_values = ct.c_int(num_values)
        c_address = ct.c_uint32(address)
        self._call('SpiSendBytesAtAddress', c_address, self._c_array, c_num_values)

    def spi_receive_byte_at_address(self, address):
        """Write an address and receive a value via SPI; return the value.
        
        Not used with DC718 or DC890.
        Many SPI devices adopt a convention similar to I2C addressing, where a
        byte is sent indicating which register address the rest of the data
        pertains to. Often there is a read-write bit in the address, this
        function will not shift or set any bits in the address, it basically
        just writes two bytes, the address byte and data byte one after the
        other.
        """
        c_address = ct.c_uint32(address)
        c_value = ct.c_ubyte()
        self._call('SpiReceiveByteAtAddress', c_address, ct.byref(c_value))
        return c_value.value

    def spi_receive_bytes_at_address(self, address, values=None,
                                     start=0, end=-1):
        """Fill values[start:end] with values received via SPI at an address.
        
        Not used with DC718 or DC890.
        Many SPI devices adopt a convention similar to I2C addressing, where a
        byte is sent indicating which register address the rest of the data
        pertains to. Often there is a read-write bit in the address, this
        function will not shift or set any bits in the address, it basically
        just writes the address byte and data bytes one after the other. 
        Defaults for start and end and interpretation of negative values are 
        the same as for slices. if values is None a new list is created. A 
        reference to values is returned.
        """
        if values is None and end < 0:
            raise ValueError("If values is None, end cannot be -1")
        if start < 0:
            raise ValueError("start must be >= 0")
        if end < 0:
            end = len(values) + end + 1
        elif end < start:
            raise ValueError("end must be >= start")

        num_values = end - start

        if self._c_array_type != "ubyte" or len(self._c_array) < num_values:
            # noinspection PyCallingNonCallable
            self._c_array = (ct.c_ubyte * num_values)()

        c_num_values = ct.c_int(num_values)
        c_address = ct.c_uint32(address)
        self._call('SpiReceiveBytesAtAddress', c_address, self._c_array, c_num_values)

        if values is None:
            values = [self._c_array[i + start] for i in xrange(0, num_values)]
        else:
            for i in xrange(0, num_values):
                values[i + start] = int(self._c_array[i])

        return values

    def spi_set_cs_state(self, chip_select_state):
        """Set the SPI chip-select high or low.
        
        Not used with DC718. Will cause a bunch of ineffective I2C traffic on a DC890 if the
        demo-board does not have an I/O expander."""
        
        c_chip_select = ct.c_int(chip_select_state)
        self._call('SpiSetCsState', c_chip_select)

    def spi_send_no_chip_select(self, values, start=0, end=-1):
        """Send values[start:end] via SPI without controlling chip-select.
        
        Not used with DC718. Will cause a bunch of ineffective I2C traffic on a DC890 if the
        demo-board does not have an I/O expander.
        Defaults for start and end and interpretation of negative values are
        the same as for slices.
        """
        if start < 0:
            raise ValueError("start must be >= 0")
        if end < 0:
            end = len(values) + end + 1
        elif end < start:
            raise ValueError("end must be >= start")

        num_values = end - start

        if self._c_array_type != "ubyte" or len(self._c_array) < num_values:
            # noinspection PyCallingNonCallable
            self._c_array = (ct.c_ubyte * num_values)()

        for i in xrange(0, num_values):
            self._c_array[i] = values[i + start]

        c_num_values = ct.c_int(num_values)
        self._call('SpiSendNoChipSelect', self._c_array, c_num_values)

    def spi_receive_no_chip_select(self, values=None, start=0, end=-1):
        """Fill values[start:end] via SPI without controlling chip-select.
        
        Not used with DC718 or DC890.
        If values is None a new list is created. Defaults for start and end
        and interpretation of negative values are the same as for slices. A
        reference to values is returned.
        """
        if values is None and end < 0:
            raise ValueError("If values is None, end cannot be -1")
        if start < 0:
            raise ValueError("start must be >= 0")
        if end < 0:
            end = len(values) + end + 1
        elif end < start:
            raise ValueError("end must be >= start")

        num_values = end - start

        if self._c_array_type != "ubyte" or len(self._c_array) < num_values:
            # noinspection PyCallingNonCallable
            self._c_array = (ct.c_ubyte * num_values)()

        c_num_values = ct.c_int(num_values)
        self._call('SpiReceiveNoChipSelect', self._c_array, c_num_values)

        if values is None:
            values = [self._c_array[i + start] for i in xrange(0, num_values)]
        else:
            for i in xrange(0, num_values):
                values[i + start] = int(self._c_array[i])

        return values

    def spi_transceive_no_chip_select(self, send_values, send_start=0, send_end=-1,
                                      receive_values=None, receive_start=0):
        """Transceive bytes without controlling chip-select.
        
        Not used with DC718 or DC890.
        Simultaneously send send_values[send_start:send_end] and fill 
        receive_values[receive_start:receive_end] with bytes received via
        SPI. If receive_values is None (default) create a new list. Defaults
        for (send_/receive_)start and (send_/receive_)end and interpretation
        of negative values are the same as for slices. Return a reference to
        values.
        """
        if send_start < 0:
            raise ValueError("send_start must be >= 0")
        if send_end < 0:
            send_end = len(send_values) + send_end + 1
        if send_end <= send_start:
            raise ValueError("send_end must be > send_start")

        num_values = send_end - send_start

        if receive_values is None and send_end < 0:
            raise ValueError("If receive_values is None, receive_end cannot be -1")
        if receive_start < 0:
            raise ValueError("receive_start must be >= 0")

        if self._c_array_type != "ubyte" or len(self._c_array) < num_values:
            # noinspection PyCallingNonCallable
            self._c_array = (ct.c_ubyte * num_values)()
        for i in xrange(0, num_values):
            self._c_array[i] = send_values[i + send_start]

        c_num_values = ct.c_int(num_values)
        self._call('SpiTransceiveNoChipSelect', self._c_array, self._c_array, c_num_values)

        if receive_values is None:
            receive_values = [self._c_array[i + receive_start] for i in xrange(0, num_values)]
        else:
            for i in xrange(0, num_values):
                receive_values[i + receive_start] = int(self._c_array[i])

        return receive_values

    def fpga_get_is_loaded(self, fpga_filename):
        """
        Check if a particular FPGA load is loaded.

        Not used with high_speed controllers or DC718
        fpga_filename -- The base file name without any folder, extension
        or revision info, for instance 'DLVDS' or 'S2175', case insensitive.
        returns True if the requested load is loaded, False otherwise.
        """
        is_loaded = ct.c_bool()
        self._call('FpgaGetIsLoaded', ct.c_char_p(fpga_filename), ct.byref(is_loaded))
        return is_loaded.value
        
    def fpga_load_file(self, fpga_filename):
        """
        Loads an FPGA file
        
        Not used with high_speed controllers or DC718
        fpga_filename -- The base file name without any folder, extension
            or revision info, for instance 'DLVDS' or 'S2175', case insensitive.
        returns True if the requested load is loaded, False otherwise.
        """
        self._call('FpgaLoadFile', ct.c_char_p(fpga_filename))

    def fpga_load_file_chunked(self, fpga_filename):
        """Load a particular FPGA file a chunk at a time. 
        fpga_filename -- The base file name without any folder, extension
            or revision info, for instance 'DLVDS' or 'S2175', case insensitive.
        The first call returns a number, each subsequent call will return a
        SMALLER number. The process is finished when it returns 0.
        """
        progress = ct.c_int()
        self._call('FpgaLoadFileChunked', ct.c_char_p(fpga_filename), ct.byref(progress))
        return progress.value
        
    def fpga_cancel_load(self):
        """Must be called if you abandon loading the FPGA file before complete"""
        self._call('FpgaCancelLoad')
            
    def eeprom_read_string(self, num_chars):
        """Receive an EEPROM string."""
        c_string = ct.create_string_buffer(num_chars+1)
        self._call('EepromReadString', c_string, num_chars+1)
        return c_string.value

    def hs_set_bit_mode(self, mode):
        """Set device mode to MODE_FIFO or MODE_MPSSE."""
        c_mode = ct.c_int(mode)
        self._call('HsSetBitMode', c_mode)

    def hs_purge_io(self):
        """Purge input and output buffers."""
        self._call('HsPurgeIo')

    def hs_fpga_toggle_reset(self):
        """Set the FPGA reset bit low then high."""
        self._call('HsFpgaToggleReset')

    def hs_fpga_write_address(self, address):
        """Set the FPGA address to write or read."""
        c_address = ct.c_ubyte(address)
        self._call('HsFpgaWriteAddress', c_address)

    def hs_fpga_write_data(self, value):
        """Write a value to the current FPGA address."""
        c_value = ct.c_ubyte(value)
        self._call('HsFpgaWriteData', c_value)

    def hs_fpga_read_data(self):
        """Read a value from the current FPGA address and return it."""
        c_value = ct.c_ubyte()
        self._call('HsFpgaReadData', ct.byref(c_value))
        return c_value.value

    def hs_fpga_write_data_at_address(self, address, value):
        """Set the current address and write a value to it."""
        c_address = ct.c_ubyte(address)
        c_value = ct.c_ubyte(value)
        self._call('HsFpgaWriteDataAtAddress', c_address, c_value)

    def hs_fpga_read_data_at_address(self, address):
        """Set the current address and read a value from it."""
        c_address = ct.c_ubyte(address)
        c_value = ct.c_ubyte()
        self._call('HsFpgaReadDataAtAddress', c_address, ct.byref(c_value))
        return c_value.value

    def hs_gpio_write_high_byte(self, value):
        """Set the GPIO high byte to a value."""
        c_value = ct.c_ubyte(value)
        self._call('HsGpioWriteHighByte', c_value)

    def hs_gpio_read_high_byte(self):
        """Read the GPIO high byte and return the value."""
        c_value = ct.c_ubyte()
        self._call('HsGpioReadHighByte', ct.byref(c_value))
        return c_value.value

    def hs_gpio_write_low_byte(self, value):
        """Set the GPIO low byte to a value."""
        c_value = ct.c_ubyte(value)
        self._call('HsGpioWriteLowByte', c_value)

    def hs_gpio_read_low_byte(self):
        """Read the GPIO low byte and return the value"""
        c_value = ct.c_ubyte()
        self._call('HsGpioReadLowByte', ct.byref(c_value))
        return c_value.value

    def hs_fpga_eeprom_set_bit_bang_register(self, register_address):
        """Set the FPGA register used to do bit-banged I2C.
        
        If not called, address used is 0x11.
        """
        c_register_address = ct.c_ubyte(register_address)
        self._call('HsFpgaEepromSetBitBangRegister', c_register_address)

    def dc1371_set_generic_config(self, generic_config):
        """
        generic_config is always 0, so you never have to call this function
        """
        self._call('1371SetGenericConfig', ct.c_uint32(generic_config))

    def dc1371_set_demo_config(self, demo_config):
        """
        Set the value corresponding to the four pairs of hex digits at the end
        of line three of the EEPROM string for a DC1371A demo-board.
        demo_config -- If an ID string were to have 01 02 03 04,
        demo_config would be 0x01020304
        """
        self._call('1371SetDemoConfig', ct.c_uint32(demo_config))

    def dc1371_spi_choose_chip_select(self, new_chip_select):
        """
        Set the chip select to use in future spi commands, 1 (default) is
        correct for most situations, rarely 2 is needed.
        new_chip_select -- 1 (usually) or 2
        """
        self._call('1371SpiChooseChipSelect', ct.c_int(new_chip_select))

    def dc890_gpio_set_byte(self, byte):
        """
        Set the IO expander GPIO lines to byte, all spi transaction use this as
        a base value, or can be used to bit bang lines
        byte -- The bits of byte correspond to the output lines of the IO expander.
        """
        self._call('890GpioSetByte', ct.c_uint8(byte))

    def dc890_gpio_spi_set_bits(self, cs_bit, sck_bit, sdi_bit):
        """
        Set the bits used for SPI transactions, which are performed by
        bit-banging the IO expander on demo-boards that have one. This function
        must be called before doing any spi transactions with the DC890

        cs_bit -- the bit used as chip select
        sck_bit -- the bit used as sck
        sdi_bit -- the bit used as sdi
        """
        self._call('890GpioSpiSetBits', ct.c_int(cs_bit), ct.c_int(sck_bit), ct.c_int(sdi_bit))

    def dc890_flush(self):
        """
        Causes the DC890 to terminate any I2C (or GPIO or SPI) transactions then
        purges the buffers.
        :return: nothing
        """
        self._call('890Flush')
