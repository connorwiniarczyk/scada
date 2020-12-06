#!/usr/bin/python3

import sys, os
config_path = '/usr/etc/scada/config'
sys.path.append(config_path)

import config
import redis
import time

# open a connection to the redis server where we will
# be writing data
data = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)
listener = data.pubsub()
listener.subscribe('can-message')

# CANOpen function codes
FUNCTIONS = {
	0x000: "NMT",
	0x080: "SYNC",
	0x180: 'PDO-1',
	0x280: 'PDO-2',
	0x380: 'PDO-3',
	0x480: 'PDO-4',
}

def on_message(message):
	message_bytes = message.split(' ')
	cob_id = message_bytes[0]
	message_bytes = message_bytes[1:]

	print(cob_id)
	print(int(cob_id, 16))

	cob_id = int(cob_id, 16)

	# split cob_id into function code and node id
	node = cob_id % 16
	function_code = cob_id - node
	protocol = FUNCTIONS.get(function_code)

	print(node)

	# do processing of PDOs
	if protocol in ['PDO-1', 'PDO-2', 'PDO-3', 'PDO-4']:
		_, pdo_number = protocol.split('-')
		sort_pdo(node, pdo_number, message_bytes)


def sort_pdo(node_id, pdo_number, message_data):
	node = config.get('node_ids').get(node_id)

	pdo_key = node + ("" if pdo_number == "1" else "_" + pdo_number)
	pdo_structure = config.get('process_data').get(pdo_key)

	pipe = data.pipeline()
	for index, byte in enumerate(message_data, start=0):

		byte = int(byte, 16)

		key = '{}:{}'.format(node, pdo_structure[index])
		key = key.lower()
		pipe.setex(key, 10, byte)
	
	data.publish('bus_data', key)
	pipe.execute()

while True:
	message = listener.get_message()
	if message and type(message['data']) == str:
		on_message(message['data'])
	else:
		time.sleep(0.01)


#class Listener(can.Listener):
#	def on_message_received(self, msg):

#		# infer the CANOpen protocol used and node id of sender
#		protocol, node_id = messages.get_info(msg)

##		if protocol == 'SDO-WRITE':
##			if len(msg.data) == 0:
##				return
##
##			# check the config file to find out name of node
##			try:
##				node = config.get('can_nodes').get(node_id)
##			except:
##				return
##
##			control_byte = msg.data[0]
##			index = msg.data[2] * 256 + msg.data[1]
##			subindex = msg.data[3]
##
##			if index == 0x3003:
##				temp = msg.data[5] * 256 + msg.data[4]
##				print(f"cell: {subindex} at temp: {temp}")
##				data.setex(f"pack1:temp:cell_{subindex}",60,temp)

#		# if the protocol used is one of the four types
#		# of PDOs (Process Data Objects), then log it
#		if protocol in ['PDO-1', 'PDO-2', 'PDO-3', 'PDO-4']:

#			_, pdo_number = protocol.split('-')

#			# check the config file to find out name of node
#			try:
#				node = config.get('can_nodes').get(node_id)
#			except:
#				return

#			# check the config file to figure out expected
#			# structure of the process data
#			if pdo_number == '1':
#				pdo_structure = config.get('process_data').get(node)
#			else:
#				pdo_structure = config.get('process_data').get('{}-{}'.format(node, pdo_number))

#			# separate can message into bytes and write each one
#			# to the redis server with its name as defined in the
#			# config file

#			pipe = data.pipeline()

#			for index, byte in enumerate(msg.data, start=0):
#				key = '{}:{}'.format(node, pdo_structure[index])
#				key = key.lower()
#				pipe.setex(key, 10, int(byte))

#			data.publish('bus_data', key)
#			pipe.execute()

#if __name__ == "__main__":
#	bus = utils.bus(config.get('bus_info'))
#	notifier = can.Notifier(bus, [Listener()])

#	for msg in bus:
#		pass
