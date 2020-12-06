class ObjectDictionary():

	def __init__(self):
		self.od = {}		# the literal object dictionary
							# maps a two byte index and one byte subindex to a value
		
		self.od_map = {}	# maps indeces in the object dictionary to 
							# human readable property names

		self.next_index = 0x2000

		# add dummy object
		self.add_key('DUMMY', 0x1008, value = 0)

		# add pdo indeces
		self.add_key('TPDO1_MAP', 0x1A00)
		self.add_key('TPDO1_LENGTH', 0x1A00, 0x00, value = 8)
		self.add_key('TPDO1_01', 0x1A00, 0x01)
		self.add_key('TPDO1_02', 0x1A00, 0x02)
		self.add_key('TPDO1_03', 0x1A00, 0x03)
		self.add_key('TPDO1_04', 0x1A00, 0x04)
		self.add_key('TPDO1_05', 0x1A00, 0x05)
		self.add_key('TPDO1_06', 0x1A00, 0x06)
		self.add_key('TPDO1_07', 0x1A00, 0x07)
		self.add_key('TPDO1_08', 0x1A00, 0x08)

	def __str__(self):
		output = ''

		for key in self.od_map:

			index, sub = self.get_index(key)

			if sub == 255:
				index_str = '{}'.format(hex(index))
			else:
				index_str = '{}sub{}'.format(hex(index), sub)


			line = 'Name: {} \t Value: {} \t Index: {} \n'.format(
				key, self.get_value(key), (index, sub))
			
			output = output + line
		
		return output

	def get_value(self, key, index=None):

		if index == None:
			index = self.od_map[key]

		return self.od[index]

	def get_index(self, key):
		return self.od_map[key]

	def set(self, key, value):
		index = self.get_index(key)
		self.od[index] = value

	def add_key(self, key, index=None, subindex=0xFF, value=0):

		if index == None:
			index = self.next_index
			self.next_index += 1

		self.od_map[key] = (index, subindex)

		self.set(key, value)

	def add_keys(self, keys):

		for key in keys:
			self.add_key(key)

	def set_pdo_map(self, property_list, pdo_number=1):
		pdo_length = len(property_list)

		self.set('TPDO1_LENGTH', pdo_length)

		for i, property in enumerate(property_list, start=1):

			try:
				index = self.get_index(property)
			except:
				print('Error: {} is not defined in object dictionary'.format(property))
				index = self.get_index('DUMMY')

			key = 'TPDO1_0{}'.format(i)
			self.set(key, index)


	def get_pdo_data(self, pdo_number=1):
		pdo_length = self.get_value('TPDO1_LENGTH')
		output = []

		for i in range(1, pdo_length + 1):
			index = self.get_value('TPDO1_0{}'.format(i))
			index_real, sub = index

			output.append(self.get_value('', index))

		return output

