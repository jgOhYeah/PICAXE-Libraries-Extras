# PICAXE Libraries and Extras
Extra code and libraries I have written for PICAXE microcontrollers or making life easier when dealing with them.

Feedback / Improvements are welcome.

## LoRa and PJON drivers for SX127* based LoRa modules
Some code and modules for interfacing a PICAXE microcontroller to an SX127* based radio module. This code allows sending and receiving of raw LoRa packets and or encoding and decoding them using a limited implementation of the PJON protocol.

Click [here](LoRa%20and%20PJON/README.md) for more info.

## EEPROMTools
A python script and PICAXE code to read and write to EEPROM chips and save and restore from binary files. These files can be edited using your favourite hex editor and downloaded from or uploaded to the EEPROM chip connected to a PICAXE microcontroller using the EEPROMTools.py script.

### Example usage
###### Reading
```
./EEPROMTools.py r test.bin # Reads bytes 0 to 2047 (defaults) into test.bin
```
###### Writing
```
./EEPROMTools.py w 255 test.bin # Writes the first 255 bytes of test.bin into the first 255 bytes of the eeprom chip.
```

## Python Preprocessor
Implementation of a very simple and limited preprocessor for the PICAXE compiler.

Click [here](PythonPreprocessor/README.md) for more info.
[This preprocessor](https://github.com/Patronics/PicaxePreprocess) is very similar and has more features implemented, so I recommend that you use that one if you can.

## Musescore Tune Converter
A small Musescore 3 plugin to convert simple tunes into code that can be used by the PICAXE tune command.

Click [here](MusescoreTuneConverter/README.md) for more info.
