#!/usr/bin/python3

import sys, os

import can
import config

import random

import utils
from utils import object_dictionary
from utils import messages

bus = utils.bus(config.get('bus_info'))
notifier = can.Notifier(bus, [])

od = object_dictionary.ObjectDictionary()

od.add_key('voltage')
od.add_key('current')
od.add_key('state_of_charge_01')
od.add_key('SOC_2')
od.add_key('AMBIENT_TEMP')
od.add_key('MIN_CELL_TEMP')
od.add_key('AVG_CELL_TEMP')
od.add_key('MAX_CELL_TEMP')

od.add_key('SEGMENT_01_TEMPS', index=0x3001)
od.add_key('CELL_01_TEMP', index=0x3001, subindex=0x00)
od.add_key('CELL_02_TEMP', index=0x3001, subindex=0x01)
od.add_key('CELL_03_TEMP', index=0x3001, subindex=0x02, value=25)
od.add_key('CELL_04_TEMP', index=0x3001, subindex=0x03)
od.add_key('CELL_05_TEMP', index=0x3001, subindex=0x04)
od.add_key('CELL_06_TEMP', index=0x3001, subindex=0x05)
od.add_key('CELL_07_TEMP', index=0x3001, subindex=0x06)
od.add_key('CELL_08_TEMP', index=0x3001, subindex=0x07)

od.add_key('SEGMENT_02_TEMPS', index=0x3002)
od.add_key('CELL_09_TEMP', index=0x3002, subindex=0x00)
od.add_key('CELL_10_TEMP', index=0x3002, subindex=0x01, value=8)
od.add_key('CELL_11_TEMP', index=0x3002, subindex=0x02, value=25)
od.add_key('CELL_12_TEMP', index=0x3002, subindex=0x03)
od.add_key('CELL_13_TEMP', index=0x3002, subindex=0x04)
od.add_key('CELL_14_TEMP', index=0x3002, subindex=0x05)
od.add_key('CELL_15_TEMP', index=0x3002, subindex=0x06)
od.add_key('CELL_16_TEMP', index=0x3002, subindex=0x07)

od.add_key('SEGMENT_01_VOLTAGES', index=0x3003)
od.add_key('CELL_01_VOLTAGE', index=0x3003, subindex=0x00)
od.add_key('CELL_02_VOLTAGE', index=0x3003, subindex=0x01)
od.add_key('CELL_03_VOLTAGE', index=0x3003, subindex=0x02)
od.add_key('CELL_04_VOLTAGE', index=0x3003, subindex=0x03)
od.add_key('CELL_05_VOLTAGE', index=0x3003, subindex=0x04)
od.add_key('CELL_06_VOLTAGE', index=0x3003, subindex=0x05)
od.add_key('CELL_07_VOLTAGE', index=0x3003, subindex=0x06)
od.add_key('CELL_08_VOLTAGE', index=0x3003, subindex=0x07)

od.add_key('SEGMENT_02_VOLTAGES', index=0x3004)
od.add_key('CELL_09_VOLTAGE', index=0x3004, subindex=0x00)
od.add_key('CELL_10_VOLTAGE', index=0x3004, subindex=0x01)
od.add_key('CELL_11_VOLTAGE', index=0x3004, subindex=0x02)
od.add_key('CELL_12_VOLTAGE', index=0x3004, subindex=0x03)
od.add_key('CELL_13_VOLTAGE', index=0x3004, subindex=0x04)
od.add_key('CELL_14_VOLTAGE', index=0x3004, subindex=0x05)
od.add_key('CELL_15_VOLTAGE', index=0x3004, subindex=0x06)
od.add_key('CELL_16_VOLTAGE', index=0x3004, subindex=0x07)

od.set_pdo_map(config.get('process_data')['PACK1'])

time = 0
maxval = 85
def ramp(t):
	return t % maxval

x = 37
y = 23
soc1 = 67
soc2 = 74
def update():
	global time, x, y, soc1, soc2
	
	od.set('AMBIENT_TEMP', ramp(time))
	time = time + 1
	
	if x == 0:
		soc1 = soc1 - 1
		od.set('SOC_1', soc1)
		x = 37
	x = x - 1

	if y == 0:
		soc2 = soc2 - 1
		od.set('SOC_2', soc2)
		y = 23
	y = y - 1

	od.set('VOLTAGE', 60 + random.randint(-5, 5))

	od.set('CURRENT', 6)

class Listener(can.Listener):
	def __init__(self, node_id):
		self.node_id = node_id

	def on_message_received(self, msg):

		function, node = messages.get_info(msg)

		# sync
		if function == 'SYNC':
			data = od.get_pdo_data()
			msg = messages.pdo(self.node_id, data)
			bus.send(msg)

		# sdo read
		if function == 'SDO-READ' and node == self.node_id:

			command = msg.data[0]
			index = int.from_bytes(msg.data[1:3], byteorder='big')
			subindex = msg.data[3]

			value = od.get_value('', index=(index, subindex))

			new_index = [msg.data[1], msg.data[2]]
			response = messages.sdo_response(self.node_id, new_index, subindex, value)
			bus.send(response)
