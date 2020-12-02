#!/usr/bin/python3
""" Implementation of a very simple and limited preprocessor for the PICAXE compiler.
This script is aimed as a workaround for enabling #include on platforms other than Windows as this
is handled by the preprocessor that is built into the Windows only programming editor 6, which is
not included with the command line compilers.
This script merges all files into one and calls the correct compiler to process or upload the code.
The compilers can be downloaded from the PICAXE website software section if needed, found at:
www.picaxe.co.uk.

Script written by Jotham Gates, last edited 02/12/2020. I have had nothing to do with the
compilers except using them to program PICAXE chips. Also, please be aware that I wrote this in my
spare time to suit my own picaxe scripts, so there may be the odd bug.

Macros, #if and #defines are not supported or manipluated in any way yet.

See https://picaxeforum.co.uk/threads/macros-with-axepad.29809/ for a further description of the
issue. See the help text (run picaxe.py -h) for more usage info.

Install location.
For better or worse, I copied the script and compilers as follows so that I can access them without
needing to remember file paths. Instead, I can just type in "picaxe.py" to run it. Edit
compiler_path on line 43 to suit your needs. There may be a better or more appropriate place to
locate these files.

picaxe.py: /usr/local/bin/picaxe.py
compilers: /usr/local/lib/picaxe/picaxe* (where * is 08, 08m, 08m2, ...)
"""
import os
import sys
import subprocess
version = "1.0" # Version of this script

# DEFAULTS AND SETTINGS
# Default settings (May be overridden with the command line arguments)
use_colour = True # Does not work on Windows, will end up with a lot of nonsense characters when
                  # showing an error.
chip = "08m2" # Must be lowercase m or x if included
port = "-c/dev/ttyUSB0" # Must have "-c" with no space before like using the compiler as normal.
src_file = ""
dst_file = "picaxe_tmp_compiled.bas" # File to combine everything into before sending to the compiler

# Compiler path
compiler_path = "/usr/local/lib/picaxe/" # Needs a / afterwards
compiler_name = "picaxe"
compiler_extension = "" # File extension. For linux anyway, there is none, but including just in
                        # case it is different for other platforms.
def show_help():
    """ Shows the help and usage window """
    print("""Simple preprocessor for PICAXE compilers.
This script combines all files linked to the given one into a single file, then
starts the correct PICAXE compiler.
Currently, #MACRO, #DEFINE, #IF and #ELSEIF are not processed by this
preprocessor, so they may be missing or missing features as they are left to the
compiler.

USAGE: picaxe.py [OPTION]... FILE.bas

Optional switches (similar to those in the PICAXE compilers)
    -v          Variant (default 08m2)
                (alternatively use #PICAXE directive within the program. This
                option will be ignored if #PICAXE is used)
    -s          Syntax check only (no download)
    -f          Firmware check only (no download)
    -cPortName  Assign COM/USB port device (default /dev/ttyUSB0)
                (alternately use #COM directive within program. This option will
                be ignored if #COM is used)
    -d          Leave port open for debug display (b0-13)
    -dh         Leave port open for debug display (hex mode)
    -e          Leave port open for debug display (b14-b27)
    -eh         Leave port open for debug display (hex mode)
    -t          Leave port open for sertxd display
    -th         Leave port open for sertxd display (hex mode)
    -ti         Leave port open for sertxd display (int mode)
    -p          Add pass message to error report file
    -h          Display this help

Examples:
    14M2 chip on COM1 with AXE026 serial cable
        picaxe.py -v14m2 -c/dev/ttyS0 test.bas
    18M2 chip on USB with AXE027 USB cable
        picaxe.py -v18m2 -c/dev/ttyUSB0 test.bas
    A chip syntax check without download and the chip and port are specified
    using #PICAXE and #COM respectively in the file:
        picaxe.py -s test.bas

This is version {}.
""".format(version))

    exit()

def preprocessor_error(msg):
    """ Prints an error message that may be coloured if there is an issue preprocessing.
    Will also stop the script executing. """
    # Header
    if use_colour:
        print("\u001b[1m\u001b[31m", end="") # Bold Red
    print("PREPROCESSOR ERROR")
    if use_colour:
        print("\u001b[0m", end="") # Reset
    
    # Body
    print(msg)

    # Note to say giving up
    if use_colour:
        print("\u001b[33m", end="") # Yellow
    print("Processing halted. Please try again.")
    if use_colour:
        print("\u001b[0m", end="") # Reset

    output.close() # In case output was still open
    exit()
    
def preprocessor_warning(msg):
    """ Prints a warning message. Similar to error, but will not stop. """
    if use_colour:
        print("\u001b[1m\u001b[33m", end="") # Bold Yellow
    print("PREPROCESSOR WARNING")
    if use_colour:
        print("\u001b[0m", end="") # Reset
    print(msg)

