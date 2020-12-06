#!/usr/bin/python3

import time
import redis
data = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)	
p = data.pubsub()
p.subscribe('restart-emulators')

import tsi_emulator
tsi = tsi_emulator.TSI()

# Main update loop, just tell the emulators to update their states
# and wait for a short amount of time
while True:
    # on reset signal
    if p.get_message():
        data.set('emulator:simulation_time', 0)
        data.publish('new-session', 0)

    #ams_emulator.update()
    simulation_time = data.incr('emulator:simulation_time')
    tsi.update(simulation_time)
    time.sleep(0.5)

