from distance import computeDistance2D

THRESOLD_LATENCY = 500

def isClose(p1, p2):
  return computeDistance2D(p1, p2) < THRESOLD_LATENCY

class Stack:
  def __init__(self):
	  self.stack = []

  def add(self, item):
    self.stack.append(item)
    if len(self.stack) > 5:
      self.stack.pop(0)

  def reinitialize(self):
    self.stack = []

  def get(self):
    return self.stack


  def isStable(self, position, minimum = 3):
    if position == None:
      return False
    if len(self.stack) < minimum:
      self.add(position)
      return False
    for p in self.stack: 
        if not isClose(position, p):
            self.add(position)
            return False
    self.add(position)
    return True


