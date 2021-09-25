from __future__ import absolute_import

import time

from .powerexceptions import *
from driver.powerconfiguration.powerenums import *
from driver.base.fpga import FPGA


def flash_file_modify(byte_file_name, extension, trim_file):
    """
    :type byte_file_name: bytearray
    """
    if not trim_file:
        return byte_file_name

    if extension.upper() == "BIN":
        while byte_file_name and byte_file_name[-1] == 255:
            byte_file_name.pop(-1)

        while len(byte_file_name) % 4 != 0:
            byte_file_name.append(255)
    elif extension.upper() == "POF":
        while byte_file_name and byte_file_name[0] != 255 and byte_file_name[1] != 255:
            byte_file_name = byte_file_name[2:]

        while byte_file_name and byte_file_name[-1] != 255 and byte_file_name[-2] != 255:
            byte_file_name.pop()
            byte_file_name.pop()

        while byte_file_name and byte_file_name[-1] == 255:
            byte_file_name.pop(-1)

        while len(byte_file_name) % 4 != 0:
            byte_file_name.append(255)
        # with open("pre_swap.pof", "wb") as file_write:
        #     file_write.write(byte_file_name)
        temp_byte_arr = bytearray()
        bytes_conversion = ["0", "8", "4", "C", "2", "A", "6", "E", "1", "9", "5", "D", "3", "B", "7", "F"]

        # for i in range(0,len(byte_file_name)):
        while byte_file_name:
            orig_val = "%02X" % byte_file_name.pop(0)
            lsb = bytes_conversion[int(orig_val[1], 16)]
            msb = bytes_conversion[int(orig_val[0], 16)]
            temp_byte_arr.append(int(lsb + msb, 16))

        byte_file_name = temp_byte_arr

        # with open("modified.pof", "wb") as file_write:
        #     file_write.write(byte_file_name)
    return byte_file_name


