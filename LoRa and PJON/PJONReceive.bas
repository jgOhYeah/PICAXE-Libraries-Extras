; PJONReceive.bas
; Code for PICAXE microcontrollers to talk to SPI LoRa modules and use a small implementation of the
; PJON protocol over LoRa.
; This particular example receive code receives and prints PJON packets to the serial terminal.
; Written by Jotham Gates, January 2021
; https://github.com/jgOhYeah/PICAXE-Libraries-Extras

#INCLUDE "include/symbols.basinc"
#INCLUDE "include/generated.basinc"
#DEFINE ENABLE_LORA_RECEIVE
#DEFINE ENABLE_PJON_RECEIVE
; #DEFINE ENABLE_LORA_TRANSMIT
; #DEFINE ENABLE_PJON_TRANSMIT
#PICAXE 14M2
#TERMINAL 38400
#COM /dev/ttyUSB0

; Status LED
symbol LED_PIN = B.3

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

	; gosub idle_lora ; 4.95mA
	; gosub sleep_lora ; 3.16mA
	gosub setup_lora_receive ; 14mA
	; Everything in sleep ; 0.18 to 0.25mA
	; Finish setup
	low LED_PIN
	
main:
	if LORA_RECEIVED then
		sertxd("Got packet")
		gosub read_pjon_packet
		if rtrn != PJON_INVALID_PACKET then
			; Valid packet
			high LED_PIN

			; Length
			sertxd(" from ", #param1, cr, lf)
			total_length = rtrn
			sertxd("  - Length: ",#total_length,cr,lf)
			; RSSI
			gosub packet_rssi
			sertxd("  - RSSI: ")
			gosub print_signed
			; SNR
			gosub packet_snr
			start_time = rtrn % 4 * 5 / 2 ; First digit after decimal point
			rtrn = rtrn / 4
			sertxd(cr,lf,"  - SNR: ")
			gosub print_signed
			sertxd(".",#start_time,cr,lf)
			
			; Payload
			sertxd("  - Payload: '")
			for total_length = total_length to 1 step -1 ; So that we don't have to store the packet length.
				sertxd(#@bptrinc,", ")
			next total_length
			sertxd("'",cr,lf,cr,lf)
			
			low LED_PIN
			
		else
			sertxd("  - CRC Error receiving",cr,lf)
		endif
	endif
	goto main

print_signed:
	; Prints the value stored in rtrn as a 2s complement signed integer
	tmpwd = rtrn & 0x8000
	if tmpwd != 0 then
		; Negative
		sertxd("-")
		tmpwd = rtrn ^ 0xffff + 1 ; Convert to positive
		sertxd(#tmpwd)
	else
		sertxd(#rtrn)
	endif
	return

failed:
	; Flashes the LED on and off to give an indication it isn't happy.
	high LED_PIN
	pause 4000
	low LED_PIN
	pause 4000
	goto failed

; Libraries that will not be run first thing.
#INCLUDE "include/LoRa.basinc"
#INCLUDE "include/PJON.basinc"