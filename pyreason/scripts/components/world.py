import pyreason.scripts.interval.interval as interval


class World:
	
	def __init__(self, labels):
		self._world = {}
		for label in labels:
			self._world[label] = interval.closed(0, 1)

	def is_satisfied(self, label, interval):
		result = False
		
		bnd = self._world[label]
		result = bnd in interval

		return result

	def update(self, label, interval):
		lwanted = None
		bwanted = None 
		
		current_bnd = self._world[label]
		new_bnd = current_bnd.intersection(interval)
		self._world[label] = new_bnd

	def get_bound(self, label):
		result = None

		result = self._world[label] 
		return result

	def get_world(self):
		world = []
		for label in self._world.keys():
			bnd = self._world[label]
			world.append((label.get_value(), interval.closed(bnd.lower, bnd.upper)))
		return world


	def __str__(self):
		result = ''
		for label in self._world.keys():
			result = result + label.get_value() + ',' + self._world[label].to_str() + '\n'

		return result
