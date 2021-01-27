; BatteryVoltsMonitor.bas
; A remote LoRa battery monitor and electric fence energiser switch.
; Jotham Gates, Jan 2021
; https://github.com/jgOhYeah/PICAXE-Libraries-Extras
;
; FLASH MODES:
; Sleeping: One flash ~once per minute
; Actively listening: One flash every half second
; Cannot connect to LoRa module on start: Constant long flashes (on half second, off half second).
;
#INCLUDE "include/symbols.basinc"
#INCLUDE "include/generated.basinc"
#DEFINE ENABLE_LORA_RECEIVE
#DEFINE ENABLE_PJON_RECEIVE
#DEFINE ENABLE_LORA_TRANSMIT
#DEFINE ENABLE_PJON_TRANSMIT
#PICAXE 14M2
#TERMINAL 38400
; #COM /dev/ttyUSB0

; Sensors
; #DEFINE ENABLE_TEMP
; #DEFINE ENABLE_FVR

; Sensors and control
symbol BATTERY_PIN = B.2
#IFDEF ENABLE_TEMP
symbol TEMPERATURE_PIN = B.1
#ENDIF
symbol FENCE_PIN = B.4

; Status LED
symbol LED_PIN = B.3

; Variables unique to this - see symbols.basinc for the rest
symbol fence_enable = bit0
symbol transmit_enable = bit1

; Constants
symbol LISTEN_TIME = 120 ; Listen for 60s (number of 0.5s counts) after each transmission
symbol SLEEP_TIME = 5 ; Roughly 5 mins at 26*2.3s each ; TODO: Save in eeprom and adjust OTA?
symbol RECEIVE_FLASH_INT = 1 ; Every half second

; Temperature and battery voltage calibration
symbol CAL_BATT_NUMERATOR = 58
symbol CAL_BATT_DENOMINATOR = 85
#IFDEF ENABLE_TEMP
symbol CAL_TEMP_NUMERATOR = 52
symbol CAL_TEMP_DENOMINATOR = 17
#ENDIF

init:
	; Initial setup
	high FENCE_PIN ; Fence is fail deadly to keep cattle in at all costs :)
	fence_enable = 1
	transmit_enable = 1

	setfreq m32
	high LED_PIN
	sertxd("Electric Fence Controller", cr, lf, "Jotham Gates, Jan 2021", cr, lf)
	; Attempt to start the module
	gosub begin_lora
	if rtrn = 0 then
		sertxd("Failed to start LoRa",cr,lf)
		goto failed
	else
		sertxd("LoRa Started",cr,lf)
	endif

	; Set the spreading factor
	gosub set_spreading_factor

	; gosub idle_lora ; 4.95mA
	; gosub sleep_lora ; 3.16mA
	gosub setup_lora_receive ; 14mA
	; Everything in sleep ; 0.18 to 0.25mA
	; Finish setup
	low LED_PIN
	
