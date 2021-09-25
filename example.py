# imorting driver of ftdi and board
from driver.boardbase import *

if __name__ == '__main__':
    # create instance of class BoardBase where there are all relevant functions, like R/W Fpga, R/W I2C, Get/Set Rail Voltage /...
    # parameters: name of the board. If board name is unknown, there is option to get the name by getting information
    # from ftdi devices after importing driver.boardbase:
    #   ftdi_devices.devices_info ->
    #       [{'index': 0, 'flags': 2L, 'location': 74513L, 'handle': c_void_p(None), 'serial': '995A5FFAA', 'type': 6L,
    #       'id': 67330064L, 'description': 'Pisgah MEV NIC FABY-1 001 A'}, {'index': 1, 'flags': 2L, 'location': 74514L,
    #       'handle': c_void_p(None), 'serial': '995A5FFAB', 'type': 6L, 'id': 67330064L,
    #       'description': 'Pisgah MEV NIC FABY-1 001 B'}]
    # need to take description value with last char 'B'
    board = BoardBase('Pisgah MEV NIC FABY-1 001 B')

    # list of board functions:

    # get info of connected ftdi device
    board.get_board_info()  # {'status': 0, 'handle': c_void_p(20110128L), 'description': 'Pisgah MEV NIC FABY-1 001 B', 'serial': '995A5FFAB', 'type': 6L, 'id': 67330064L}

    # read data from registers via FPGA - parameter value is hex number in string format without "0x" in the start
    board.read_fpga("20")  # '0x00000000' - output is 4 bytes in hex

    # write data to fpga register
    # parameters:
    #   1. reg address
    #   2. data - in hex without "0x" in the start
    board.write_fpga("101", "1")

    # read data from registers via I2C
    # parameters:
    #   1. device address
    #   2. reg address
    #   3. number of bytes to read
    #   4. number of device address bytes
    board.read_i2c("60", "0", 2, 1)  # '0x00000000' - output is 4 bytes in hex

    # write data to registers via I2C
    # parameters:
    #   1. device address
    #   2. reg address
    #   3. data
    #   4. number of bytes to write
    #   5. number of device address bytes
    board.write_i2c("60", "0", "1", 2, 1)

    # get list of rails:
    board.rails.keys()  # ['VNNSRAM_0V75', 'VDDQ_1V1', 'VCCFA_P1V8', 'V1P15', 'VDDQLP_0V6', 'VNN_0V74', 'VCC_1V04', 'VCC3V3', 'VCCSRAM_0V85']

    # get voltage of rail
    board.rails["VDDQLP_0V6"].get_voltage()  # output double value

    try:
        board.rails["VCCSRAM_0V85"].get_voltage()
    except Exception as ex:
        print(str(ex))  # output - Read failed from address: 41, output: 0x00411208


    # set voltage of rail
    board.rails["VNNSRAM_0V75"].set_voltage(0.76)
