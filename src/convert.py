import cv2
import numpy as np 

def to_planar(arr: np.ndarray, shape: tuple) -> list:
		return cv2.resize(arr, shape).transpose(2,0,1).flatten()

# nn data, being the bounding box locations, are in <0..1> range - they need to be normalized with frame width/height
def frameNorm(frame, bbox):
		normVals = np.full(len(bbox), frame.shape[0])
		normVals[::2] = frame.shape[1]
		return (np.clip(np.array(bbox), 0, 1) * normVals).astype(int)
