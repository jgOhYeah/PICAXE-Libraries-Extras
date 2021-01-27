; Receive.bas
; Code for PICAXE microcontrollers to talk to SPI LoRa modules.
; This particular example receive code receives and prints packets to the serial terminal.
; Written by Jotham Gates, December 2020
; https://github.com/jgOhYeah/PICAXE-Libraries-Extras
; TODO: Fix RSSI printing negatives.
#INCLUDE "include/symbols.basinc"
#INCLUDE "include/generated.basinc"
#DEFINE ENABLE_LORA_RECEIVE
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
	gosub setup_lora_receive
	; Finish setup
	low LED_PIN
	
main:
	if LORA_RECEIVED then
		sertxd("Got packet",cr,lf)
		gosub setup_lora_read
		if rtrn != LORA_RECEIVED_CRC_ERROR then
			; Valid packet
			; Length
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
			sertxd(cr,lf,"  - Payload: '")
			for total_length = total_length to 1 step -1 ; So that we don't have to store the packet length.
				gosub read_lora
				sertxd(rtrn)
			next total_length
			sertxd("'",cr,lf,cr,lf)
			
			
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