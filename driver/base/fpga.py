from __future__ import absolute_import
from struct import *
import time
import sys
import subprocess

try:
    import ftd2xx
except ImportError as e:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "ftd2xx"])
finally:
    import ftd2xx

from .powerexceptions import *
from driver.powerconfiguration.powerenums import *

a2d_commnad = {
    "0_minus_1": "8C",
    "0_minus_3": "CC",
    "1_minus_3": "EC",
    "2_minus_3": "AC"
}


def swapbytehex(data=0):
    a = (data & 0x00FF) << 8
    b = (data & 0xFF00) >> 8
    data_out = format((a + b), '04x')
    return data_out


def _get_dwords_counter(hex_data):
    dwords_counter = 1
    if len(hex_data) > 8:
        dwords_counter = len(hex_data) / 8
    return dwords_counter


def get_pos_or_neg_value(num):
    bin_str = '{0:016b}'.format(num)
    if bin_str[0] == '0':
        return int(bin_str, 2)

    converted_str = ''.join('1' if x == '0' else '0' for x in bin_str)
    return int(converted_str, 2) * (-1)


class FTDI:
    def __init__(self, object, index):
        self.object = object
        self.index = index

    def open(self, time_wait=0):
        if self.object.status == 0:
            self.object = ftd2xx.open(self.index)
            self.object.resetDevice()
            time.sleep(time_wait)

    def close(self):
        if self.object.status == 1:
            self.object.close()


