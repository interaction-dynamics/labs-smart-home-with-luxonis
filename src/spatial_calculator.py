
def convertToDm(value):
	return int(value/10)

def computePosition(frame, spatialCalcQueue):
		positions = []
		inDepthAvg = spatialCalcQueue.get() # Blocking call, will wait until a new data has arrived
		spatialData = inDepthAvg.getSpatialLocations()

		for depthData in spatialData:
				roi = depthData.config.roi
				roi = roi.denormalize(width=frame.shape[1], height=frame.shape[0])
				xmin = int(roi.topLeft().x)
				ymin = int(roi.topLeft().y)
				xmax = int(roi.bottomRight().x)
				ymax = int(roi.bottomRight().y)
								
				positions.append((convertToDm(depthData.spatialCoordinates.x), convertToDm(depthData.spatialCoordinates.y), convertToDm(depthData.spatialCoordinates.z)))