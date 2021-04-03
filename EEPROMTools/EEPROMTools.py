#!/usr/bin/env python3
"""
Tools for backing up and restoring data to eeprom chips connected to a PICAXE
microcontroller.
Written by Jotham Gates
Created 03/04/2021
Modified 03/04/2021
"""
import serial
import sys
import time

ser = serial.Serial("/dev/ttyUSB0", 38400)
sleep_time = 0.2 # Time so the interpretor in the PICAXE can keep up.
acknowledge = b'\x01' # Char to receive
def print_help():
    print("""EEPROMTools.py MODE [[[START]] [END]] [FILENAME]

Where:
    MODE is read or write (r/w or read/write)
    START is the start address (optional, default 0)
    END is the inclusive end address (optional, default 1023)
    FILENAME is the file to read or write (optional, default EEPROM.bas)

Tool for uploading and downloading data from eeproms connected to picaxe
microcontrollers.

Serial Protocol:
    Read:
        'r' is sent, followed by 2 bytes for the start address and 2 bytes for
        the end address in little endian format. The microcontroller will send
        all bytes back.

    Write:
        'w' is sent, followed by the start address as 2 bytes in little endian
        format and the end address as 2 bytes.
        Then for each byte to write, send the byte and wait for a 1 to be sent
        back as acknowledgement before sending the next.
""")

def enter_computer_mode():
    """ Enters the mode on the microcontroller """
    print("Waiting for signature")
    ser.read_until(b"'`")
    print("Got signature")
    time.sleep(0.2)
    ser.write(b"'`'")
    ser.read_until(acknowledge)
    print("Acknowledged")

def read_memory(start: int, end: int) -> bytearray:
    """ Reads a given portion of eeprom memory and returns a list of byte objects """
    print("Sending read command")
    ser.write(b'r')
    time.sleep(sleep_time)
    ser.write(start.to_bytes(2,'little'))
    time.sleep(sleep_time)
    ser.write(end.to_bytes(2,'little'))
    length = end-start+1
    print("Sent params")
    result = bytearray()
    for _ in range(length):
        result += ser.read()
        print(".", end="", flush=True)

    print("\nFinished reading")
    return result # TODO: Checksum?

def write_memory(start: int, end:int, data: bytearray) -> None:
    """ Sends data to write to the microcontroller """
    print("Sending write command")
    ser.write(b'w')
    time.sleep(sleep_time)
    ser.write(start.to_bytes(2,'little'))
    time.sleep(sleep_time)
    ser.write(end.to_bytes(2,'little'))
    time.sleep(sleep_time)
    length = end-start+1
    print("Sent params")
    for i in range(length):
        ser.read()
        time.sleep(sleep_time)
        ser.write(data[i].to_bytes(1, 'little')) # Because 1 byte, endianness doesn't matter
        print(".", end="", flush=True)
    
    print("\nFinished writing")


def write_file(filename: str, data: bytearray) -> None:
    """ Writes a binary file than can then be edited with a hex editor """
    with open(filename, "wb") as file:
        file.write(data)

def read_file(filename: str) -> bytearray:
    """ Reads the data from a file into a bytearray """
    with open(filename, "rb") as file:
        return file.read()

def reset_micro() -> None:
    """ Sends the reset command """
    ser.write(b'q')

def query_mode() -> bool:
    """ Returns True if the microcontroller is correctly initialised """
    ser.write(b'?')

    # Set the serial timeout to be shorter and listen for the expected result
    cur_timeout = ser.timeout
    ser.timeout = 1
    data = ser.read_until(acknowledge)
    ser.timeout = cur_timeout
    # Test if we got some data back and it is what we expect
    if len(data) != 0 and data[-1].to_bytes(1, 'little') == acknowledge:
        return True
    else:
        return False

if __name__ == "__main__":
    do_operations = True

    # Default settings
    read = True
    start_addr = 0
    end_addr = 1023
    filename = "EEPROM.bin"

    if len(sys.argv) == 1:
        # No args given
        print_help()
        print("No arguments given.")
        do_operations = False
    else:
        # 1 or more args given (mode)
        # Get mode arg
        mode = sys.argv[1].lower()
        if mode == "r" or mode == "read":
            read = True
        elif mode == "w" or mode == "write":
            read = False
        else:
            print_help()
            do_operations = False

        # If 2 or more args:
        if len(sys.argv) > 2:
            # Filename arg
            filename = sys.argv[-1]

            if len(sys.argv) > 3:
                # End arg
                end_addr = int(sys.argv[-2])

                if len(sys.argv) > 4:
                    # Start arg
                    start_addr = int(sys.argv[-3])

    if do_operations:
        if not query_mode():
            print("Microcontroller is not in the correct mode.\nAttempting to enter it now.")
            enter_computer_mode()
        else:
            print("Microcontroller is in the correct more.")

        if read:
            print("Reading from {} to {} into {}".format(start_addr, end_addr, filename))

            data = read_memory(start_addr, end_addr)
            print("Writing file")
            write_file(filename, data)
        else:
            print("Writing {} into eeprom from {} to {}".format(filename, start_addr, end_addr))

            # Create a backup of the eeprom contents currently
            print("Making backup just in case")
            data = read_memory(start_addr, end_addr)
            print("Writing backup file")
            write_file("backup.bin", data)

            # Open and write the new file
            print("Writing file to eeprom")
            data = read_file(filename)
            write_memory(start_addr, end_addr, data)

        print("Done")