class Flash:
    def __init__(self):
        self._FT_Out_Buffer_Size = 65536
        self.write_status = 0
        self.read_status = 0
        self._fpga = FPGA()

    def configure_flash(self, ftdi, byte_file_name, extension, trim_file, qpi_mode):
        """
         :type byte_file_name: bytearray
         :param extension:
         :param trim_file:
         :param qpi_mode:
         :param erase_opcode:
         :type ftdi: FTDI
         """

        if extension.upper() == "BIN" and not self.set_fpga_flash_mux(ftdi, "SPI", "FPGA", action_type=ActionTypeFPGA.OPENCLOSE):
            return False, None
        elif extension.upper() == "POF":
            erase_opcode = self.get_erase_opcode_epcs(ftdi)
            if not self.set_fpga_flash_mux(ftdi, "EPCS", "FPGA", action_type=ActionTypeFPGA.OPENCLOSE):
                return False, None
            self._fpga.write_to_fpga_memory(ftdi, "4015", erase_opcode, action_type=ActionTypeFPGA.OPENCLOSE)

        if qpi_mode:
            self._fpga.write_to_fpga_memory(ftdi, "4009", "1", action_type=ActionTypeFPGA.OPEN)
        else:
            self._fpga.write_to_fpga_memory(ftdi, "4009", "0", action_type=ActionTypeFPGA.OPEN)

        self._fpga.write_to_fpga_memory(ftdi, "4000", "5")
        self._fpga.read_from_fpga_memory(ftdi, "4006", 1, action_type=ActionTypeFPGA.CLOSE)

        if self._fpga.Dword_From_FPGA[-1] == 'F':
            self.set_fpga_flash_mux(ftdi, "SPI", "DUT", action_type=ActionTypeFPGA.OPENCLOSE)
            self.set_fpga_flash_mux(ftdi, "EPCS", "NONE", action_type=ActionTypeFPGA.OPENCLOSE)
            return False, None

        modified_byte_file_name = flash_file_modify(byte_file_name, extension, trim_file)

        self._fpga.write_to_fpga_memory(ftdi, "4001", "0", action_type=ActionTypeFPGA.OPEN)
        self._fpga.write_to_fpga_memory(ftdi, "4000", "2", action_type=ActionTypeFPGA.CLOSE)

        self.write_status = self._fpga.write_to_fpga_memory_burst(ftdi, "4002", modified_byte_file_name, 0, action_type=ActionTypeFPGA.OPENCLOSE)

        if not self.set_fpga_flash_mux(ftdi, "SPI", "DUT", action_type=ActionTypeFPGA.OPENCLOSE):
            return False, None
        if not self.set_fpga_flash_mux(ftdi, "EPCS", "NONE", action_type=ActionTypeFPGA.OPENCLOSE):
            return False, None

        if extension.upper() == "POF":
            byte_file_name = modified_byte_file_name

        return True, byte_file_name

    def verify_flash(self, ftdi, byte_file_name, extension):
        """
         :type byte_file_name: bytearray
         :param extension:
         :type ftdi: FTDI
         """

        num_of_bytes_to_read = len(byte_file_name)
        if extension.upper() == "BIN" and not self.set_fpga_flash_mux(ftdi, "SPI", "FPGA", action_type=ActionTypeFPGA.OPENCLOSE):
            return False
        elif extension.upper() == "POF" and not self.set_fpga_flash_mux(ftdi, "EPCS", "FPGA", action_type=ActionTypeFPGA.OPENCLOSE):
            return False

        self._fpga.write_to_fpga_memory(ftdi, "4000", "5", action_type=ActionTypeFPGA.OPEN)
        self._fpga.read_from_fpga_memory(ftdi, "4006", 1, action_type=ActionTypeFPGA.CLOSE)

        if self._fpga.Dword_From_FPGA[-1] == 'F':
            self.set_fpga_flash_mux(ftdi, "SPI", "DUT", action_type=ActionTypeFPGA.OPENCLOSE)
            self.set_fpga_flash_mux(ftdi, "EPCS", "NONE", action_type=ActionTypeFPGA.OPENCLOSE)
            return False

        array_offset = 0
        no_of_dwords_to_read = int((self._FT_Out_Buffer_Size - 4) / 4)

        while True:
            if array_offset >= num_of_bytes_to_read:
                break

            self.read_status = 100 * array_offset / num_of_bytes_to_read
            self._fpga.write_to_fpga_memory(ftdi, "4001", hex(array_offset).replace("0x", ""), action_type=ActionTypeFPGA.OPEN)
            self._fpga.write_to_fpga_memory(ftdi, "4000", "B")

            if (num_of_bytes_to_read - array_offset) < no_of_dwords_to_read:
                no_of_dwords_to_read = int((num_of_bytes_to_read - array_offset) / 4)

            read_res = self._fpga.read_from_fpga_memory(ftdi, "00004003", no_of_dwords_to_read, 0, 0, action_type=ActionTypeFPGA.CLOSE)
            read_byte_array = bytearray(read_res)
            if len(read_byte_array) - 2 != no_of_dwords_to_read * 4:
                return False

            for i in range(0, no_of_dwords_to_read, 4):
                if read_byte_array[i] != byte_file_name[array_offset + i + 3] or \
                        read_byte_array[i + 1] != byte_file_name[array_offset + i + 2] or \
                        read_byte_array[i + 2] != byte_file_name[array_offset + i + 1] or \
                        read_byte_array[i + 3] != byte_file_name[array_offset + i]:
                    self.set_fpga_flash_mux(ftdi, "SPI", "DUT", action_type=ActionTypeFPGA.OPENCLOSE)
                    self.set_fpga_flash_mux(ftdi, "EPCS", "NONE", action_type=ActionTypeFPGA.OPENCLOSE)
                    return False

            array_offset = array_offset + (self._FT_Out_Buffer_Size - 4)

            print("Verify flash status: " + str(self.read_status) + "% completed")
        if not self.set_fpga_flash_mux(ftdi, "SPI", "FPGA", action_type=ActionTypeFPGA.OPENCLOSE) and not self.set_fpga_flash_mux(ftdi, "EPCS", "FPGA", action_type=ActionTypeFPGA.OPENCLOSE):
            return False

        self.read_status = 100
        print("Verify flash status: " + str(self.read_status) + "% completed")

        return True

    def set_fpga_flash_mux(self, ftdi, spi_or_epcs, mux_channel, action_type=ActionTypeFPGA.NOTHING):
        try:
            address, value = "4010", "0"
            if spi_or_epcs == "SPI":
                if mux_channel == "DUT":
                    address, value = "4010", "1"
                elif mux_channel == "FPGA":
                    address, value = "4010", "2"
                elif mux_channel == "NONE":
                    address, value = "4010", "0"
            elif spi_or_epcs == "EPCS":
                if mux_channel == "NONE":
                    address, value = "4011", "0"
                elif mux_channel == "FPGA":
                    address, value = "4011", "1"
            self._fpga.write_to_fpga_memory(ftdi, address, value, action_type=action_type)
            return True
        except Exception as e:
            return False

    def erase_flash(self, ftdi, extension):
        """
         :type ftdi: FTDI
         """
        if extension.upper() == "BIN" and not self.set_fpga_flash_mux(ftdi, "SPI", "FPGA", action_type=ActionTypeFPGA.OPENCLOSE):
            return False
        elif extension.upper() == "POF" and not self.set_fpga_flash_mux(ftdi, "EPCS", "FPGA", action_type=ActionTypeFPGA.OPENCLOSE):
            return False

        self._fpga.write_to_fpga_memory(ftdi, "4000", "5", action_type=ActionTypeFPGA.OPEN)
        self._fpga.read_from_fpga_memory(ftdi, "4006", 1, 0, 0, action_type=ActionTypeFPGA.CLOSE)

        if self._fpga.Dword_From_FPGA[-1] == 'F':
            self.set_fpga_flash_mux(ftdi, "SPI", "FPGA", action_type=ActionTypeFPGA.OPENCLOSE)
            self.set_fpga_flash_mux(ftdi, "EPCS", "FPGA", action_type=ActionTypeFPGA.OPENCLOSE)
            return False

        self._fpga.write_to_fpga_memory(ftdi, "4005", "2", action_type=ActionTypeFPGA.OPEN)
        self._fpga.write_to_fpga_memory(ftdi, "4000", "1")

        if extension.upper() == "BIN":
            self._fpga.write_to_fpga_memory(ftdi, "4000", "60", action_type=ActionTypeFPGA.CLOSE)
        elif extension.upper() == "POF":
            self._fpga.write_to_fpga_memory(ftdi, "4000", "C7", action_type=ActionTypeFPGA.CLOSE)

        while True:
            self._fpga.write_to_fpga_memory(ftdi, "4000", "5", action_type=ActionTypeFPGA.OPEN)
            time.sleep(0.1)

            self._fpga.read_from_fpga_memory(ftdi, "4006", 1, 0, 1, action_type=ActionTypeFPGA.CLOSE)
            if self._fpga.Dword_From_FPGA[-2:] == '00':
                break

        if not self.set_fpga_flash_mux(ftdi, "SPI", "FPGA", action_type=ActionTypeFPGA.OPENCLOSE) and not self.set_fpga_flash_mux(ftdi, "EPCS", "FPGA", action_type=ActionTypeFPGA.OPENCLOSE):
            return False

        return True

    def get_flash_dev_id(self, ftdi, spi_or_epcs):
        if not self.set_fpga_flash_mux(ftdi, spi_or_epcs, "FPGA", action_type=ActionTypeFPGA.OPENCLOSE):
            raise Exception("Can't get flash device id")

        if spi_or_epcs.upper() == "SPI":
            id_opcode = "9F"
            mux_channel = "DUT"
        elif spi_or_epcs.upper() == "EPCS":
            id_opcode = "AB"
            mux_channel = "NONE"

        self._fpga.write_to_fpga_memory(ftdi, "4000", id_opcode, action_type=ActionTypeFPGA.OPEN)
        self._fpga.read_from_fpga_memory(ftdi, "4100", 1, action_type=ActionTypeFPGA.CLOSE)

        jedec_id = self._fpga.Dword_From_FPGA

        if not self.set_fpga_flash_mux(ftdi, spi_or_epcs, mux_channel, action_type=ActionTypeFPGA.OPENCLOSE):
            raise Exception("Can't get flash device id")

        return jedec_id

    def get_erase_opcode_epcs(self, ftdi):
        jedec_id = self.get_flash_dev_id(ftdi, "EPCS")

        erase_opcode = "80D80080"
        check_data = jedec_id[-2:]
        if check_data == "12" or check_data == "14" or check_data == "16":
            erase_opcode = "80D80100"

        return erase_opcode

    def identify_epcs(self, ftdi):
        jedec_id = self.get_flash_dev_id(ftdi, "EPCS")

        manufacture = "Altera"
        check_data = jedec_id[-2:]
        epcs_type = "NA"

        if check_data == "10":
            epcs_type = "EPCS1"
        elif check_data == "12":
            epcs_type = "EPCS4"
        elif check_data == "14":
            epcs_type = "EPCS16"
        elif check_data == "16":
            epcs_type = "EPCS64"

        return "EPCS Flash data for device " + epcs_type + " by "+ manufacture