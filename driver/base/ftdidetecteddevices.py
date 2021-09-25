from __future__ import absolute_import
import sys
import subprocess
from driver import getpip

try:
    import ftd2xx
except ImportError as e:
    try:
        import pip
    except ImportError as e:
        getpip.install_pip()
    finally:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--proxy=https://proxy-chain.intel.com:911", "ftd2xx"])
finally:
    import ftd2xx


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class FTDIDetectedDevices:
    __metaclass__ = Singleton

    def __init__(self):
        self.devices_info = []
        self._load_ftdi_devices()

    def _load_ftdi_devices(self):
        count = ftd2xx.createDeviceInfoList()
        for x in range(0, count):
            info = ftd2xx.getDeviceInfoDetail(x, False)
            self.devices_info.append(info)
