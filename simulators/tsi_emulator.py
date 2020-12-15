#!/usr/bin/python3

import sys, os
import math

lib_path = '/usr/etc/scada/utils'
config_path = '/usr/etc/scada/config'

sys.path.append(lib_path)
sys.path.append(config_path)

import config

import redis
data = redis.Redis(host='redis', password="hackme", port=6379, db=0, decode_responses=True)	

import object_dictionary

class Simulator():
	def __init__(self):
		pass
	def update():
		pass

class TSI(Simulator):
	def __init__(self):
		self.od = object_dictionary.ObjectDictionary()
		pdo_structure = config.get('process_data')['tsi']
		self.od.add_keys(pdo_structure)
		self.od.set_pdo_map(pdo_structure)
		self.od.set('state:int', 1)

		self.state_transitions = [5, 10, 25, 35, 40]

	# update the state of the simulator at each time step
	def update(self, simulation_time):

		state = self.get_state(simulation_time)
		
		# calculate Voltage
		if state == 0 or state == 1:
			voltage = 0
		else:
			voltage = 100

		# motor controller voltage
		if state == 0 or state == 1:
			mc_voltage = 0
		elif state == 2:
			mc_voltage = self.precharge_curve(simulation_time - self.state_transitions[1])
		else:
			mc_voltage = 100
		
		# throttle voltage
		if state == 5:
			throttle = int(127 * math.sin(1 + simulation_time / 180))
		else:
			throttle = 0

		# update object dictionary
		self.od.set('state:int', state)
		self.od.set('voltage:raw', self.fix_voltage(voltage))
		self.od.set('mc_voltage:raw', self.fix_voltage(mc_voltage))
		self.od.set('throttle:raw', throttle)

		pdo = self.od.get_pdo_data()

		# pdo_message = " ".join([hex(byte) for byte in pdo])
		pdo_message = "_".join(["{:02x}".format(byte) for byte in pdo])
		
		data.publish("can-message", "183" + "_" + pdo_message)

		message = "0x183 " + pdo_message
		message = message.replace("0x", "").replace(" ", "-")
		data.lpush("canbuffer", message)
		data.ltrim("canbuffer", 0, 9)

	# determine which drive state the TSI is in based off the current time,
	# with hard coded state transitions
	def get_state(self, time):
		state_transitions = self.state_transitions.copy()
		state_transitions.append(time)
		state_transitions.sort()
		return state_transitions.index(time)
	
	# simulate the shape of the precharge curve with a decaying exponential
	def precharge_curve(self, time):
		return 100 * (1 - math.exp(-1 * 0.25 * time))
	
	# adjust the value of the voltage we are sending to match that of the real TSI
	def fix_voltage(self, v):
		return int((((v / 61) + 1.28) / 5) * 255)

