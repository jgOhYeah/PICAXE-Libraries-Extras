#!/usr/bin/env python3
# Calculates the required calibration factor for a voltage divider to get a number in units using integers.
# Designed for expressions like voltage = adc_reading * numerator / denominator.
# This aims to calculate the most accurate numerator and denominator, with the restriction that the
# numerator * adc_reading should never overflow (in the case of a PICAXE, be > 16 bits).
# Written by Jotham Gates, December 2020

import math
from fractions import Fraction

# Use the excel spreadsheet to calculate the ideal values and select something near
#
# Battery +
# ----------
#          |
#          <
#          < r1
#          <
#          |
#          |-----> Picaxe
#          |
#          <
#          < r2
#          <
#          |
# ------------------
# Ground

r1 = 119e3
r2 = 5583

# Stuff relating to how the microcontroller is set up
bit_depth = 10 # readadc10 is 10 bit, readadc is 8 bit
#adc_ref = 2.048
adc_ref = 0.93 # Supply voltage
word_size = 16 # Number of bits to play around with before we start to get overflow.
voltage_multiplier = 10 # 1 for whole Vs, 10 so 0.1V steps...
temperature_multiplier = 10 # 1 for whole degrees, 10 for 0.1 degrees...

def adc_to_volts(adc, numerator, denominator, integer_mode=True):
    """ Tests out the callibration factor
    :param integer_mode: If true (default), uses integer division like uC, if False, floating point.
    """
    tmp = adc * numerator
    if tmp > (2**word_size - 1):
        raise ValueError("Numerator is too high and would have allowed overflow")

    if integer_mode:
        return tmp // denominator
    else:
        return tmp / denominator

def cf_to_fraction(cf, bit_depth=bit_depth, word_size=word_size):
    """ Determines the best possible calibration factor """
    cff = Fraction(cf)
    print("Calibration fraction is: {}".format(cff))

    # Calculate the required maximum denominator so that the numerator will not overflow
    max_numerator = (2**word_size - 1) // (2**bit_depth - 1)
    max_denominator = math.floor(max_numerator / cf)
    print("Max numerator: {}, Max demoninator: {}".format(max_numerator, max_denominator))

    # Generate the fraction
    cff = cff.limit_denominator(max_denominator)
    print("Closest calibration fraction is: {}".format(cff))

    # Check how this compares to the original calibration factor.
    new_cf = cff.numerator / cff.denominator
    percentage_off = abs(new_cf - cf) / cf * 100
    print("This is {:.4f}% off from the ideal calibration factor.".format(percentage_off))

    return cff
    
# Calculate the calibration factor for the battery voltage
print("BATTERY VOLTAGE:")
cf = voltage_multiplier * adc_ref * (r1 + r2) / ((2**bit_depth - 1) * r2) # When multiplied by adc, will obtain the voltage in 0.1V increments
print("Voltage calibration factor is: {}".format(cf))
cff = cf_to_fraction(cf)

# Check the minimum steps.
resolution = adc_to_volts(1, cff.numerator, cff.denominator, False) / voltage_multiplier
print("The minimum adc voltage resolution is: {:.4f}V".format(resolution))

# Check the maximum is not over
maximum = adc_to_volts(2**bit_depth - 1, cff.numerator, cff.denominator) / voltage_multiplier
print("Maximum measurable: {}V\n".format(maximum))



# Calculate the cabibration factor for the temperature
print("TEMPERATURE:")
tf = temperature_multiplier * adc_ref * 100 / (2**bit_depth -1)
print("Temperature calibration factor is: {}".format(tf))
tff = cf_to_fraction(tf)

# Check the minimum steps.
resolution = adc_to_volts(1, tff.numerator, tff.denominator, False) / temperature_multiplier
print("The minimum adc temperature resolution is: {:.4f}C".format(resolution))

# Check the maximum is not over
maximum = adc_to_volts(2**bit_depth - 1, tff.numerator, tff.denominator) / temperature_multiplier
print("Maximum measurable: {}C\n".format(maximum))



# Display the callibration factor
print()
print()
print("If this all looks reasonable, then copy the following into the code:")
print("For Picaxe microcontrollers:")
print("symbol CAL_BATT_NUMERATOR = {}".format(cff.numerator))
print("symbol CAL_BATT_DENOMINATOR = {}".format(cff.denominator))
print("symbol CAL_TEMP_NUMERATOR = {}".format(tff.numerator))
print("symbol CAL_TEMP_DENOMINATOR = {}".format(tff.denominator))
print()
print("For Arduino microcontrollers:")
print("#define CAL_BATT_NUMERATOR {}".format(cff.numerator))
print("#define CAL_BATT_DENOMINATOR {}".format(cff.denominator))
print("#define CAL_TEMP_NUMERATOR {}".format(tff.numerator))
print("#define CAL_TEMP_DENOMINATOR {}".format(tff.denominator))
