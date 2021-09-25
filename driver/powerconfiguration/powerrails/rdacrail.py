from __future__ import absolute_import
from .baserail import BaseRail, BaseRailError


class RdacRail(BaseRail):
    """description of class"""

    def __init__(self, ftdi, board_configurations, rail_name):
        super(RdacRail, self).__init__(ftdi, board_configurations, rail_name)
        self.voltage_default_set = 0.0  # V SET
        self.vref = 0.0  # V_REF
        self.max_value = 0
        self.r_down = 0.0
        self.r_up = 0.0
        self.rdac_address = 0  # I2C Address ??
        self.v_read_address = ""
        self.v_read_method = ""
        self.v_read_port = 0
        self.v_read_vref = 0.0
        self.i_read_method = ""
        self.i_read_address = ""
        self.i_read_vref = 0.0
        self.i_read_mode = ""
        self.i_read_rsense = ""
        self.i_read_linear = 0.0
        self.i_read_proportional = 0.0

    def get_voltage(self):
        try:
            self._ftdi.open()
            if not self.check_power_good():
                raise Exception(self.rail_name + "rail is off")

            if self.v_read_method.upper() == "AD7998":
                result = self._fpga.read_ad7998(self._ftdi,self.v_read_address, self.v_read_port, self.v_read_vref)
            elif self.v_read_method.upper() == "PMB":
                result = self._fpga.read_ina233a_a2d(self._ftdi, self.i_read_address, self.max_current, self.i_read_rsense, "v")
            # hex_value = self._fpga.read_ad5272(self._ftdi, self.rdac_address)
            # print(hex_value)
            # voltage_value = (
            #         (((((int(hex_value, 16) * 20000) / 1024) + 49.9) / self.voltage_read_resolution) + 1) * self.vref)

            self._ftdi.close()
            return result
        except Exception as e:
            raise BaseRailError(str(e))

    def get_current(self):
        try:
            self._ftdi.open()
            if not self.check_power_good():
                raise Exception(self.rail_name + "rail is off")

            if self.i_read_method.upper() == "ADS1112":
                a2d_value = self._fpga.read_ads11112_a2d(self._ftdi, self.i_read_address, self.i_read_mode, self.i_read_vref)
                return round((a2d_value - self.i_read_linear) * self.i_read_proportional, 3)
            elif self.i_read_method.upper() == "INA233A":
                return self._fpga.read_ina233a_a2d(self._ftdi, self.i_read_address, self.max_current, self.i_read_rsense, "i")
            return 0.0
        except Exception as e:
            raise BaseRailError(str(e))

    def set_voltage(self, voltage_val, correction_set=True):
        try:
            self._ftdi.open()
            if not self.check_power_good():
                raise Exception(self.rail_name + "rail is off")

            data = int((self.r_down * ((voltage_val / self.vref) - 1) - self.r_up) * (self.voltage_read_resolution / self.max_value))
            # data = int(
            #     round((((((voltage_val / self.vref) - 1) * self.voltage_read_resolution) - 49.9) * 1024 / 20000)))
            self._fpga.write_ad5272(self._ftdi, self.rdac_address, data,
                                    False)  # 0x1f0: 3.242V, (0x1C3:3.0V<>0x22: 3.465V)
            self._ftdi.close()
        except Exception as e:
            raise BaseRailError(str(e))

