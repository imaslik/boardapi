from __future__ import absolute_import
import ctypes
from sys import *
import os
import ast
from driver.base import fpga
import time
import csv
from datetime import datetime
try:
    from tabulate import tabulate
except ImportError as e:
    try:
        import pip
    except ImportError as e:
        getpip.install_pip()
    finally:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--proxy=https://proxy-chain.intel.com:911", "tabulate"])
finally:
    from tabulate import tabulate


if platform == "win32" or platform == "cli":
    site_root = os.path.dirname(os.path.realpath(__file__))
    parent_root = os.path.abspath(os.path.join(site_root, os.pardir))
    path.append(parent_root)
    path.append(site_root)
    path.append(os.path.join(site_root, "base"))
    path.append(os.path.join(site_root, "powerconfiguration"))
    path.append(os.path.join(site_root, "powerconfiguration", "powerrails"))
elif platform == "linux":
    path.append('/home/laduser/boardserver/driver/powerconfiguration/powerrails')
    path.append('/home/laduser/boardserver/driver/powerconfiguration')
    path.append('/home/laduser/boardserver/driver/base')
    path.append('/home/laduser/boardserver/driver')
    path.append('/home/laduser/boardserver')

from driver.base.ftdidetecteddevices import *
from driver.base.fpga import FTDI
from driver.base.flash import *
from driver.base.powerexceptions import *
from driver.powerconfiguration.powerrails.pmbusrail import *
from driver.powerconfiguration.powerrails.rdacrail import *
from driver.powerconfiguration.powerenums import *

ftdi_devices = FTDIDetectedDevices()


def swapbytehex(data=0):
    a = (data & 0x00FF) << 8
    b = (data & 0xFF00) >> 8
    data_out = format((a + b), '04x')
    return data_out


def twos_complement(hexstr, bits):
    value = int(hexstr, 16)
    if value & (1 << (bits - 1)):
        value -= 1 << bits
    return value


def safe_cast(val, to_type, default=None):
    try:
        return to_type(val)
    except (ValueError, TypeError):
        return default


class BoardBaseError(Exception):
    """Exception class for status messages"""

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


def _get_config_file():
    file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "powerconfiguration", "powerrails", "PisgahMEVConfiguration.json")

    if os.path.exists(file_path):
        return file_path
    return None