def set_chip(new_chip):
    """ Validates and selects the compiler to use.
    This needs to be validated as it will be used to run a command line program, so do not want to
    inject malicious code (although should they already have access to the command line directly if
    they are running this script??? """
    global chip
    valid_chips = ["08", "08m2", "08m2le", "14m", "14m2", "18", "18a", "18m", "18m2", "18x",
                   "18x_1", "20m", "20m2", "20x2", "28", "28a", "28x", "28x_1", "28x1", "28x1_0",
                   "28x2"]
    new_chip = new_chip.lower() # In case of 08M2 or 08m2
    if new_chip in valid_chips:
        print("Setting the PICAXE chip to: '{}'".format(new_chip))
        chip = new_chip
    else:
        preprocessor_error("""'{}' given as a PICAXE chip, but is not in the list of known parts or compilers.
Please select from:\n{}""".format(new_chip,valid_chips))

def combine(filename):
    """ Recursively combines PICAXE BASIC files into one """
    global port
    # For each line in file, strip out ^M (\r).
    # If #include (convert to lower or uppercase) in line, then recursively call combine.
    try:
        file = open(filename)
    except FileNotFoundError:
        preprocessor_error("Could not include '{}'".format(filename))
    except IsADirectoryError:
        preprocessor_error("'{}' is a directory. Only files can be included.".format(filename))

    text = file.read()
    # text = text.replace("'",";") # Make all comments be in the same format for consistency.
    contents = text.split("\n")
    file.close()
    for line in contents:
        filtered = line.replace("\r", "") # The linux compiler at least crashes with carraige
        # returns but the Windows programming editor 6 adds them in, so need to remove.
        
        # Remove all whitespace at the start or end to make command identification easier. A
        # commented out character will not be removed, so hence will not match anything checked for
        # below.
        command = filtered.strip()

        # Process the line for any preprocessor directives
        if len(command) >= 8 and command[:8].lower() == "#include":
            # This is a #include line.
            print("#include found: {}".format(command))
            output.write("; {}\n; *** INSERTED BELOW ***\n".format(command)) # Add the include line commented out
            broken_down = command.split('"') # The file name should be the 2nd in the list
            if(len(broken_down) < 3 or '"' not in command):
                # There is not enough elements in the array for the include to be valid.
                preprocessor_error("""Invalid #include statement: '{}'.
Either there is no given file to include or it is not enclosed in quotation (\") marks.""".format(command))
            combine(broken_down[1])
            output.write("; *** END OF INSERT ***\n\n")

        # Check if the line is a directive to set the PICAXE chip
        elif len(command) >= 7 and command[:7].lower() == "#picaxe":
            broken_down = command.split(' ') # The PICAXE chip should be the 2nd in the list
            if(len(broken_down) < 2):
                preprocessor_error("""Invalid call to set the PICAXE type: '{}'
The name of the chip is not included""".format(command))
            set_chip(broken_down[1])
            output.write("; {}\n".format(command))

        # Check if the line is a directive to set the serial port.
        # Probably not necessary as I think the compiler also checks and handles this.
        elif len(command) >= 4 and command[:4].lower() == "#com":
            broken_down = command.split(' ') # The PICAXE chip should be the 2nd in the list
            if(len(broken_down) < 2):
                preprocessor_error("""Invalid call to set the PICAXE serial port: '{}'
The name of the port is not included""".format(command))
            print("Setting the serial port to: {}".format(broken_down[1]))
            port = "-c{}".format(broken_down[1])

        else:
            output.write(filtered)
            output.write("\n")

# Command line options
if len(sys.argv) == 1:
    # No arguments given
    show_help()

# For each argument given, store it to pass it on or interpret it.
command = [""] # Empty string at the first position will be replaced by the compiler name and path.
for i in range(1, len(sys.argv)):
    arg = sys.argv[i]
    if arg[:2] == "-c":
        # Serial port
        port = arg
    
    elif arg[:2] == "-v":
        # PICAXE variant
        set_chip(arg[2:])
    
    elif arg == "-h" or arg == "?" or arg == "--help":
        # Help / usage screen
        show_help()

    elif arg[0] == "-":
        # -d, -t, -s or anything else not used by the preprocessor that needs to be passed on
        command.append(arg)

    elif i == len(sys.argv) - 1:
        # Does not start with a dash and is the last argument, so assume it is a filename
        src_file = arg

    else:
        # Who knows what
        show_help()


# Changing directory
# Getting path code from https://stackoverflow.com/a/17057603
working_dir, src_file_new = os.path.split(os.path.abspath(src_file))
os.chdir(working_dir)
output = open(dst_file,"w") # Array of lines of the finished program.

# Combining and processing
combine(src_file_new)

# Finishing up
output.close()
print("Preprocessor done. Passing over to the compiler")
# Calling the correct compiler
command[0] = "{}{}{}{}".format(compiler_path, compiler_name, chip, compiler_extension)
command.append(port)
command.append(dst_file)
subprocess.run(command)

print("Finished.")