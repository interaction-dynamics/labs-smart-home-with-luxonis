import numpy as np 

OBJECT_DETECTOR_ROI_WIDTH = 300 
OBJECT_DETECTOR_ROI_HEIGHT = 300

labels = ["background", "aeroplane", "bicycle", "bird", "boat", "bottle", "bus", "car", "cat", "chair", "cow",
						"diningtable", "dog", "horse", "motorbike", "person", "pottedplant", "sheep", "sofa", "train", "tvmonitor"]

np.random.seed(42)
COLORS = np.random.randint(0, 255, size=(len(labels), 3), dtype="uint8")

class BoundingBox:
  def __init__(self, boundingBox):
    self.topLeft = (boundingBox[0], boundingBox[1])
    self.size = (boundingBox[2], boundingBox[3])

# class Position:
#   def _i

# nn data, being the bounding box locations, are in <0..1> range - they need to be normalized with frame width/height
def frameNorm(bbox):
		normVals = np.full(len(bbox), OBJECT_DETECTOR_ROI_HEIGHT)
		normVals[::2] = OBJECT_DETECTOR_ROI_WIDTH
		return (np.clip(np.array(bbox), 0, 1) * normVals).astype(int)

class Object:
  def __init__(self, frame, detection, labels):
    boundingBox = frameNorm((detection.xmin, detection.ymin, detection.xmax, detection.ymax))
    self.label = labels[detection.label]
    self.boundingBox = BoundingBox(boundingBox)
    self.positions = []
    self.status = ''


def detectObjects(frame, objectDetection):
	objects = []
	objectDetectionValue = objectDetection.tryGet()
	if objectDetectionValue is not None:
			for detection in objectDetectionValue.detections: 
				objects.append(Object(frame, detection, labels))

	return objects