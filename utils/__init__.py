# import utils.messages
import utils.object_dictionary
# import utils.calibration
# import can

# ObjectDictionary = object_dictionary.ObjectDictionary

# def bus(bus_info):

# 	try:
# 		bustype = bus_info['bustype']
# 	except:
# 		return

# 	if bustype == 'virtual':
# 		return can.interface.Bus('main', bustype=bustype)

# 	elif bustype == 'socketcan':
# 		return can.interface.Bus(bustype='socketcan', channel=bus_info['channel'], bitrate=bus_info['bitrate'])
