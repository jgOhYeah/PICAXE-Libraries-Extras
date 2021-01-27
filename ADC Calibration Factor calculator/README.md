# ADC Calibration Factor calculator
Calculates the required calibration factor for a voltage divider to get a number in units using integers.
Designed for expressions like `voltage = adc_reading * numerator / denominator`.
This aims to calculate the most accurate numerator and denominator, with the restriction that the
`numerator * adc_reading` should never overflow (in the case of a PICAXE, be > 16 bits).
This script is a little rushed and not finished, but it produced some useful number for me.
Written by Jotham Gates, December 2020
