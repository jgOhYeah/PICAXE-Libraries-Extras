; Example usage of a converted tune
; Code written by Jotham Gates, 13/12/2020.
; The song 'Botany Bay' is an Australian folk tune

; Unmodified output from the musescore plugin:
; tune pin, speed, (103,105,43,2,2,41,0,0,107,105,167,2,43,2,7,0,4,7,2,130,2,7,6,7,9,7,4,66,107,167,103,105,43,2,2,41,0,43,39,167,66,64,43,2,2,41,0,0,107,105,167,66,64,43,2,7,0,4,7,2,130,66,66,7,6,7,9,7,4,66,107,167,103,105,43,2,2,41,0,43,39,167) 'Converted from Botany_Bay_-_PICAXE_Demo

main:
	; With pin C.2 and a speed of 162bpm (5). Double check in the manual which pins can be used on which parts.
	tune C.2, 5, (103,105,43,2,2,41,0,0,107,105,167,2,43,2,7,0,4,7,2,130,2,7,6,7,9,7,4,66,107,167,103,105,43,2,2,41,0,43,39,167,66,64,43,2,2,41,0,0,107,105,167,66,64,43,2,7,0,4,7,2,130,66,66,7,6,7,9,7,4,66,107,167,103,105,43,2,2,41,0,43,39,167) 'Converted from Botany_Bay_-_PICAXE_Demo
	goto main
