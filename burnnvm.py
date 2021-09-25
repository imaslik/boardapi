from driver.boardbase import *
import optparse
import os


def start_burn(**kwargs):
    file_path = None
    board_name = None

    if 'file_path' in kwargs:
        file_path = kwargs['file_path']
    if 'board_name' in kwargs:
        board_name = kwargs['board_name']

    if file_path is None:
        raise Exception("File path argument doesn't exist")
    if board_name is None:
        raise Exception("Board name argument doesn't exist")

    file_path = r"" + options.file_path + ""

    if not os.path.exists(file_path):
        raise Exception("File path doesn't exist")

    with open(file_path, "rb") as fileRead:
        image_bytes = bytearray(fileRead.read())

    print("Create " + board_name)
    # file_path = r"\\ladhfs\ev\Sys1\CVL\Regression_Lab\NVMs\CVL_2.2_Beta_can1\CVL_SD_M2p60_50G_FW_1p5p2p1_NCSI_1PORT_BACKPLANE_5.49_Revision\CVL_SD_M2p60_50G_FW_1p5p2p1_NCSI_1PORT_BACKPLANE_5.49_Revision_8000438E_NOPLDMH.bin"

    file_name, file_extension = os.path.splitext(file_path)
    board = BoardBase(board_name)
    status, message = board.burn_flash(image_bytes, file_extension[1:])

    if not status:
        raise Exception(message)

    print(message)


if __name__ == '__main__':
    try:
        parser = optparse.OptionParser()
        parser.add_option("-b", "--board", dest="board_name", type="str", help="FTDI Board name")
        parser.add_option("-f", "--file", dest="file_path", type="str", help="image file path .bin")

        (options, args) = parser.parse_args()

        start_burn(file_path=options.file_path, board_name=options.board_name)

    except Exception as e:
        print(str(e))
