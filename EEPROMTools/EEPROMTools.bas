; EEPROMTools.bas
; A program to manage an I2C EEPROM chip connected to a PICAXE microcontroller.
; Designed to interface with the EEPROMTools.py script that can save and load
; binary files. This allows disk images of sorts to be taken, edited using a hex
; editor of your choice and uploaded.
;
; Designed for a XL24C16P 16kbit eeprom chip connected vie hardware I2C.
;
; Jotham Gates
; Created 03/04/2021
; Modified 03/04/2021

#PICAXE 18M2 ; Just so the command line compiler behaves. This an be changed
#NO_DATA

; For an 18M2
#DEFINE PIN_LED_ALARM B.3
#DEFINE PIN_LED_ON B.6
#DEFINE PIN_I2C_SDA B.1
#DEFINE PIN_I2C_SCL B.4

symbol tmpwd0 = w3
symbol tmpwd0l = b6
symbol tmpwd0h = b7
symbol tmpwd1 = w4
symbol tmpwd1l = b8
symbol tmpwd1h = b9
symbol tmpwd2 = w5
symbol tmpwd2l = b10
symbol tmpwd2h = b11
symbol tmpwd3 = w6
symbol tmpwd3l = b12
symbol tmpwd3h = b13
symbol tmpwd4 = w7
symbol tmpwd4l = b14
symbol tmpwd4h = b15

; The EEPROM chip I am using uses its address to select banks, so this has to be set as well.
#MACRO EEPROM_SETUP(ADDR, TMPVAR)
	; ADDR is a word
	; TMPVAR is a byte
	; I2C address
	TMPVAR = ADDR / 128 & %00001110
	TMPVAR = TMPVAR | %10100000
    ; sertxd(" (", #ADDR, ", ", #TMPVAR, ")")
	hi2csetup i2cmaster, TMPVAR, i2cslow_32, i2cbyte ; Reduce clock speeds when running at 3.3v
#ENDMACRO

init:
    setfreq m32 ; Because other projects run at that frequency. 38400 serial baud

computer_mode:
    ; Initialise
    sertxd(1)
    low PIN_LED_ON ; LEDS to flash (from another project)
    high PIN_LED_ALARM

computer_mode_loop:
    serrxd tmpwd0l
    select case tmpwd0l
        case "r" ; Read bytes
            low PIN_LED_ALARM
            serrxd tmpwd1l, tmpwd1h, tmpwd2l, tmpwd2h ; Start and end address (inclusive) in little endian
            ; Upload everything
            high PIN_LED_ALARM
            high PIN_LED_ON
            for tmpwd0 = tmpwd1 to tmpwd2
                EEPROM_SETUP(tmpwd0, tmpwd3l)
                hi2cin tmpwd0l, (tmpwd3l)
                sertxd(tmpwd3l)
            next tmpwd0
            low PIN_LED_ON
        case "w" ; Write bytes
            low PIN_LED_ALARM
            serrxd tmpwd1l, tmpwd1h, tmpwd2l, tmpwd2h ; Start and end address (inclusive) in little endian
            ; Read everything
            high PIN_LED_ALARM
            high PIN_LED_ON
            for tmpwd0 = tmpwd1 to tmpwd2
                sertxd(1) ; Acknowledge
                EEPROM_SETUP(tmpwd0, tmpwd3l)
                serrxd tmpwd3l
                hi2cout tmpwd0l, (tmpwd3l)
                toggle PIN_LED_ON
                pause 80
            next tmpwd0
            low PIN_LED_ON
            ; Done
        case "q" ; Reset
            reset
        case "p" ; Programming mode
            reconnect
            stop
        case "?" ; Query if this program is running correctly
            sertxd(1)
    end select
    goto computer_mode_loop