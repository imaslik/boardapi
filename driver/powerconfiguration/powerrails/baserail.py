from __future__ import absolute_import
from abc import ABCMeta, abstractmethod
import driver.base
from driver.powerconfiguration.powerenums import *


class BaseRailError(Exception):
    """Exception class for status messages"""

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class BaseRail:
    """description of class"""
    __metaclass__ = ABCMeta

    def __init__(self, ftdi, board_configurations, rail_name):
        """

        :type ftdi: FTDI
        """
        # fpga
        self._fpga = driver.base.fpga.FPGA()
        self._ftdi = ftdi

        self._board_configurations = board_configurations
        # General Rail Data
        self.rail_name = rail_name
        self.rail_number = 0
        self.voltage_read_resolution = 0.0  # V resolution

        # Sequence
        self.sequence = ""
        self.sequence_address = ""  # Sequence Reg

        # Delay
        self.delay = 0  # in milli seconds? seconds?
        self.delay_address = ""  # Delay reg I2C class
        self.delay_time_type = DelayTimeType.MILISECONDS

        # Voltage
        self.max_voltage = 0.0
        self.min_voltage = 0.0

        # Current
        self.max_current = 0.0  # Max current
        self.min_current = 0.0  # Min current
        self.current_monitoring = CurrentMonitoringMethod.RES  # Current monitoring method: Res/PMBUS/VR
        self.current_read_resolution = 0.0  # Current read resolution
        self.current_adc_address = 0  # Current ADC ADDRESS

        # Registers
        self.power_type = PowerManagementType.RDAC  # PMBUS/RDAC
        self.i2c_mux_address = ""
        self.power_good_address = ""  # Power Good
        self.power_good_status_bit = ""
        self.enable_address = ""  # EN Reg
        self.fault_status_address = ""  # Fault status

    @abstractmethod
    def get_voltage(self):
        pass

    @abstractmethod
    def get_current(self):
        pass

    @abstractmethod
    def set_voltage(self, voltage_val, correction_set=True):
        pass

    def check_power_good(self):

        action_type = ActionTypeFPGA.NOTHING
        #if self._ftdi.object.status == 0:
           # action_type = ActionTypeFPGA.OPENCLOSE
        self._fpga.read_from_fpga_memory(self._ftdi, self.power_good_address, 1, action_type=action_type)
        power_good_data = self._fpga.Dword_From_FPGA
        if "{0:16b}".format(int(power_good_data, 16))[int(self.power_good_status_bit)] == '0':
            return False
        return True
