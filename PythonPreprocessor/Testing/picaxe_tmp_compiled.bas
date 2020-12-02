; Testing file for the unnofficial PICAXE python precompiler
; Mainly a bunch of #INCLUDES and directives
; #INCLUDE "Symbols.basinc"
; *** INSERTED BELOW ***
; Symbols.basinc
; File to be included for testing.
; #PICAXE 14m2
; #COM /dev/ttyUSB0

symbol LED_PIN = B.3
; *** END OF INSERT ***


main:
    gosub high_led_sub
    pause 500
    gosub low_led_sub
    pause 500
    goto main

; #INCLUDE "AnotherFile.basinc"
; *** INSERTED BELOW ***
; AnotherFile.basinc
; File to be included for testing
high_led_sub:
    ; Calling this for the sake of calling a function
    high LED_PIN
    return

low_led_sub:
    ; Calling this for the sake of calling a function
    low LED_PIN
    return
; *** END OF INSERT ***

