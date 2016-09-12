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