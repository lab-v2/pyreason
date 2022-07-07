# import numba
# from numba.experimental.jitclass import jitclass

# spec = [
#     ('_lower', numba.types.float32),
#     ('_upper', numba.types.float32),
#     ('_left', numba.types.unicode_type),
#     ('_right', numba.types.unicode_type)

# ]

# @jitclass(spec)
# class Interval:
# 	"""
# 	No support for open, closedopen, openclosed
# 	"""
# 	def __init__(self, left, lower, upper, right):
# 		self._lower = lower
# 		self._upper = upper
# 		self._left = left
# 		self._right = right

# 	@property
# 	def lower(self):
# 		return self._lower

# 	@property
# 	def upper(self):
# 		return self._upper

# 	def to_str(self):
# 		interval = f'{self._left}{self._lower},{self._upper}{self._right}'
# 		return interval

# 	def intersection(self, interval):
# 		lower = max(self._lower, interval.lower)
# 		upper = min(self._upper, interval.upper)
# 		return Interval('[', lower, upper, ']')

# 	def __contains__(self, item):
# 		if self._lower <= item.lower and self._upper >= item.upper:
# 			return True
# 		else:
# 			return False
            
# 	def equals(self, interval):
# 		if self.lower == interval.lower and self.upper == interval.upper:
# 			return True
# 		else:
# 			return False

# 	# def __eq__(self, interval):
# 	# 	if self.lower == interval.lower and self.upper == interval.upper:
# 	# 		return True
# 	# 	else:
# 	# 		return False

# 	def __repr__(self):
# 		return self.to_str()

# 	def __lt__(self, other):
# 		if self.upper < other.lower:
# 			return True
# 		else:
# 			return False

# 	def __le__(self, other):
# 		if self.upper <= other.upper:
# 			return True
# 		else:
# 			return False

# 	def __gt__(self, other):
# 		if self.lower > other.upper:
# 			return True
# 		else:
# 			return False

# 	def __ge__(self, other):
# 		if self.lower >= other.lower:
# 			return True
# 		else:
# 			return False



# @numba.jit(nopython=True)
# def closed(lower, upper):
# 	return Interval('[', lower, upper, ']')



class Interval:
	"""
	No support for open, closedopen, openclosed
	"""
	def __init__(self, left, lower, upper, right):
		self._lower = lower
		self._upper = upper
		self._left = left
		self._right = right

	@property
	def lower(self):
		return self._lower

	@property
	def upper(self):
		return self._upper

	def to_str(self):
		interval = f'{self._left}{self._lower},{self._upper}{self._right}'
		return interval

	def intersection(self, interval):
		lower = max(self._lower, interval.lower)
		upper = min(self._upper, interval.upper)
		return Interval('[', lower, upper, ']')

	def __contains__(self, item):
		if self._lower <= item.lower and self._upper >= item.upper:
			return True
		else:
			return False

	def __eq__(self, interval):
		if self.lower == interval.lower and self.upper == interval.upper:
			return True
		else:
			return False

	def __repr__(self):
		return self.to_str()

	def __lt__(self, other):
		if self.upper < other.lower:
			return True
		else:
			return False

	def __le__(self, other):
		if self.upper <= other.upper:
			return True
		else:
			return False

	def __gt__(self, other):
		if self.lower > other.upper:
			return True
		else:
			return False

	def __ge__(self, other):
		if self.lower >= other.lower:
			return True
		else:
			return False




def closed(lower, upper):
	return Interval('[', lower, upper, ']')


# def open(lower, upper):
# 	return Interval('(', lower, upper, ')')


# def closedopen(lower, upper):
# 	return Interval('[', lower, upper, ')')


# def openclosed(lower, upper):
# 	return Interval('(', lower, upper, ']')
