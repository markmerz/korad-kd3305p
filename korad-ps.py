#!/usr/bin/python3

import sys
import glob
import serial
import pathlib

DEVICE_STRING = "KORAD KD3305P"
CH1_MODE_MASK =             0b00000001
CH1_MODE_CC =               0b00000000
CH1_MODE_CV =               0b00000001
CH2_MODE_MASK =             0b00000010
CH2_MODE_CC =               0b00000000
CH2_MODE_CV =               0b00000010
TRACKING_MODE_MASK =        0b00001100
TRACKING_MODE_INDEPENDENT = 0b00000000
TRACKING_MODE_SERIES =      0b00000100
TRACKING_MODE_PARALLEL =    0b00001000
CH1_OUTPUT_MASK =           0b01000000
CH1_OUTPUT_ON =             0b01000000
CH1_OUTPUT_OFF =            0b00000000
CH2_OUTPUT_MASK =           0b10000000
CH2_OUTPUT_ON =             0b10000000
CH2_OUTPUT_OFF =            0b00000000

def main():
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
    try:
        fhandle = detect_fhandle()
        c = 1
        while c < len(sys.argv):
            if sys.argv[c].upper().startswith("Q"):
                c += 1
                command = sys.argv[c]
                if command.upper() == "STATUS?":
                    print(decode_status(korad_query_raw(fhandle, command)))
                else:
                    print(korad_query(fhandle, command))
            elif sys.argv[c].upper().startswith("C"):
                c += 1
                command = sys.argv[c]
                korad_command(fhandle, command)
            elif sys.argv[c].upper().startswith("S"):
                c += 2
                command = sys.argv[c-1]
                value = sys.argv[c]
                korad_set(fhandle, command, value)
            else:
                print_usage()
                sys.exit(2)        
            c += 1
    except ValueError as ex:
        print(ex, file=sys.stderr)
        sys.exit(1)

def print_usage():
    usage = f"Usage: {sys.argv[0]} query vset1?\n" +\
    f"Usage: {sys.argv[0]} q vset1? q iset1? \n" +\
    f"Usage: {sys.argv[0]} set vastep1 25,15,0.5,1 \n" +\
    f"Usage: {sys.argv[0]} command lock1 \n"

    print(usage, end='', file=sys.stderr)

def decode_status(input: bytes) -> str:
    statusi = int.from_bytes(input[0:1])
    
    ret = "Tracking mode: "
    tracking = statusi & TRACKING_MODE_MASK
    if tracking == TRACKING_MODE_INDEPENDENT:
        ret = ret + "independent\n"
    elif tracking == TRACKING_MODE_SERIES:
        ret = ret + "in series\n"
    elif tracking == TRACKING_MODE_PARALLEL:
        ret = ret + "in parallel\n"

    ret = ret + "Channel 1: "
    output = statusi & CH1_OUTPUT_MASK
    if output == CH1_OUTPUT_OFF:
        ret = ret + "Output: OFF\n"
    elif output == CH1_OUTPUT_ON:
        ret = ret + "Output: ON\n"

    ret = ret + "Channel 1: "
    channel_mode = statusi & CH1_MODE_MASK
    if channel_mode == CH1_MODE_CV:
        ret = ret + "Mode: Constant Voltage\n"
    elif channel_mode == CH1_MODE_CC:
        ret = ret + "Mode: Constant Current\n"

    ret = ret + "Channel 2: "
    output = statusi & CH2_OUTPUT_MASK
    if output == CH2_OUTPUT_OFF:
        ret = ret + "Output: OFF\n"
    elif output == CH2_OUTPUT_ON:
        ret = ret + "Output: ON\n"

    ret = ret + "Channel 2: "
    channel_mode = statusi & CH2_MODE_MASK
    if channel_mode == CH2_MODE_CV:
        ret = ret + "Mode: Constant Voltage"
    elif channel_mode == CH2_MODE_CC:
        ret = ret + "Mode: Constant Current"

    return ret

def korad_query(fhandle: str, query: str) -> str:
    with serial.Serial(fhandle, 9600, timeout=0.5) as ser:
        ser.write((query.upper() + "\n").encode("utf-8"))
        ret = ser.readline().decode("utf-8").strip()
    if len(ret) > 0:
        return ret
    else:
        raise ValueError(f"{query} - no reply from device {fhandle}. Unknown query?")
    
def korad_query_raw(fhandle: str, query: str) -> bytes:
    with serial.Serial(fhandle, 9600, timeout=0.5) as ser:
        ser.write((query.upper() + "\n").encode("utf-8"))
        ret = ser.readline()
    if len(ret) > 0:
        return ret
    else:
        raise ValueError(f"{query} - no reply from device {fhandle}. Unknown raw query?")
    
def korad_command(fhandle: str, command: str):
    with serial.Serial(fhandle, 9600, timeout=0.5) as ser:
        commandbytes = (command.upper() + "\n").encode("utf-8")
        outlen = ser.write(commandbytes)
    if outlen != len(commandbytes):
        raise ValueError(f"{command} - no reply from device {fhandle}. Unknown command?")
    
def korad_set(fhandle: str, command: str, value: str):
    with serial.Serial(fhandle, 9600, timeout=0.5) as ser:
        commandbytes = (command.upper() + ":" + value + "\n").encode("utf-8")
        outlen = ser.write(commandbytes)
    if outlen != len(commandbytes):
        raise ValueError(f"{command} - no reply from device {fhandle}. Unknown set command?")

def detect_fhandle() -> str:
    candidates = []
    saved_candidate = None
    try:
        with open(pathlib.Path.home() / ".korad-power-supply") as kfd:
            saved_candidate = kfd.read()
            candidates.append(saved_candidate)
    except FileNotFoundError as ex:
        pass
    
    candidates.extend(glob.glob("/dev/ttyACM*"))

    for candidate in candidates:
            try:
                with serial.Serial(candidate, 9600, timeout=0.5) as ser:
                    ser.write("*IDN?\n".encode("utf-8"))
                    ret = ser.readline().decode("utf-8")
                    if ret.startswith(DEVICE_STRING):
                        if candidate != saved_candidate:
                            with open(pathlib.Path.home() / ".korad-power-supply", "w") as kfd:
                                kfd.write(candidate)
                        return candidate
            except serial.serialutil.SerialException as ex:
                pass
    else:
        raise ValueError("Device handle was not found.")

if __name__ == "__main__":
    main()
