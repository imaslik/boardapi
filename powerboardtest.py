from driver.boardbase import *

if __name__ == '__main__':

    board = BoardBase('Pisgah NIC RevA1 070 B')
    board.set_ssc("OFF")
    # file_path = r"C:\Users\imaslik\Downloads\new_NVM_2021_02_28_17_03_33_e4dacc9_e71b7c4_x_x_GOLDEN.bin"
    # with open(file_path, "rb") as fileRead:
    #     image_bytes = bytearray(fileRead.read())
    #
    # file_name, file_extension = os.path.splitext(file_path)
    # count = 0
    # dict_status = {}
    # dict_status["True"] = 0
    # dict_status["False"] = 0
    # dict_status["Messages"] = []
    # while True:
    #     count += 1
    #     print ("Burning count " + str(count))
    #     status, message = board.burn_flash(image_bytes, file_extension[1:])
    #     dict_status[str(status)] += 1
    #     if not status:
    #         dict_status["Messages"].append(message)


    # board.rails["VCCSRAM_0V85"].get_voltage()
    for name in board.rails:
        try:
             print(name + ": " + str(board.rails[name].get_current()))
        except Exception as e:
             print(name + ": " + str(e))

        try:
             print(name + ": " + str(board.rails[name].get_voltage()))
        except Exception as e:
             print(name + ": " + str(e))

    print("Finish")
    #a = board.get_flash_dev_id("SPI")
    # b = board.get_flash_dev_id("EPCS")
    # c = board.identify_epcs()
    #
    #
    # board.set_ppm(-200)
    # board.get_ppm()
    # with open(r"C:\Users\imaslik\OneDrive - Intel Corporation\Desktop\Power\MEV_SVB_FPGA.pof", "rb") as fileRead:
    #     image_bytes = bytearray(fileRead.read())
    #
    #
    # board.burn_flash(image_bytes, "pof")
    # v = board.rails["VCCFA_P1V8"].get_voltage()
    # v = board.rails["VCCFA_P1V8"].set_voltage(1.83)
    # v = board.rails["VCCFA_P1V8"].get_voltage()
    #
    # # Read FPGA - address in hex without "0x" in the start
    # data = board.read_fpga("")
    #
    # # Write FPGA - address and data in hex without "0x" in the start
    # board.write_fpga("20", "1")
    # print("Finish")


