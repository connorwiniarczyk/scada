#!/usr/bin/python3

import sys, os

lib_path = '/usr/etc/scada'
config_path = '/usr/etc/scada/config'

sys.path.append(lib_path)
sys.path.append(config_path)

import config
import time, datetime
import redis
import psycopg2

car_state = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
database = psycopg2.connect(
	user='fsae',
	password='cables',
	host='localhost',
	port='5432',
	database = 'demo'
)

p = car_state.pubsub()
p.subscribe('bus_data')
p.subscribe('calculated_data')
p.subscribe('new-session')

cursor = database.cursor()

# Uncomment this to wipe the database on startup of 
# this script, sometimes useful when debugging
# 
# cursor.execute(""" 
# 	DROP TABLE IF EXISTS sensors;
# 	DROP TABLE IF EXISTS data;
# """)

# Make sure both of our tables exist before starting
cursor.execute("""
CREATE TABLE IF NOT EXISTS data(
	id SERIAL PRIMARY KEY,
	sensor_id VARCHAR(255) NOT NULL,
	value VARCHAR(255),
	timestamp TIMESTAMP DEFAULT NOW()
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS sensors(
	id SERIAL PRIMARY KEY,
	redis_key VARCHAR(255) NOT NULL UNIQUE,
	display_name VARCHAR(255),
	datatype VARCHAR(255),
	unit VARCHAR(255)
);		  
""")

database.commit()



def delimit_session():
        """
        Insert a session delimiter into the data table.
        This is a row with sensor_id of "scada:session"
        and value of "NEW-SESSION"
        """

	cursor.execute("""
		INSERT INTO data (sensor_id, value)		   
		VALUES ('scada:session', 'NEW-SESSION');
	""") 

previous_values = {}
def check_update_ready(key):
	"""
	For a given key, determine if a new row should be added
	to the data table or not. It does this by checking the 
        key against a locally stored dictionary of recently logged
        keys, called previous_values. The dictionary stores both the
        last value logged and the time it was logged. The function
        will return true if either the values are different, or if
        it has been more than a minute since the key was logged last.
	"""

	value, timestamp = previous_values.get(key, (None, datetime.datetime.now()))

	# Always update if the current and previous values are different
	if value != car_state.get(key):
		return True

	# If they are the same, only update if a set amount of time has elapsed
	elapsed_time = datetime.datetime.now() - timestamp
	if elapsed_time > datetime.timedelta(seconds=60):
		return True

	# default
	return False

def update(message, key):
	# Don't log the value if an identical
	# value has been logged recently

	if not check_update_ready(key):
		return

	ignore_keys = []
	for key_string in config.get('dont_log', []):
		ignore_keys = ignore_keys + car_state.keys(key_string)
		
	if not key in ignore_keys:
		cursor.execute("""
			INSERT INTO sensors
			(redis_key)
			VALUES (%s)
			ON CONFLICT (redis_key) DO NOTHING
		""", [key])
		
		cursor.execute("""
			INSERT INTO data (sensor_id, value)
			VALUES (%s, %s)
		""", [key, car_state.get(key)])

		previous_values[key] = (car_state.get(key), datetime.datetime.now())

while True:
	message = p.get_message()
	if message:
		if message['channel'] in ['bus_data', 'calculated_data']:  
			update(message['channel'], message['data'])
		elif message['channel'] == 'new-session':
			delimit_session()		 

	else:
		database.commit()
		time.sleep(0.1)
