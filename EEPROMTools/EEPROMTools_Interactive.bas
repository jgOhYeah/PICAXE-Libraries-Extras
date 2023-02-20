; EEPROMTools_Interactive.bas
; Set of tools for reading and writing to eeprom. This version runs only on the
; microcontroller - nothing other than a serial terminal is required on the
; computer. This may be easier to use, but doesn't allow binary files to be
; read and written.
;
; Jotham Gates
; Created 06/01/2020
; Modified 20/02/2023

#PICAXE 18m2
symbol param1 = w0
symbol param1l = b0
symbol param1h = b1
symbol tmpbt0 = b2
symbol tmpwd0 = w2
symbol tmpwd0l = b4
symbol tmpwd0h = b5
symbol tmpwd1 = w3
symbol tmpwd1l = b6
symbol tmpwd1h = b7
symbol tmpwd2 = w4
symbol tmpwd2l = b8
symbol tmpwd2h = b9
symbol tmpwd3 = w5
#MACRO EEPROM_SETUP(ADDR, TMPVAR)
	; I2C address
	TMPVAR = ADDR / 128 & %00001110
	TMPVAR = TMPVAR | %10100000
    ; sertxd(" (", #ADDR, ", ", #TMPVAR, ")")
	hi2csetup i2cmaster, TMPVAR, i2cfast_32, i2cbyte
#ENDMACRO

init:
    setfreq m32
    gosub print_help

main:
    serrxd tmpbt0
    select case tmpbt0
        case "a"
            sertxd(cr, lf, "Printing all memory locations", cr, lf)
            for tmpwd3 = 0 to 2047 step 8
                param1 = tmpwd3
                gosub print_block
            next tmpwd3
            sertxd("Done",cr, lf)
		case "b"
			sertxd(cr, lf, "Printing first block", cr, lf)
            for tmpwd3 = 0 to 255 step 8
                param1 = tmpwd3
                gosub print_block
            next tmpwd3
            sertxd("Done",cr, lf)
        case "w"
            sertxd("Enter address to write (dec): ")
            serrxd #tmpwd0
            EEPROM_SETUP(tmpwd0, tmpbt0)
            sertxd(#tmpwd0, cr, lf, "Enter value (dec): ")
            serrxd #tmpbt0
            hi2cout tmpwd0l, (tmpbt0)
            sertxd(#tmpbt0, cr, lf, "Done",cr, lf)
        case "e"
            sertxd("Resetting everything to 255", cr, lf)
            param1 = 0
            gosub erase
            sertxd("Done",cr, lf)
        case "f"
            sertxd("Enter first address to erase (dec): ")
            serrxd #param1
            sertxd(#param1, cr, lf)
            gosub erase
            sertxd("Done",cr, lf)
        case "p"
            sertxd("Entering programming mode. Anything sent will cause a reset.", cr, lf)
            reconnect
            stop
		case "q"
			sertxd("Resetting",cr, lf)
			reset
        case "h"
            gosub print_help
        case " ", cr, lf
            ; Ignore
        else
            sertxd(cr, lf, "Command not regonised. Please try again.", cr, lf)
    end select
    goto main

erase:
    for tmpwd1 = param1 to 2047
        EEPROM_SETUP(tmpwd1, tmpbt0)
        hi2cout tmpwd1l, (0xFF)
        pause 20
    next tmpwd1
    return

print_help:
    sertxd(cr, lf, "EEPROM Tools", cr, lf)
    sertxd("All values are in HEX.", cr, lf)
    sertxd("Commands:", cr, lf)
    sertxd("    a   Read all", cr, lf)
	sertxd("    b   Read first block", cr, lf)
    sertxd("    w   Write at address", cr, lf)
    sertxd("    e   Erase all", cr, lf)
    sertxd("    f   Erase after", cr, lf)
    sertxd("    p   Enter programming mode", cr, lf)
	sertxd("    q   Reset", cr, lf)
    sertxd("    h   Show this help", cr, lf)
    sertxd("Waiting for input: ")
    return
    

print_block:
    ; Read the 8 bytes and display them as hex
    ;
    ; Variables modified: tmpwd0, param1, tmpwd1, tmpwd2, 
    tmpwd0 = param1
    param1 = param1h
    gosub print_byte
    param1 = tmpwd0l
    gosub print_byte
    param1 = tmpwd0
    sertxd(": ")
    tmpwd0 = param1 + 7
    tmpwd1 = param1
    for tmpwd2 = tmpwd1 to tmpwd0
        EEPROM_SETUP(tmpwd2, param1)
        hi2cin tmpwd2l, (param1)
        gosub print_byte
        sertxd(" ")
    next tmpwd2
    sertxd(cr, lf)
    return

print_byte:
    ; Prints a byte formatted as hex stored in param1
    ;
    ; Variables modified: tmpbt0
    tmpbt0 = param1l
    param1 = param1l / 0x10
    gosub print_digit
    param1 = tmpbt0 & 0x0F
    gosub print_digit
    param1 = tmpbt0 ; Reset param1 back to what it was
    return

print_digit:
    ; Prints a 4 bit hex digit stored in param1
    ;
    ; Variables modified: param1
    ; sertxd("(",#param1,")")
    if param1 < 0x0A then
        param1 = param1 + 0x30
    else
        param1 = param1 + 0x37
    endif
    sertxd(param1)
    return