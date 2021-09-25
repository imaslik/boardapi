from __future__ import absolute_import
from .baserail import BaseRail, BaseRailError
from driver.powerconfiguration.powerenums import *


def convert_twos_complement(num, count_bits):
    bin_str = '{0:b}'.format(num).zfill(count_bits)
    
    if bin_str[0] == '0':
        return int(bin_str, 2)

    converted_str = ''.join('1' if x == '0' else '0' for x in bin_str)
    return -int(converted_str, 2)


class PmbusRail(BaseRail):
    """description of class"""

    def __init__(self, ftdi, board_configurations, rail_name):
        super(PmbusRail, self).__init__(ftdi, board_configurations, rail_name)
        self.rail_page_number = 0
        self.pmbus_address = 0  # PMBUS ADDRESS
        self.margining_enable_for_pmbus = ""
        self.i_read_factor = 0.0
        self.read_i_out_address = ""
        self._page_cmd = '00'
        self._vout_cmd = '21'

    def get_voltage(self):
        try:
            self._ftdi.open()
            if not self.check_power_good():
                raise Exception(self.rail_name + "rail is off")

            self._pmbus_enable_select(True)
            self._fpga.write_i2c_dev(self._ftdi, self.pmbus_address, self._page_cmd, self.rail_page_number, 1,
                                     1)  # change to the right page number
            hex_data = self._fpga.read_i2c_dev(self._ftdi, self.pmbus_address, self._vout_cmd, 2, 1)
            
            voltage_value = float(int(hex_data, 16)) * self.voltage_read_resolution

            self._pmbus_enable_select(False)

            self._ftdi.close()
            return round(voltage_value, 4)
        except Exception as e:
            raise BaseRailError(e.message)

    def get_current(self):
        try:
            self._ftdi.open()
            if not self.check_power_good():
                raise Exception(self.rail_name + "rail is off")

            self._pmbus_enable_select(True)
            self._fpga.write_i2c_dev(self._ftdi, self.pmbus_address, self._page_cmd, self.rail_page_number, 1,
                                     1)  # change to the right page number
            hex_data = self._fpga.read_i2c_dev(self._ftdi, self.pmbus_address, self.read_i_out_address, 2, 1)
           
            #print(hex_data)
            i_11_bit_val = convert_twos_complement(int(hex_data, 16) & 0x3FF, 10)
            #print(i_11_bit_val)
            current_value = i_11_bit_val * self.i_read_factor

            self._pmbus_enable_select(False)

            self._ftdi.close()
            return round(current_value, 4)
        except Exception as e:
            raise BaseRailError(e.message)

    def set_voltage(self, voltage_val, correction_set=True):
        """

        :param voltage_val:
        :param correction_set:
        """
        try:
            self._ftdi.open()
            if not self.check_power_good():
                raise Exception(self.rail_name + "rail is off")

            self._pmbus_enable_select(True)
            self._fpga.write_i2c_dev(self._ftdi, self.pmbus_address, self._page_cmd, self.rail_page_number, 1,
                                     1)  # change to the right page number
            self._fpga.write_i2c_dev(self._ftdi, self.pmbus_address, self._vout_cmd,
                                     str(format(int(round((voltage_val / self.voltage_read_resolution))), 'x')), 2, 1)

            self._pmbus_enable_select(False)
            self._ftdi.close()
        except Exception as e:
            raise BaseRailError(e.message)

    def _pmbus_enable_select(self, en_sel):
        if en_sel:
            self._fpga.write_to_fpga_memory(self._ftdi, self._board_configurations["PMBusMuxEn"], '00000000')  # PM Bus Mux Enabled
            self._fpga.write_to_fpga_memory(self._ftdi, self._board_configurations["PMBusMuxSel"], '00000001')  # PM Bus Mux Selected
        else:
            self._fpga.write_to_fpga_memory(self._ftdi, self._board_configurations["PMBusMuxEn"], '00000001')  # PM Bus Mux Disabled
            self._fpga.write_to_fpga_memory(self._ftdi, self._board_configurations["PMBusMuxSel"], '00000000')  # PM Bus Mux Unselected

