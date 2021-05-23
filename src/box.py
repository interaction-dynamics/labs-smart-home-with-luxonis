import cv2
import os
from draw import drawBox, drawLabel, init, drawObject, drawDiamond

dirname = os.path.dirname(__file__)

imageFilename = os.path.join(dirname, '../assets/screenshot.png')
frame = cv2.imread(imageFilename)

start_point = (200, 200)
  
end_point = (1000, 1000)
  
color = (0, 255, 0)

thickness = 2
  
h, w, c = frame.shape

(image, draw) = init(frame)

drawBox(draw, start_point, end_point, color, thickness=2, gap=6)

drawLabel(draw, (20, h - 20), "STATUS: SCANNING FURNITURES...", 20)

drawObject(draw, (200, 190), "HUMAN", (10, 30), "SITTED ON SOFA, 0.5m", True, 18)

drawDiamond(draw, (1000, 500))

image.show("Smart Home")

# cv2.imshow("Frame", frame)
# cv2.waitKey(0)