class BoardBase:
    def __init__(self, board_name=None, handle=None):
        self.board_configurations = None
        ftdi_object = None
        if handle is not None:
            ftdi_object = ftd2xx.FTD2XX(handle)
        else:
            ftdi_object, ftdi_index = self._get_ftdi(board_name)
        self.config_file = _get_config_file()
        self.ftdi = FTDI(ftdi_object, ftdi_index)
        self.ftdi.close()
        self._fpga = FPGA()
        self._flash = Flash()
        self.rails = {}
        self._ppm_bits = {
            "0000": 6.25,
            "0001": 10,
            "0002": 12.5,
            "0003": 25,
            "0004": 50,
            "0005": 80,
            "0006": 100,
            "0007": 125,
            "0008": 150,
            "0009": 200,
            "000A": 400,
            "000B": 600,
            "000C": 800,
            "000D": 1200,
            "000E": 1600,
            "000F": 3200
        }
        self.set_rails()

    @staticmethod
    def _get_ftdi(board_name):
        try:
            if board_name is None:
                device_info = next((device for device in ftdi_devices.devices_info if str(device['description'].decode()).upper().endswith(" B")),
                     False)
                board_name = ''
            else:
                device_info = next((device for device in ftdi_devices.devices_info if board_name == device['serial'].decode()),
                                   False)
                if device_info:
                    return ftd2xx.open(device_info['index']), device_info['index']
                device_info = next((device for device in ftdi_devices.devices_info if board_name == device['description'].decode()),
                                   False)
            if device_info:
                return ftd2xx.open(device_info['index']), device_info['index']
            raise BoardBaseError("Not found connected board with " + board_name)
        except ftd2xx.DeviceError as e:
            raise BoardBaseError(e.message)

    def set_rails(self, conf=None):
        try:
            if conf is None:
                if self.config_file is None:
                    raise Exception("Configuration file not exists")

                with open(self.config_file, "r") as fileRead:
                    conf = ast.literal_eval(fileRead.read())
            self.board_configurations = conf["Board"]
            self.rails = {}
            for rail_info in conf["Rails"]:
                rail_name = rail_info["RailName"]
                power_type = PowerManagementType[rail_info["PowerType"].upper()]
                if power_type == PowerManagementType.PMBUS:
                    self.rails[rail_name] = PmbusRail(self.ftdi, self.board_configurations, rail_name)
                    self.rails[rail_name].rail_page_number = rail_info["RailPageNumber"]
                    self.rails[rail_name].pmbus_address = rail_info["PmbusAddress"]
                    self.rails[rail_name].margining_enable_for_pmbus = rail_info["MarginingEnableForPmbus"]
                    self.rails[rail_name].i_read_factor = safe_cast(rail_info["IReadFactor"], float, 0.0)
                    self.rails[rail_name].read_i_out_address = rail_info["ReadIOUTAddress"]
                elif power_type == PowerManagementType.RDAC:
                    self.rails[rail_name] = RdacRail(self.ftdi,self.board_configurations, rail_name)
                    self.rails[rail_name].voltage_default_set = safe_cast(rail_info["VoltageDefaultSet"], float, 0.0)
                    self.rails[rail_name].vref = safe_cast(rail_info["VRef"], float, 0.0)
                    self.rails[rail_name].rdac_address = rail_info["RDacAddress"]
                    self.rails[rail_name].i_read_method = rail_info["IReadMethod"]
                    self.rails[rail_name].i_read_address = rail_info["IReadAddress"]
                    if "MaxValue" in rail_info:
                        self.rails[rail_name].max_value = safe_cast(rail_info["MaxValue"], int, 0)
                    if "RDown" in rail_info:
                        self.rails[rail_name].r_down = safe_cast(rail_info["RDown"], float, 0.0)
                    if "RUp" in rail_info:
                        self.rails[rail_name].r_up = safe_cast(rail_info["RUp"], float, 0.0)
                    if "VReadMethod" in rail_info:
                        self.rails[rail_name].v_read_method = rail_info["VReadMethod"]
                    if "VReadAddress" in rail_info:
                        self.rails[rail_name].v_read_address = rail_info["VReadAddress"]
                    if "VReadPort" in rail_info:
                        self.rails[rail_name].v_read_port = safe_cast(rail_info["VReadPort"], int, 0)
                    if "VReadVref" in rail_info:
                        self.rails[rail_name].v_read_vref = safe_cast(rail_info["VReadVref"], float, 0.0)
                    if "IReadVref" in rail_info:
                        self.rails[rail_name].i_read_vref = safe_cast(rail_info["IReadVref"], float, 0.0)
                    if "IReadMode" in rail_info:
                        self.rails[rail_name].i_read_mode = rail_info["IReadMode"]
                    if "IReadRsense" in rail_info:
                        self.rails[rail_name].i_read_rsense = safe_cast(rail_info["IReadRsense"], float, 0.0)
                    if "IReadLinear" in rail_info:
                        self.rails[rail_name].i_read_linear = safe_cast(rail_info["IReadLinear"], float, 0.0)
                    if "IReadProportional" in rail_info:
                        self.rails[rail_name].i_read_proportional = safe_cast(rail_info["IReadProportional"], float, 0.0)
                else:
                    raise Exception("Power type " + self.rails[rail_name].power_type + " is not exists")

                self.rails[rail_name].power_type = power_type
                self.rails[rail_name].voltage_read_resolution = safe_cast(rail_info["VoltageReadResolution"], float,
                                                                          0.0)
                self.rails[rail_name].rail_number = safe_cast(rail_info["RailNumber"], int, 0)
                self.rails[rail_name].sequence = rail_info["Sequence"]
                self.rails[rail_name].sequence_address = rail_info["SequenceAddress"]
                self.rails[rail_name].delay = safe_cast(rail_info["Delay"], int, 0)
                self.rails[rail_name].delay_time_type = DelayTimeType[rail_info["DelayTimeType"].upper()]
                self.rails[rail_name].delay_address = rail_info["DelayAddress"]
                self.rails[rail_name].max_voltage = safe_cast(rail_info["MaxVoltage"], float, 0.0)
                self.rails[rail_name].min_voltage = safe_cast(rail_info["MinVoltage"], float, 0.0)
                self.rails[rail_name].max_current = safe_cast(rail_info["MaxCurrent"], float, 0.0)
                self.rails[rail_name].min_current = safe_cast(rail_info["MinCurrent"], float, 0.0)
                self.rails[rail_name].current_monitoring = CurrentMonitoringMethod[
                    rail_info["CurrentMonitoring"].upper()]
                self.rails[rail_name].current_read_resolution = safe_cast(rail_info["CurrentReadResolution"], float,
                                                                          0.0)
                self.rails[rail_name].current_adc_address = safe_cast(rail_info["CurrentAdcAddress"], int, 0)
                self.rails[rail_name].i2c_mux_address = rail_info["I2CMuxAddress"]
                self.rails[rail_name].power_good_address = rail_info["PowerGoodAddress"]
                self.rails[rail_name].power_good_status_bit = rail_info["PowerGoodStatusBit"]
                self.rails[rail_name].enable_address = rail_info["EnableAddress"]
                self.rails[rail_name].fault_status_address = rail_info["FaultStatusAddress"]
        except Exception as e:
            raise BoardBaseError(e.message)

    def get_board_info(self):
        return self.ftdi.object.__dict__

    def read_all_rail_voltage(self):
        for rail_name in self.rails:
            print(f"{rail_name} voltage: "+ str(self.rails[rail_name].get_voltage()))
            
    def read_all_rail_current(self):
        for rail_name in self.rails:
            print(f"{rail_name} current: "+ str(self.rails[rail_name].get_current()))


    def read_measurement_loop(self, time_run, type, rail_names=None, time_sleep=0):
        time_run = float(time_run)
        os.system('clear')
        self.ftdi.open()
        counter = 0

        header = list(self.rails.keys())
        if rail_names != None and rail_names != "":
            header = rail_names.split()

        full_data = []
        #rails = [rail for rail in self.rails if rail.rail_name in header]
        while time_run > 0:
            counter += 1
            data = []

            start = time.perf_counter()
            print(f"time run: {time_run}")
            for rail_name in header:
                if type == "voltage":
                    data.append(str(self.rails[rail_name].get_voltage(ActionTypeFPGA.NOTHING)))
                elif type == "current":
                     data.append(str(self.rails[rail_name].get_current(ActionTypeFPGA.NOTHING)))
                else:
                    break
                #print(f"{rail_name} voltage: "+ str(self.rails[rail_name].get_voltage(ActionTypeFPGA.NOTHING)))
            #self.read_all_rail_voltage()
            
            full_data.append(data)
            #print("================================")
            end = time.perf_counter()
            
            time_diff = end-start
            if time_sleep != 0 and int(time_sleep) - (end-start) > 0:
                time_diff = int(time_sleep)
                time.sleep(float(int(time_sleep) - (end-start)))

            time_run =time_run-time_diff
            #os.system('clear')
        self.ftdi.close()
        print(tabulate(full_data, headers=header))
        cur_time = datetime.utcnow().strftime('%Y%m%d%H%M%S%f')[:-3]
        file_name = f"voltages_{cur_time}.csv"
        with open(file_name, 'w', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)

            # write the header
            writer.writerow(header)

            # write multiple rows
            writer.writerows(full_data)

    def write_fpga(self, address, data):
        """

        :param address:
        :type data: str
        :param data:
        """
        try:
            action_type = ActionTypeFPGA.CLOSE
            if self.ftdi.object.status == 0:
                action_type = ActionTypeFPGA.OPENCLOSE
            self._fpga.write_to_fpga_memory(self.ftdi, address, data, action_type=action_type)
        except FpgaException as e:
            raise BoardBaseError(e.message)

    def read_fpga(self, address):
        try:
            action_type = ActionTypeFPGA.CLOSE
            if self.ftdi.object.status == 0:
                action_type = ActionTypeFPGA.OPENCLOSE
            self._fpga.read_from_fpga_memory(self.ftdi, address, 1, action_type=action_type)
            return self._fpga.Dword_From_FPGA
        except FpgaException as e:
            raise BoardBaseError(e.message)

    def read_i2c(self, dev_address, reg_address, num_of_bytes, num_pre_write_bytes):
        try:
            self.ftdi.open()
            return self._fpga.read_i2c_dev(self.ftdi, dev_address, reg_address, num_of_bytes, num_pre_write_bytes)
            self.ftdi.close()
        except FpgaException as e:
            raise BoardBaseError(e.message)

    def write_i2c(self, dev_address, reg_address, data, num_of_bytes, num_pre_write_bytes):
        try:
            self.ftdi.open()
            self._fpga.write_i2c_dev(self.ftdi, dev_address, reg_address, data, num_of_bytes, num_pre_write_bytes)

        except FpgaException as e:
            try:
                print("Write I2C again, dev_address: " + dev_address + " reg_address: " + reg_address +
                      " data: " + data + " num_of_bytes: " + str(num_of_bytes) +
                      " num_pre_write_bytes: " + str(num_pre_write_bytes))
                self._fpga.write_i2c_dev(self.ftdi, dev_address, reg_address, data, num_of_bytes, num_pre_write_bytes)
            except FpgaException as e:
                raise BoardBaseError(e.message)
        self.ftdi.close()

    def read_ad5272(self, dev_address):
        try:
            return self._fpga.read_ad5272(self.ftdi, dev_address)
        except FpgaException as e:
            raise BoardBaseError(e.message)

    def write_ad5272(self, dev_address, rdata, program_eeprom):
        try:
            self._fpga.write_ad5272(self.ftdi, dev_address, rdata, program_eeprom)
        except FpgaException as e:
            raise BoardBaseError(e.message)


    def lan_power_good(self):
        self.write_fpga(self.board_configurations["LanPowerGood"],"0")
        self.write_fpga(self.board_configurations["LanPowerGood"],"1")

    def _power_on_off(self, operation):
        address = self.board_configurations["PowerOnOffReg"]
        if operation == "on":
            value = "1"
        elif operation == "off":
            value = "0"

        self.write_fpga(address, value)

    def power_on(self):
        self._power_on_off("on")

    def power_off(self):
        self._power_on_off("off")

    def get_ppm(self):
        reg2 = str(swapbytehex(int(self.read_i2c(self.board_configurations["ClockPCIePPM"], "2", 2, 1), 16)))
        reg1 = swapbytehex(
            int(self.read_i2c(self.board_configurations["ClockPCIePPM"], "1", 2, 1), 16) & 0xFFF3)  # format(int("00E6", 16) & 0x3FF, "04x")
        reg0 = str(swapbytehex(int(self.read_i2c(self.board_configurations["ClockPCIePPM"], "0", 2, 1), 16)))
        dcxo_frequency = reg1 + reg0
        pull_range = self._ppm_bits[reg2.upper()]
        symbol = (int(dcxo_frequency, 16) >> 25) & 1
        factor = pow(2, 25) - 1 + symbol
        ppm_shift = twos_complement(dcxo_frequency, 26) * pull_range / factor

        return ppm_shift

    def set_ppm(self, ppm):
        last_range = str(self._ppm_bits["000F"])
        if ppm < (-self._ppm_bits["000F"]):
            raise BoardBaseError("Minimum available ppm value is -" + last_range)

        if ppm > self._ppm_bits["000F"]:
            raise BoardBaseError("Maximum available ppm value is " + last_range)

        keys = list(self._ppm_bits.keys())
        keys.sort()

        for bit in keys:
            if self._ppm_bits[bit] >= abs(ppm):
                pull_range = self._ppm_bits[bit]
                reg2 = bit
                break

        factor = pow(2, 25)
        if ppm >= 0:
            factor = factor - 1
        oe_control_enable = 1 << 26
        control_word_value = (int(round((float(ppm) / pull_range * factor))) & 0x3FFFFFF) | oe_control_enable
        reg0 = str(swapbytehex(control_word_value & 0xFFFF))
        reg1 = str(swapbytehex((control_word_value >> 16) & 0xFFFF))
        reg2 = str(swapbytehex(int(reg2, 16)))

        self.write_i2c(self.board_configurations["ClockPCIePPM"], "2", reg2, 2, 1)
        self.write_i2c(self.board_configurations["ClockPCIePPM"], "0", reg0, 2, 1)
        self.write_i2c(self.board_configurations["ClockPCIePPM"], "1", reg1, 2, 1)

    def set_ssc(self, value):
        reg2 = self.read_i2c(self.board_configurations["ClockPCIeGenerator"], "2", 2, 1)

        if str(value) == "OFF":
            data = 1
        elif str(value) == "-0.25%":
            data = 4
        elif str(value) == "-0.5%":
            data = 7
        else:
            raise BoardBaseError("Wrong spread spectrum value")

        reg2 = format((int(reg2, 16) & 0x1FFF) | (data << 13), "04X")
        self.write_i2c(self.board_configurations["ClockPCIeGenerator"], "2", reg2, 2, 1)

    def get_ssc_sw(self):
        return self._get_ssc("2", 13)

    def get_ssc_read(self):
        return self._get_ssc("1", 8)

    def _get_ssc(self, register, shift):
        reg = self.read_i2c(self.board_configurations["ClockPCIeGenerator"], register, 2, 1)
        data = (int(reg, 16) >> shift) & 0x3
        value = "OFF"

        if data == 0:
            value = "-0.25%"
        elif data == 3:
            value = "-0.5%"

        return value

    def burn_flash(self, image_bytes, extension):
        try:
            status, modified_file = self._flash.configure_flash(self.ftdi, image_bytes, extension, True, False)
            if self._flash.write_status != 100:
                raise Exception("Configure flash failed")

            self._flash.verify_flash(self.ftdi, modified_file, extension)
            if self._flash.read_status != 100:
                raise Exception("Verify flash failed")

            if extension.upper() == "POF":
                self.fpga_reconfig()

            return True, "flash burn successfully"

        except Exception as e:
            if extension.upper() == "BIN":
                self._flash.erase_flash(self.ftdi, extension)
            self.cycle_port()
            return False, str(e)

    def erase_flash(self, flash_type):
        try:
            if flash_type.upper() == "SPI":
                extension = "BIN"
            elif flash_type.upper() == "EPCS":
                extension = "POF"
            else:
                raise Exception("Wrong flash type, should be: 'SPI' for 'BIN' files or 'EPCS' for 'POF' files")

            self.open_ftdi()
            print("Start Erase flash")
            self._flash.erase_flash(self.ftdi, extension)
            print("Erase flash success")
            self.close_ftdi()
        except Exception as e:
            print("Erase flash failed. Error: " + str(e))

    def fpga_reconfig(self):
        self.write_fpga("FAC", "1")

    def get_flash_dev_id(self, spi_or_epcs):
        return self._flash.get_flash_dev_id(self.ftdi, spi_or_epcs)

    def identify_epcs(self):
        return  self._flash.identify_epcs(self.ftdi)

    def open_ftdi(self):
        self.ftdi.open()

    def close_ftdi(self):
        self.ftdi.close()

    def cycle_port(self):
        if self.ftdi.object.status == 1:
            self.ftdi.object.cyclePort()
