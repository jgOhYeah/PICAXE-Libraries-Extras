# Python Preprocessor
Implementation of a very simple and limited preprocessor for the PICAXE compiler.
This script is aimed as a workaround for enabling #include on platforms other than Windows as this
is handled by the preprocessor that is built into the Windows only programming editor 6, which is
not included with the command line compilers.
This script merges all files into one and calls the correct compiler to process or upload the code.
The compilers can be downloaded from the PICAXE website software section if needed, found at:
https://www.picaxe.co.uk.

If you need macros and defines, you might be interested in [this similar preprocessor](https://github.com/Patronics/PicaxePreprocess), also written in python.

## Usage
```
picaxe.py [OPTION]... FILE.bas
```

### Optional switches (similar to those in the PICAXE compilers)

| Switch       | Description                                                                                                                                             |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `-v`         | Variant (default `08m2`) <br>(alternatively use `#PICAXE` directive within the program. This option will be ignored if `#PICAXE` is used)               |
| `-s`         | Syntax check only (no download)                                                                                                                         |
| `-f`         | Firmware check only (no download)                                                                                                                       |
| `-cPortName` | Assign COM/USB port device (default `/dev/ttyUSB0`) <br>(alternately use `#COM` directive within program This option will be ignored if `#COM` is used) |
| `-d`         | Leave port open for debug display (`b0`-`13`)                                                                                                           |
| `-dh`        | Leave port open for debug display (hex mode)                                                                                                            |
| `-e`         | Leave port open for debug display (`b14`-`b27`)                                                                                                         |
| `-eh`        | Leave port open for debug display (hex mode)                                                                                                            |
| `-t`         | Leave port open for sertxd display                                                                                                                      |
| `-th`        | Leave port open for sertxd display (hex mode)                                                                                                           |
| `-ti`        | Leave port open for sertxd display (int mode)                                                                                                           |
| `-p`         | Add pass message to error report file                                                                                                                   |
| `-h`         | Display this help text                                                                                                                                  |

### Examples
#### 14M2 chip on COM1 with AXE026 serial cable
```
picaxe.py -v14m2 -c/dev/ttyS0 test.bas
```

#### 18M2 chip on USB with AXE027 USB cable
```
picaxe.py -v18m2 -c/dev/ttyUSB0 test.bas
```

#### A syntax check without download and the chip and port are specified using #PICAXE and #COM respectively in the file:
```
picaxe.py -s test.bas
```

## Testing files
Run the compiler on `HelloWorld.bas` and all other files linked to by it should be merged and compiled.
