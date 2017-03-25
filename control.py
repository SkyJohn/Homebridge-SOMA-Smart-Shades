'''
The MIT License (MIT)
Copyright (c) 2016 Jeremy Noel
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''

import argparse
import subprocess
import thread
import time
import re

# meta
script_ver = 1.0
script_dec = "Interact with Smart Shades peripherals"

# cmd
cmd_get_battery = "get_battery"
cmd_get_position = "get_position"
cmd_move_up = "move_up"
cmd_move_down = "move_down"
cmd_move_target = "move_target"

# options
parser = argparse.ArgumentParser(description=script_dec, version=str(script_ver))
parser.add_argument("-t", "--target", dest="target", action="store", help="target peripheral MAC address",
                    required=True)
parser.add_argument("-c", "--command", dest="command", action="store",
                    choices=[cmd_get_battery, cmd_get_position, cmd_move_up, cmd_move_down, cmd_move_target],
                    help="command to execute on the peripheral", required=True)
parser.add_argument("-a", "--motor_target", dest="motor_target", action="store", type=int,
                    help="value in range 0 - 100, won't move if the distance is too short, set when command is " +
                         cmd_move_target, required=False)
parser.add_argument("-e", "--verbose", dest="verbose", action="store_true", default=False,
                    help="print script execution information", required=False)

args = parser.parse_args()
# verbose print
if args.verbose:
    def printv(string):
        print(string)
else:
    def printv(string):
        return

# battery
BATTERY_SERVICE_UUID = "0000180f-0000-1000-8000-00805f9b34fb".lower()
BATTERY_CHARACTERISTIC_UUID = "00002a19-0000-1000-8000-00805f9b34fb".lower()
# motor control
MOTOR_SERVICE_UUID = "00001861-B87F-490C-92CB-11BA5EA5167C".lower()
MOTOR_STATE_CHARACTERISTIC_UUID = "00001525-B87F-490C-92CB-11BA5EA5167C".lower()
MOTOR_CONTROL_CHARACTERISTIC_UUID = "00001530-B87F-490C-92CB-11BA5EA5167C".lower()
MOTOR_TARGET_CHARACTERISTIC_UUID = "00001526-B87F-490C-92CB-11BA5EA5167C".lower()
MOTOR_MOVE_UP = 69
MOTOR_MOVE_DOWN = 96


# peripheral control methods
def connect(stdin):
    printv("cmd = connect")
    stdin.write("connect\n")
    return


def disconnect(stdin):
    printv("cmd = disconnect")
    stdin.write("disconnect\n")
    return


def list_services(stdin):
    printv("cmd = primary")
    stdin.write("primary\n")
    return


def list_characteristics(stdin, service):
    printv("cmd = characteristics {0}".format(service))
    stdin.write("characteristics {0}\n".format(service))
    return


def write_characteristic(stdin, char, val):
    printv("cmd = char-write-req {0} {1}".format(char, val))
    stdin.write("char-write-req {0} {1}\n".format(char, val))
    return


def read_characteristic(stdin, char):
    printv("cmd = char-read-hnd {0}".format(char))
    stdin.write("char-read-hnd {0}\n".format(char))
    return


output_list = list()
service_dict = dict()
char_dict = dict()


def parse_output(stdout):  # read output on a background thread and store it
    while (True):
        try:
            output_list.append(stdout.readline())
        except Exception:
            continue
    return


def parse_connect():
    while True:
        if len(output_list) > 0:
            last_line = output_list[-1].lower()
            if "error" in last_line:
                print(last_line)
                return False
            elif "successful" in last_line:
                printv("out = connection successful")
                return True
        time.sleep(0.1)
    return


def parse_services():
    re_key = re.compile("(?<=(uuid\:\s))([^\s\,]+)")
    re_val = re.compile("(?<=(attr\shandle\:\s))([^\s\,]+)")
    while True:
        if len(output_list) > 0:
            last_line = output_list[-1].lower()
            if "error" in last_line:
                if args.verbose:
                    printv("out = " + last_line)
                else:
                    print(last_line)
                return False
            elif "attr handle" in last_line:
                time.sleep(1)  # wait a second for services to be fully printed
                for line in output_list[::-1]:
                    if "primary" in line.lower():
                        break
                    uuid_key = re_key.findall(line)
                    attr_val = re_val.findall(line)
                    if len(uuid_key) > 0 and len(attr_val) > 0:
                        service_dict.update({uuid_key[0][1]: attr_val[0][1]})
                printv("out = " + str(service_dict))
                return True
        time.sleep(0.1)
    return


def parse_chars():
    re_key = re.compile("(?<=(uuid\:\s))([^\s\,]+)")
    re_val = re.compile("(?<=(char\svalue\shandle\:\s))([^\s\,]+)")
    while True:
        if len(output_list) > 0:
            last_line = output_list[-1].lower()
            if "error" in last_line:
                if args.verbose:
                    printv("out = " + last_line)
                else:
                    print(last_line)
                return False
            elif "char value handle" in last_line:
                time.sleep(1)  # wait a second for characteristics to be fully printed
                for line in output_list[::-1]:
                    if "characteristics" in line.lower():
                        break
                    uuid_key = re_key.findall(line)
                    attr_val = re_val.findall(line)
                    if len(uuid_key) > 0 and len(attr_val) > 0:
                        char_dict.update({uuid_key[0][1]: attr_val[0][1]})
                printv("out = " + str(char_dict))
                return True
        time.sleep(0.1)
    return


def parse_read_write():
    re_val = re.compile("(?<=(value/descriptor\:\s))([^\s\,]+)")
    while True:
        if len(output_list) > 0:
            last_line = output_list[-1].lower()
            if "error" in last_line:
                print(last_line)
                return False
            elif "value/descriptor:" in last_line:
                out_val = re_val.findall(last_line)
                if args.verbose:
                    printv("out = " + str(int(out_val[0][1], 16)))
                else:
                    print(str(args.command) + " " + str(int(out_val[0][1], 16)))
                return True
            elif "written successfully" in last_line:
                printv("out = write successful")
                return True

        time.sleep(0.1)
    return


# restart bluetooth
pd = subprocess.Popen(["/bin/hciconfig", "hci0", "down"])
pd.wait()
pu = subprocess.Popen(["/bin/hciconfig", "hci0", "up"])
pu.wait()

# connect to peripheral and execute command
ps = subprocess.Popen(["/usr/bin/gatttool", "-b", args.target, "-t", "random", "-I"], stdout=subprocess.PIPE,
                      stdin=subprocess.PIPE)
t = thread.start_new_thread(parse_output, (ps.stdout,))
connect(ps.stdin)
if parse_connect():
    list_services(ps.stdin)
    if parse_services():
        if args.command == cmd_get_battery:
            list_characteristics(ps.stdin, service_dict[BATTERY_SERVICE_UUID])
        else:
            list_characteristics(ps.stdin, service_dict[MOTOR_SERVICE_UUID])
        if parse_chars():
            if args.command == cmd_get_battery:
                read_characteristic(ps.stdin, char_dict[BATTERY_CHARACTERISTIC_UUID])
            elif args.command == cmd_get_position:
                read_characteristic(ps.stdin,
                                    char_dict[MOTOR_STATE_CHARACTERISTIC_UUID])  # first byte in array is motor position
            elif args.command == cmd_move_down:
                write_characteristic(ps.stdin, char_dict[MOTOR_CONTROL_CHARACTERISTIC_UUID], MOTOR_MOVE_DOWN)
            elif args.command == cmd_move_up:
                write_characteristic(ps.stdin, char_dict[MOTOR_CONTROL_CHARACTERISTIC_UUID], MOTOR_MOVE_UP)
            elif args.command == cmd_move_target:
                write_characteristic(ps.stdin, char_dict[MOTOR_TARGET_CHARACTERISTIC_UUID],
                                     format(args.motor_target, "02x")) # convert input int to 2 digit hex string
            parse_read_write()
disconnect(ps.stdin)
ps.terminate()
