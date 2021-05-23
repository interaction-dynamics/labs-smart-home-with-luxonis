from convert import to_planar, frameNorm

class BoundingBox:
  def __init__(self, boundingBox):
    self.topLeft = (boundingBox[0], boundingBox[1])
    self.size = (boundingBox[2], boundingBox[3])

# class Position:
#   def _i

class Object:
  def __init__(self, frame, detection, labels):
    boundingBox = frameNorm(frame, (detection.xmin, detection.ymin, detection.xmax, detection.ymax))
    self.label = labels[detection.label]
    self.boundingBox = BoundingBox(boundingBox)
    self.positions = []
    self.status = ''