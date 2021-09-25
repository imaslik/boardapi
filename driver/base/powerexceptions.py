class FpgaException(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class OpenFtdiException(Exception):
    def __init__(self):
        pass

    def __str__(self):
        return "Open FTDI device by SN failed."


class ResetFtdiException(Exception):
    def __init__(self):
        pass

    def __str__(self):
        return "Reset FTDI device failed"


class WritingDataFtdiException(Exception):
    def __init__(self):
        pass

    def __str__(self):
        return "Writing data to FTDI device failed"


class CloseFtdiException(Exception):
    def __init__(self):
        pass

    def __str__(self):
        return "Close to FTDI device failed"


class FileSizeException(Exception):
    def __init__(self):
        pass

    def __str__(self):
        return "File size larger then 65500 bytes"


class GetStatusException(Exception):
    def __init__(self):
        pass

    def __str__(self):
        return "Get Status of FTDI device failed"


class ReportedSendDataException(Exception):
    def __init__(self):
        pass

    def __str__(self):
        return "Error while writing data to FTDI device. Sent x bytes, reported y"


class CpldCommunicationException(Exception):
    def __init__(self):
        pass

    def __str__(self):
        return "No Data sent back from CPLD.\nCPLD communication failed"


class CpldSendDataException(Exception):
    def __init__(self):
        pass

    def __str__(self):
        return "No Data sent back from CPLD.\nCPLD sent unexpected ACK data value"


class FpgaConfigurationException(Exception):
    def __init__(self):
        pass

    def __str__(self):
        return "FPGA configuration completed with failure!!"


class FtSetBaudRateException(Exception):
    def __init__(self):
        pass

    def __str__(self):
        return "FT_SetBaudRate error"


class FtSetDataCharacteristicsException(Exception):
    def __init__(self):
        pass

    def __str__(self):
        return "FT_SetDataCharacteristics error"


class FtSetFlowControlException(Exception):
    def __init__(self):
        pass

    def __str__(self):
        return "FT_SetFlowControl error"


class FtSetTimeoutsException(Exception):
    def __init__(self):
        pass

    def __str__(self):
        return "FT_SetTimeouts error"


class UsbConnectivityException(Exception):
    def __init__(self):
        pass

    def __str__(self):
        return "No Devices Found. Check Your USB Connectivity"


class Exception_FT_IO_ERROR(Exception):
    def __init__(self):
        pass

    def __str__(self):
        return "FT_IO_ERROR\n"


class Exception_FT_DEVICE_NOT_FOUND(Exception):
    def __init__(self):
        pass

    def __str__(self):
        return "FT_DEVICE_NOT_FOUND\n"


class Exception_FT_OTHER_ERROR(Exception):
    def __init__(self):
        pass

    def __str__(self):
        return "FT_OTHER_ERROR\n"


class Exception_FT_INVALID_HANDLE(Exception):
    def __init__(self):
        pass

    def __str__(self):
        return "FT_INVALID_HANDLE\n"


class CantReadLiteIgniteException(Exception):
    def __init__(self, message):
        self.message = message
        pass

    def __str__(self):
        return "FT_INVALID_HANDLE" + self.message + "\n"
