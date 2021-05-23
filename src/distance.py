import math 

def computeDistance(positionA, positionB):
	return math.sqrt((positionA[0] - positionB[0])*(positionA[0] - positionB[0]) + (positionA[1] - positionB[1])*(positionA[1] - positionB[1]) + (positionA[2] - positionB[2])*(positionA[2] - positionB[2]))