from stack import Stack

def toCm(value):
	return int(value/10)

def computePosition(frame, spatialCalcQueue):
		inDepthAvg = spatialCalcQueue.get() # Blocking call, will wait until a new data has arrived
		spatialData = inDepthAvg.getSpatialLocations()

		for depthData in spatialData:
				roi = depthData.config.roi
				roi = roi.denormalize(width=frame.shape[1], height=frame.shape[0])
				xmin = int(roi.topLeft().x)
				ymin = int(roi.topLeft().y)
				xmax = int(roi.bottomRight().x)
				ymax = int(roi.bottomRight().y)
								
				return (toCm(depthData.spatialCoordinates.x), toCm(depthData.spatialCoordinates.y), toCm(depthData.spatialCoordinates.z))

		return None
