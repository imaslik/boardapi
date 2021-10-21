#!/usr/bin/python3 -i

import argparse
import os
from inspect import getfullargspec
from driver.boardbase import *

board = BoardBase()
method_list = [func for func in dir(board) if callable(getattr(board, func))]

parser = argparse.ArgumentParser()
parser.add_argument('-m', '--method' , help="call methods", nargs="*")
args = parser.parse_args()

if args.method != None and args.method != "":
    if args.method[0] in method_list:
        arguments = args.method[1:]
        method = getattr(board, args.method[0])
        args_of_method = getfullargspec(method).args

        if len(arguments) > len(args_of_method)-1:
            print("wrong count of arguments in the method " + args.method[0])
            #os._exit(0)

        output = method(*tuple(arguments))
        
        if output is None:
            output = f"{args.method[0]} method executed"

        print(output)
        os._exit(0)
        
    else:
        print(args.method[0] + " doesn't exist")
        os._exit(1)

    