main:
	; Create and send a packet with the temperature and measured battery voltage
	if transmit_enable = 1 then
		gosub send_status
	endif
	Sertxd("Sent packet", cr, lf)

	; Go into listen mode
	; Listens for the designated time and handles incoming packets
	pulsout LED_PIN, 10000
	; sertxd("Entering receive mode", cr, lf)
	gosub setup_lora_receive
	start_time = time
	rtrn = time ; Start time for led flashing
	do
		; Handle packets arriving
		if LORA_RECEIVED then
			; sertxd("DI0 high", cr, lf)
			gosub read_pjon_packet
			if rtrn != PJON_INVALID_PACKET then
				sertxd("Valid", cr, lf)
				; Valid packet
				high LED_PIN
				; Processing and actions
				level = 0 ; Whether to send the status back
				do while rtrn > 0 ; rtrn is the length left
					mask = @bptrinc ; Field is stored in mask
					dec rtrn
					select mask
						case 0xC6 ; "F" | 0x80 ; Fence on and off
							; 1 byte, 0 for off, anything else for on.
							sertxd("Fence ")
							if rtrn > 0 then
								if @bptrinc = 0 then
									sertxd("Off", cr, lf)
									fence_enable = 0
									low FENCE_PIN
								else
									sertxd("On", cr, lf)
									fence_enable = 1
									high FENCE_PIN
								endif
								dec rtrn
							endif
							level = 1
						case 0xF2 ; "r" | 0x80 ; Radio transmissions on and off
							; 1 byte, 0 for off, anything else for on.
							sertxd("Transmit ")
							if rtrn > 0 then
								if @bptrinc = 0 then
									sertxd("Off", cr, lf)
									transmit_enable = 0
								else
									sertxd("On", cr, lf)
									transmit_enable = 1
								endif
								dec rtrn
							endif
							level = 1
						case 0xF3 ; "s" | 0x80 ; Request status, msb is high as it is an instruction
							; No payload.
							sertxd("Status", cr, lf)
							level = 1
						else
							; Something not recognised or implemented
							; NOTE: Should the rest of the packet be discarded to ensure any possible data of unkown length is not treated as a field?
							sertxd("Field ", #mask, " unkown", cr, lf)
					endselect
				loop
				if level = 1 then
					gosub send_status ; Reply with the current settings if needed
					gosub setup_lora_receive ; Go back to listening
				endif
				sertxd("Finished", cr, lf)

				low LED_PIN
				start_time = time ; Reset the time. Possible security risk of being able to keep the box in high power state?
				rtrn = time
			else
				sertxd("Invalid", cr, lf)
			endif
		endif

		; Flash the LED every half second
		tmpwd = time - rtrn
		if tmpwd >= RECEIVE_FLASH_INT then
			pulsout LED_PIN, 10000
			rtrn = time
		endif
		tmpwd = time - start_time
	loop while tmpwd < LISTEN_TIME

	; Go into power saving mode
	; TODO: Flash led once per minute
	sertxd("Entering sleep mode", cr, lf)
	gosub sleep_lora
	low LED_PIN
	
	disablebod
	for counter = 1 to SLEEP_TIME
		sleep 26 ; About 1 minute
		pulsout LED_PIN, 10000
	next counter
	enablebod
	goto main

send_status:
	; Sends the monitor's status
	high LED_PIN
	sertxd("Sending state", cr, lf)
	
	gosub begin_pjon_packet

	; Battery voltage
	@bptrinc = "V"
	gosub get_voltage
	gosub add_word
	sertxd("Batt is: (", #rtrn, "*0.1) V", cr, lf)

	; Temperature
#IFDEF ENABLE_TEMP
	@bptrinc = "T"
	gosub get_temperature
	gosub add_word
	sertxd("Temp is: (", #rtrn, "*0.1 C", cr, lf)
#ENDIF

	; Fence enable
	sertxd("Fence: ", #fence_enable, cr, lf)
	@bptrinc = "F"
	@bptrinc = fence_enable

	; Transmit enable
	sertxd("Transmit: ", #transmit_enable, cr, lf)
	@bptrinc = "r"
	@bptrinc = transmit_enable
	param1 = UPRSTEAM_ADDRESS
	sertxd(cr, lf)
	gosub end_pjon_packet
	if rtrn = 0 then ; Something went wrong. Attempt to reinitialise the radio module.
		sertxd("LoRa dropped out.")
		for tmpwd = 0 to 15
			toggle LED_PIN
			pause 4000
		next tmpwd

		gosub begin_lora
		if rtrn != 0 then ; Reconnected ok. Set up the spreading factor.
			sertxd("Reconnected ok")
			param1 = LORA_SPREADING_FACTOR
			gosub set_spreading_factor
		else
			sertxd("Could not reconnect")
		endif
	endif
	low LED_PIN
	return

failed:
	; Flashes the LED on and off to give an indication it isn't happy.
	high LED_PIN
	pause 4000
	low LED_PIN
	pause 4000
	goto failed

get_voltage:
	; Calculates the supply voltage in 0.1V steps (255 = 25.5V)
	; fvrsetup FVR2048 ; set FVR as 2.048V
	; adcconfig %011 ; set FVR as ADC Vref+, 0V Vref-
	; readadc10 BATTERY_PIN, rtrn
#IFDEF ENABLE_FVR
	fvrsetup FVR2048 ; set FVR as 2.048V
	adcconfig %011 ; set FVR as ADC Vref+, 0V Vref-
#ENDIF
	readadc10 BATTERY_PIN, rtrn ; Do it twice to try and avoid croos talk from the first reading
	rtrn = rtrn * CAL_BATT_NUMERATOR / CAL_BATT_DENOMINATOR
	return

#IFDEF ENABLE_TEMP
get_temperature: ; DS18B20
	; sertxd("Temp ADC: ",#rtrn)
	readtemp12 TEMPERATURE_PIN, rtrn
	; sertxd("Temp raw: ",#rtrn)
	rtrn = rtrn * 10 / 16
	; sertxd(" Calc: ",#rtrn,cr,lf)
	return
#ENDIF


add_word:
	; Adds a word to @bptr in little endian format.
	; rtrn contains the word to add (it is a word)
	@bptrinc = rtrn & 0xff
	tmpwd = rtrn / 0xff
	@bptrinc = tmpwd
	return

; println:
	; param1 is the address in the table
	; TODO: Print from table, allows more debugging prints without filling instructions

; Libraries that will not be run first thing.
#INCLUDE "include/LoRa.basinc"
#INCLUDE "include/PJON.basinc"