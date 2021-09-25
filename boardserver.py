#!/usr/bin/python
import sys
import json
from driver.boardbase import *

output_message = {'ok': True}
if __name__ == '__main__':
    try:
        input_message = json.loads(sys.argv[1])
        command = input_message["command"]
        ftdi_name = input_message["FTDI Name"]
        board = BoardBase(ftdi_name)
        if command == "init":
            output_message["result"] = "Init success"
        elif command == "power_on":
            board.power_on()
            output_message["result"] = "Power On success"
        elif command == "power_off":
            board.power_off()
            output_message["result"] = "Power Off success"
        elif command == "set_ppm":
            ppm = input_message["ppm"]
            board.set_ppm(ppm)
            output_message["result"] = "Set PPM success"
        elif command == "set_ssc":
            ss_value = input_message["ss_value"]
            board.set_ssc(ss_value)
            output_message["result"] = "Set SSC success"
        elif command == "get_ssc":
            mode = input_message["mode"]
            if mode == "sw":
                ssc = board.get_ssc_sw()
            elif mode == "read":
                ssc = board.get_ssc_read()
            output_message["ssc"] = ssc
            output_message["result"] = "Get" + mode + " SSC success"
        elif command == "get_ppm":
            ppm = board.get_ppm()
            output_message["ppm"] = ppm
            output_message["result"] = "Get PPM success"
        elif command == "get_voltage":
            rail_name = input_message["rail_name"]
            rails_info = input_message["rails_info"]
            board.set_rails(rails_info)
            voltage = board.rails[rail_name].get_voltage()
            output_message['voltage'] = voltage
            output_message['result'] = "Get voltage success"
        elif command == "get_current":
            rail_name = input_message["rail_name"]
            rails_info = input_message["rails_info"]
            board.set_rails(rails_info)
            voltage = board.rails[rail_name].get_current()
            output_message['current'] = voltage
            output_message['result'] = "Get current success"
        elif command == "set_voltage":
            rail_name = input_message["rail_name"]
            rails_info = input_message["rails_info"]
            board.set_rails(rails_info)
            voltage = input_message["voltage"]
            board.rails[rail_name].set_voltage(voltage)
            output_message['result'] = "Set voltage success"
        else:
            raise Exception("Command not found")
        board.close_ftdi()
    except BaseRailError as e:
        output_message['ok'] = False
        output_message['error'] = e.message
    except BoardBaseError as e:
        output_message['ok'] = False
        output_message['error'] = e.message
    except Exception as e:
        output_message['ok'] = False
        output_message['error'] = e.message
    finally:
        print(json.dumps(output_message))

# while True:
#     outputMessage = {"ok": True}
#     inputMessage = input()
#     command = inputMessage["command"]
#
#     if command == "init":
#         try:
#             ftdi_name = inputMessage["FTDI Name"]
#             rails = inputMessage["Configuration File"]
#             board = BoardBase(ftdi_name)
#         except BoardBaseError as e:
#             outputMessage["error"] = e.message
#         print json.dumps(outputMessage)
#     elif command == "get_rails":
#         try:
#             if board is None:
#                 raise BoardBaseError("Board not connected, rails not found")
#             outputMessage["rails"] = board.rails.keys()
#             print json.dumps(outputMessage)
#         except BoardBaseError as e:
#             outputMessage["ok"] = False
#             outputMessage["error"] = e.message
#             print json.dumps(outputMessage)
#     elif command == "get_voltage":
#         try:
#             if board is None:
#                 raise BoardBaseError("Board not connected, rails not found")
#             rail_name = inputMessage["railName"]
#             outputMessage["result"] = str(board.rails[rail_name].get_voltage())
#             print json.dumps(outputMessage)
#         except Exception as e:
#             outputMessage["ok"] = False
#             outputMessage["error"] = e.message + command["railName"]
#             print json.dumps(outputMessage)
#     elif command == "set_voltage":
#         try:
#             if board is None:
#                 raise BoardBaseError("Board not connected, rails not found")
#             rail_name = inputMessage["railName"]
#             board.rails[rail_name].set_voltage(inputMessage["voltageValue"])
#             print json.dumps(outputMessage)
#         except Exception as e:
#             outputMessage["ok"] = False
#             outputMessage["error"] = e.message + command["railName"]
#             print json.dumps(outputMessage)
#     elif command == "exit":
#         print "exit"
#         break
#     else:
#         outputMessage["ok"] = False
#         outputMessage["error"] = "Wrong command"
#         print json.dumps(outputMessage)
