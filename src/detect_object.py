from object import Object
import numpy as np 


OBJECT_DETECTOR_ROI_WIDTH = 300 
OBJECT_DETECTOR_ROI_HEIGHT = 300

labels = ["background", "aeroplane", "bicycle", "bird", "boat", "bottle", "bus", "car", "cat", "chair", "cow",
						"diningtable", "dog", "horse", "motorbike", "person", "pottedplant", "sheep", "sofa", "train", "tvmonitor"]

np.random.seed(42)
COLORS = np.random.randint(0, 255, size=(len(labels), 3), dtype="uint8")


def detectObjects(frame, objectDetection):
	objects = []
	objectDetectionValue = objectDetection.tryGet()
	if objectDetectionValue is not None:
			for detection in objectDetectionValue.detections: 
				objects.append(Object(frame, detection, labels))

	return objects