class FPGA:
    def __init__(self):
        self._CONST_LI_HEADER_SIZE = 4
        self._USB_TRANSFER_SIZE = 4096
        self._USB_PACKET_SIZE = int(self._USB_TRANSFER_SIZE - 2 * (self._USB_TRANSFER_SIZE / float(64)))
        self._FT_Out_Buffer = None
        self._FT_In_Buffer = bytearray(1048576)
        self._FT_Out_Buffer_Size = 524288
        self._FT_In_Buffer_Size = 65536
        self.Dword_From_FPGA = ""

    def get_ft_output_buffer(self):
        return self._FT_Out_Buffer

    def read_from_fpga_memory(self, ftdi, start_address, num_of_words, offset_fpga=0, address_increment=1,
                              action_type=ActionTypeFPGA.NOTHING):
        """
         :param num_of_words:
         :param start_address:
         :param offset_fpga:
         :param action_type:
         :param address_increment:
         :type ftdi: FTDI
         """
        try:
            if num_of_words > 16383:
                raise FpgaException("Read is limited to 16383 DWords only! Please Fix and retry.")

            self._FT_Out_Buffer = bytearray(12)
            self._create_read_write_packet(1, 0, 0, 8, offset_fpga,
                                           start_address,
                                           address_increment, num_of_dwords=num_of_words)

            if action_type == ActionTypeFPGA.OPENCLOSE or action_type == ActionTypeFPGA.OPEN:
                ftdi.open()

            ftdi.object.setBaudRate(12000000)
            ftdi.object.setDataCharacteristics(8, 0, 0)
            ftdi.object.setFlowControl(0x0100, 0x11, 0x13)
            ftdi.object.setTimeouts(5000, 5000)

            ftdi.object.write(bytes(self._FT_Out_Buffer))
            length_rx_bytes = 0
            for delay_counter in range(0, 50):
                length_rx_bytes = ftdi.object.getQueueStatus()
                time.sleep(0.005)
                if length_rx_bytes == 4 * num_of_words + 2:
                    break
            if length_rx_bytes == 0:
                raise CpldCommunicationException

            read_buffer = ftdi.object.read(int(length_rx_bytes))

            if num_of_words == 1:
                self.Dword_From_FPGA = "0x%08X" % unpack('Icc', read_buffer)[0]
            if num_of_words == 2:
                self.Dword_From_FPGA = "0x%016X" % unpack('Qcc', read_buffer)[0]

            if action_type == ActionTypeFPGA.OPENCLOSE or action_type == ActionTypeFPGA.CLOSE:
                ftdi.close()

            return read_buffer

        except CpldCommunicationException as e:
            raise FpgaException(str(e))
        except CpldSendDataException as e:
            raise FpgaException(str(e))
        except Exception as e:
            raise FpgaException(str(e))

    def write_to_fpga_memory(self, ftdi, start_address, hex_data, offset_fpga=0,
                             action_type=ActionTypeFPGA.NOTHING, address_increment=1):
        """
        :param start_address:
        :param hex_data:
        :type hex_data: str
        :param offset_fpga:
        :param action_type:
        :param address_increment:
        :type ftdi: FTDI
        """
        try:
            dwords_counter = _get_dwords_counter(hex_data)
            body_size_length = (6 + (self._CONST_LI_HEADER_SIZE * dwords_counter))
            body_size_length_bytes = bytearray.fromhex("%04X" % body_size_length)

            length_bytes_to_write = self._CONST_LI_HEADER_SIZE + 6 + (4 * dwords_counter)
            self._FT_Out_Buffer = bytearray(length_bytes_to_write)
            self._create_read_write_packet(2, 0, body_size_length_bytes[0], body_size_length_bytes[1], offset_fpga,
                                           start_address,
                                           address_increment, hex_data)

            hex_format = "%0" + str(dwords_counter * 8) + "X"
            hex_data_bytes = bytearray.fromhex(hex_format % int(hex_data, 16))
            for i in range(0, dwords_counter):
                self._FT_Out_Buffer[10 + 4 * i] = hex_data_bytes[i + 0]
                self._FT_Out_Buffer[11 + 4 * i] = hex_data_bytes[i + 1]
                self._FT_Out_Buffer[12 + 4 * i] = hex_data_bytes[i + 2]
                self._FT_Out_Buffer[13 + 4 * i] = hex_data_bytes[i + 3]

            if action_type == ActionTypeFPGA.OPENCLOSE or action_type == ActionTypeFPGA.OPEN:
                ftdi.open()

            ftdi.object.write(bytes(self._FT_Out_Buffer))
            length_rx_bytes = 0
            for delay_counter in range(0, 100000):
                length_rx_bytes = ftdi.object.getQueueStatus()
                if length_rx_bytes == 2:
                    break
            if length_rx_bytes == 0:
                raise CpldCommunicationException

            read_buffer = bytearray(ftdi.object.read(2))

            # According to LI spec , ack should be AAAA at the end
            if read_buffer[0] != 170 or read_buffer[1] != 170:
                raise CpldSendDataException

            if action_type == ActionTypeFPGA.OPENCLOSE or action_type == ActionTypeFPGA.CLOSE:
                ftdi.close()

        except CpldCommunicationException as e:
            raise FpgaException(str(e))
        except CpldSendDataException as e:
            raise FpgaException(str(e))
        except Exception as e:
            raise FpgaException(str(e))

    def write_to_fpga_memory_burst(self, ftdi, start_address, data_bytes_array, offset_fpga=0,
                                   action_type=ActionTypeFPGA.NOTHING):

        """
        :type ftdi: FTDI
        :type data_bytes_array: bytearray
        """
        try:
            write_status = 0
            no_of_bytes = len(data_bytes_array)
            body_size_length = 6 + no_of_bytes
            body_size_length_bytes = bytearray.fromhex("%06X" % body_size_length)
            length_bytes_to_write = self._CONST_LI_HEADER_SIZE + 6
            self._FT_Out_Buffer = bytearray(length_bytes_to_write)

            self._create_read_write_packet(2, body_size_length_bytes[0], body_size_length_bytes[1],
                                           body_size_length_bytes[2], offset_fpga,
                                           start_address, 0)

            if action_type == ActionTypeFPGA.OPENCLOSE or action_type == ActionTypeFPGA.OPEN:
                ftdi.open()

            ftdi.object.write(bytes(self._FT_Out_Buffer))
            no_of_cycles = int(no_of_bytes / self._FT_Out_Buffer_Size)
            residu_size = no_of_bytes % self._FT_Out_Buffer_Size

            for i in range(1, no_of_cycles + 1):
                write_status = 100 * i / no_of_cycles
                array_offset = (i - 1) * self._FT_Out_Buffer_Size
                current_array = data_bytes_array[array_offset:array_offset + self._FT_Out_Buffer_Size]

                ftdi.object.write(bytes(current_array))
                print("Configure status: " + str(write_status) + "% completed")

            if residu_size > 0:
                skip = no_of_cycles * self._FT_Out_Buffer_Size
                take = skip + residu_size
                current_array = data_bytes_array[skip:]
                ftdi.object.write(bytes(current_array))
                write_status = 100
                print("Configure status: " + str(write_status) + "% completed")

            length_rx_bytes = 0
            for delay_counter in range(0, 100000):
                length_rx_bytes = ftdi.object.getQueueStatus()
                if length_rx_bytes == 2:
                    break
            if length_rx_bytes == 0:
                raise CpldCommunicationException

            read_buffer = bytearray(ftdi.object.read(length_rx_bytes))

            # According to LI spec , ack should be AAAA at the end
            if read_buffer[0] != 170 or read_buffer[1] != 170:
                raise CpldSendDataException

            if action_type == ActionTypeFPGA.OPENCLOSE or action_type == ActionTypeFPGA.CLOSE:
                ftdi.close()

            return write_status
        except CpldCommunicationException as e:
            raise FpgaException(e.message)
        except CpldSendDataException as e:
            raise FpgaException(e.message)
        except Exception as e:
            raise FpgaException(e.message)

    def _create_read_write_packet(self, opcode, body_size_higher_byte, body_size_med_byte, body_size_lower_byte,
                                  offset_fpga, start_address, address_increment, hex_data='0', num_of_dwords=None):

        dwords_counter = _get_dwords_counter(hex_data)
        start_adress_bytes = bytearray.fromhex("%08X" % int(start_address, 16))

        self._FT_Out_Buffer[0] = opcode
        self._FT_Out_Buffer[1] = body_size_higher_byte
        self._FT_Out_Buffer[2] = body_size_med_byte
        self._FT_Out_Buffer[3] = body_size_lower_byte
        self._FT_Out_Buffer[4] = offset_fpga
        self._FT_Out_Buffer[5] = start_adress_bytes[0]
        self._FT_Out_Buffer[6] = start_adress_bytes[1]
        self._FT_Out_Buffer[7] = start_adress_bytes[2]
        self._FT_Out_Buffer[8] = start_adress_bytes[3]
        self._FT_Out_Buffer[9] = address_increment

        if num_of_dwords is not None:
            num_of_dwords_bytes = bytearray.fromhex("%04X" % num_of_dwords)
            self._FT_Out_Buffer[10] = num_of_dwords_bytes[0]
            self._FT_Out_Buffer[11] = num_of_dwords_bytes[1]

    def read_i2c_dev(self, ftdi, dev_address, reg_address, num_of_bytes, num_pre_write_bytes):
        """
        :param reg_address:
        :param num_of_bytes:
        :param num_pre_write_bytes:
        :param dev_address:
        :type ftdi: FTDI
        """
        try:
            action_type = ActionTypeFPGA.NOTHING
            # if ftdi.object.status == 0:
            #    action_type = ActionTypeFPGA.OPEN
            # ftdi.open()
            self.write_to_fpga_memory(ftdi, '5001', reg_address, action_type=action_type)
            self.write_to_fpga_memory(ftdi, '5000', dev_address + str(num_pre_write_bytes) + str(num_of_bytes) + '02')
            time.sleep(0.005)
            self.read_from_fpga_memory(ftdi, '5000', 1)
            if self.Dword_From_FPGA[-1] == '8':
                raise Exception('Read failed from address: ' + dev_address)
            self.read_from_fpga_memory(ftdi, '5003', 1, action_type=ActionTypeFPGA.NOTHING)
            # ftdi.close()
            return "0x" + self.Dword_From_FPGA.replace("0x", "")[(-2 * num_of_bytes):]
        except Exception as e:
            raise FpgaException(str(e))

    def write_i2c_dev(self, ftdi, dev_address, reg_address, data, num_of_bytes, num_pre_write_bytes):
        """
        :param dev_address:
        :param data:
        :param num_of_bytes:
        :param num_pre_write_bytes:
        :param reg_address:
        :type ftdi: FTDI
        """
        try:
            action_type = ActionTypeFPGA.NOTHING
            # if ftdi.object.status == 0:
            #     action_type = ActionTypeFPGA.OPEN
            # ftdi.open()
            self.write_to_fpga_memory(ftdi, '5001', reg_address, action_type=action_type)
            self.write_to_fpga_memory(ftdi, '5002', data)
            self.write_to_fpga_memory(ftdi, '5000', dev_address + str(num_pre_write_bytes) + str(num_of_bytes) + '01')
            self.read_from_fpga_memory(ftdi, '5000', 1, action_type=ActionTypeFPGA.NOTHING)
            # ftdi.close()
            if self.Dword_From_FPGA[-1] == '8':
                raise Exception('Read failed from address: ' + dev_address + ', output: ' + self.Dword_From_FPGA)
        except Exception as e:
            raise FpgaException(str(e))

    def read_ad7998(self, ftdi, dev_address, port_number, a2d_vref):
        a2d_read = self.read_i2c_dev(ftdi, dev_address, hex(port_number + 7)[2:] + "0", 2, 1)
        return round((a2d_vref * int(a2d_read[-1] + a2d_read[-4:-2], 16)) / 4096, 2)

    def read_ad5272(self, ftdi, dev_address):
        """

        :param dev_address:
        :type ftdi: FTDI
        """
        # the AD5272 requier the I2C high byte to come first, not like we send it
        # enable to program the resistor.
        rdata = 0x0800  # program the RDAC fuse to current resistor value.
        rdata_s = swapbytehex(rdata)
        # print(rdata_s)
        rdata_s = str(swapbytehex(int(self.read_i2c_dev(ftdi, dev_address, rdata_s, 2, 2), 16)))
        # print(rdata_s)
        return rdata_s

    def write_ad5272(self, ftdi, dev_address, rdata, program_eeprom):
        """
        :param dev_address:
        :param rdata:
        :param program_eeprom:
        :type ftdi: FTDI
        """

        # the AD5272 require the I2C high byte to come first, not like we send it
        # enable to program the resistor.
        self.write_i2c_dev(ftdi, dev_address, "061c", "061c", 2, 2)
        rdac_calculated_data = rdata
        rdata = rdata | 0x400
        rdata_s = swapbytehex(rdata)
        self.write_i2c_dev(ftdi, dev_address, rdata_s, rdata_s, 2, 0)
        if program_eeprom:
            rdata = 0x0C00  # program the RDAC fuse to current resistor value.
            rdata_s = swapbytehex(rdata)
            self.write_i2c_dev(ftdi, dev_address, rdata_s, rdata_s, 2, 0)
            rdata = 0x2000  # control register read to make sure fuse write success.
            rdata_s = swapbytehex(rdata)
            rdata_s = str(swapbytehex(int(self.read_i2c_dev(ftdi, dev_address, rdata_s, 2, 2), 16)))
            if rdata_s == "000f":
                print("AD5272 program success to:" + str(rdac_calculated_data) + " Ohm")
            else:
                print("AD5272 program fail")

    def read_ads11112_a2d(self, ftdi, dev_address, config_mode, ref_voltage=2.048):
        """
        :type ftdi: FTDI
        """
        cycle_ctr = 0

        self.write_i2c_dev(ftdi, dev_address, "0", a2d_commnad[config_mode], 1, 0)
        time.sleep(0.15)

        lsb_val = 1
        a2d_val = ""

        while lsb_val != 0 and cycle_ctr < 4:
            a2d_val = self.read_i2c_dev(ftdi, dev_address, "0", 3, 0)
            lsb_val = int(a2d_val, 16) & 0x1
            cycle_ctr = cycle_ctr + 1

        ftdi.object.close()

        return round(ref_voltage * int((a2d_val[-2:] + a2d_val[-4:-2]), 16) / 32768, 3)

    def read_ina233a_a2d(self, ftdi, dev_address, max_current, rsense_mohm, type = "i"):
        """
        :type ftdi: FTDI
        """
        cur_lsb = max_current / pow(2, 15)

        hex_cal_value = hex(int(0.00512 / (cur_lsb * 0.001 * rsense_mohm))).replace("0x", "")

        self.write_i2c_dev(ftdi, dev_address, "D4", hex_cal_value, 2, 1)

        # v_out = 0.0
        # i_out = 0.0
        # a2d_val = self.read_i2c_dev(dev_address, "88", 2, 1)
        # v_out = round(int(a2d_val, 16) / 800.0, 3)
        if type == "i":
            a2d_val = self.read_i2c_dev(ftdi, dev_address, "8C", 2, 1)
            return round(get_pos_or_neg_value(int(a2d_val, 16)) * cur_lsb, 4)
        if type == "v":
            a2d_val = self.read_i2c_dev(ftdi, dev_address, "88", 2, 1)
            return round(get_pos_or_neg_value(int(a2d_val, 16)) / 800.0, 4)

        return 0.0

