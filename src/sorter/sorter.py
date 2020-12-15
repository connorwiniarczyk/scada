#!/usr/bin/python3

import sys, os
config_path = '/usr/etc/scada/config'
sys.path.append(config_path)

import config
import redis
import time

# open a connection to the redis server where we will
# be writing data
data = redis.Redis(host='redis', password="hackme", port=6379, db=0, decode_responses=True)
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
	message_bytes = message.split('_')
	cob_id = message_bytes[0]
	message_bytes = message_bytes[1:]

	cob_id = int(cob_id, 16)

	# split cob_id into function code and node id
	node = cob_id % 16
	function_code = cob_id - node
	protocol = FUNCTIONS.get(function_code)

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
