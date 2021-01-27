; Transmit.bas
; Code for PICAXE microcontrollers to talk to SPI LoRa modules.
; This particular example transmit code transmits "Hello world" every so often.
; Written by Jotham Gates, December 2020
; https://github.com/jgOhYeah/PICAXE-Libraries-Extras

; Before spread factor as preprocessor: 855 bytes
; After spread factor as preprocessor: 836 bytes

#INCLUDE "include/symbols.basinc"
#INCLUDE "include/generated.basinc"
#DEFINE ENABLE_LORA_TRANSMIT
#PICAXE 14M2
#TERMINAL 38400
#COM /dev/ttyUSB0

; Status LED
symbol LED_PIN = B.3
#DEFINE TRANSMIT_INTERVAL 2
eeprom 0, ("Hello world")

init:
	; Initial setup
	setfreq m32
	high LED_PIN
	
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
	
	; Load the string to send into ram
	bptr = 28
	for counter2 = 0 to 10
		read counter2, @bptrinc
	next counter2

	; Finish setup
	low LED_PIN
	
main:
	; Create and send a packet with the temperature and measured battery voltage
	high LED_PIN
	gosub begin_lora_packet
	bptr = 28 ; First byte in ram
	param1 = 11 ; Packet length
	gosub write_lora
	gosub end_lora_packet
	if rtrn = 0 then ; Something went wrong. Attempt to reinitialise the radio module.
		sertxd("LoRa dropped out.", cr, lf)
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

	; Go into power saving mode
	gosub sleep_lora
	low LED_PIN
	
	; Wait for a while
	disablebod
	sleep TRANSMIT_INTERVAL
	enablebod
	goto main

failed:
	; Flashes the LED on and off to give an indication it isn't happy.
	high LED_PIN
	pause 4000
	low LED_PIN
	pause 4000
	goto failed

; Libraries that will not be run first thing.
#INCLUDE "include/LoRa.basinc"