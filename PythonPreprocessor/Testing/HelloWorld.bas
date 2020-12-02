; Testing file for the unnofficial PICAXE python precompiler
; Mainly a bunch of #INCLUDES and directives
#INCLUDE "Symbols.basinc"

main:
    gosub high_led_sub
    pause 500
    gosub low_led_sub
    pause 500
    goto main

#INCLUDE "AnotherFile.basinc"