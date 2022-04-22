import portion

class NetDiffWorld:

	def __init__(self, labels):
		self._world = {}
		for label in labels:
			self._world[label] = portion.closed(0,1)

	def isSatisfied(self, label, interval):
		result = False
		
		bnd = self._world[label]
		result = bnd in interval

		return result

	def update(self, label, interval):
		lwanted = None
		bwanted = None 
		
		current_bnd = self._world[label]
		new_bnd = current_bnd & interval
		self._world[label] = new_bnd

	def getBound(self, label):
		result = None

		result = self._world[label] 
		return result


	def __str__(self):
		result = ''
		for label in self._world.keys():
			result = result + label.getValue() + ',' + str(self._world[label]) + '\n'

		return result

