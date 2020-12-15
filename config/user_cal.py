"""
User Defined Calibration Functions
"""

from utils import calibration
cal_function = calibration.cal_function

# Combine upper and lower bytes of throttle information
# into a single 16 bit integer
@cal_function(output='motor:throttle', arguments=[
	'motor:throttle:byte0',
	'motor:throttle:byte1'
])
def throttle(lsb, msb):
	return msb * 256 + lsb

# Convert pack temperature from celcius to farenheit
@cal_function(output='pack1:temp:farenheit', arguments=['pack1:temp'])
def packtemp_farenheit(temp):
	temp_faranheit = temp * (9/5) + 32
	return temp_faranheit

# Calculates the TS power draw in kW
@cal_function(output='tsi:power', arguments=['tsi:voltage', 'tsi:current'])
def ts_power(voltage, current):
	power = (voltage * current) / 1000
	return power

# Expand the drive state enumeration into a string
@cal_function(output='tsi:state', arguments=['tsi:state:int'])
def state(state_number):
	drive_states = ['GLV-OFF', 'GLV-ON', 'PRECHARGE', 'DRIVE-SETUP', 'READY-TO-DRIVE-SOUND', 'DRIVE']
	return drive_states[state_number]

# Calibrate sensors on the TSI board
@cal_function(output='tsi:cooling_temp', arguments=['tsi:cooling_temp:raw'])
def temp(val):
	voltage = (val / 255) * 3.3
	return (20.439 * voltage * voltage) - (109.78 * voltage) + 153.61

@cal_function(output='tsi:mc_voltage', arguments=['tsi:mc_voltage:raw'])
def mc_voltage(mc_voltage_raw):
	return (((mc_voltage_raw / 255) * 5) - 1.28) * 61

@cal_function(output='tsi:voltage', arguments=['tsi:voltage:raw'])
def ts_voltage(voltage_raw):
	return (((voltage_raw / 255) * 5) - 1.28) * 61

@cal_function(output='tsi:throttle', arguments=['tsi:throttle:raw'])
def throttle(throttle_raw):
	voltage = (throttle_raw / 255) * 3.3
	return voltage * 33 / 18

# calibrate raw data from flow rate sensor
@cal_function(output='tsi:flow_rate', arguments=['tsi:flow_rate:raw'])
def flow_rate(flow_rate):
	return 0 if flow_rate == 0 else 0.0535 + 757.5 * (1/flow_rate)

