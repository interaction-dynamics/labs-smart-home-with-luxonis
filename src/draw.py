import cv2
import numpy as np
from PIL import ImageFont, ImageDraw, Image  
from pathlib import Path
import math 
import recognize_pose

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)

def init(img):
		# Convert the image to RGB (OpenCV uses BGR)  
	cv2_im_rgb = cv2.cvtColor(img,cv2.COLOR_BGR2RGB)  
	
	# Pass the image to PIL  
	pil_im = Image.fromarray(cv2_im_rgb)
	draw = ImageDraw.Draw(pil_im)
	return (pil_im, draw)


def convert(img):
	image = np.array(img)
	return cv2.cvtColor(image,cv2.COLOR_RGB2BGR)  

def drawLine(draw,pt1,pt2,color,thickness=1,gap=20):
	dist =((pt1[0]-pt2[0])**2+(pt1[1]-pt2[1])**2)**.5
	pts= []
	for i in  np.arange(0,dist,gap):
		r=i/dist
		x=int((pt1[0]*(1-r)+pt2[0]*r)+.5)
		y=int((pt1[1]*(1-r)+pt2[1]*r)+.5)
		p = (x,y)
		pts.append(p)

	s=pts[0]
	e=pts[0]
	i=0
	for p in pts:
		s=e
		e=p
		if i%2==1:
			draw.line([s,e], fill=color, width=thickness)
		i+=1

def drawRectangle(draw, topLeft, bottomRight, color, thickness, gap):
	(x1, y1) = topLeft 
	(x2, y2) = bottomRight 
	drawLine(draw,topLeft,(x2, y1),color,thickness,gap)
	drawLine(draw,(x2, y1),bottomRight,color,thickness,gap)
	drawLine(draw,bottomRight,(x1, y2),color,thickness,gap)
	drawLine(draw,(x1, y2),topLeft,color,thickness,gap)

def drawBox(draw, topLeft, bottomRight, color, thickness, gap):
	drawRectangle(draw, topLeft, bottomRight, color, thickness, gap)
	(x1, y1) = topLeft 
	(x2, y2) = bottomRight

	width = abs(x1 - x2)
	height = abs(y1 -y2)

	borderSize = round(min(width, height) * 0.1)
	borderThickness = round(thickness * 5)
	margin = 2

	draw.rectangle([(x1 - margin, y1 - margin), (x1 + borderSize, y1 + borderThickness)], fill=color)
	draw.rectangle([(x1 - margin, y1 - margin), (x1 + borderThickness, y1 + borderSize)], fill=color)

	draw.rectangle([(x2 + margin, y2 + margin), (x2 - borderThickness, y2 - borderSize)], fill=color)
	draw.rectangle([(x2 + margin, y2 + margin), (x2 - borderSize, y2 - borderThickness)], fill=color)

	draw.rectangle([(x1 + margin + width, y1 - margin), (x1 + width - borderThickness, y1 + borderSize)], fill=color)
	draw.rectangle([(x1 + margin + width, y1 - margin), (x1 + width - borderSize, y1 + borderThickness)], fill=color)

	draw.rectangle([(x1 - margin, y1 + margin + height), (x1 + borderThickness, y1 + height - borderSize)], fill=color)
	draw.rectangle([(x1 - margin, y1 + margin + height), (x1 + borderSize, y1 + height - borderThickness)], fill=color)

	notchSize = round(min(width, height) * 0.03)
	notchThickness = round(min(width, height) * 0.01)

	draw.rectangle([(round(x1 + width / 2 - notchThickness / 2) , y1 - margin), (round(x1 + width / 2 + notchThickness / 2), y1 + notchSize)], fill=color)
	draw.rectangle([(x1 - margin,  round(y1 + height / 2 - notchThickness / 2)), (x1 + notchSize , round(y1 + height / 2 + notchThickness / 2))], fill=color)
	draw.rectangle([(round(x1 + width / 2 - notchThickness / 2) , y2 + margin), (round(x1 + width / 2 + notchThickness / 2), y2 - notchSize)], fill=color)
	draw.rectangle([(x2 + margin,  round(y1 + height / 2 - notchThickness / 2)), (x2 - notchSize , round(y1 + height / 2 + notchThickness / 2))], fill=color)

filename = str((Path(__file__).parent / Path('assets/Jost-500-Medium.ttf')).resolve().absolute())


def drawLabel(draw, bottomLeft, text, fontSize):
	font_futura = ImageFont.truetype(filename, fontSize) 
	padding = round(fontSize / 2)
	height = round(fontSize / 1.3)

	borderWidth = 2
	white = (255, 255, 255)
	x = bottomLeft[0]
	y = bottomLeft[1] - 2 * padding - 2 * borderWidth - height
	# topLeft = (bottomLeft[0], bottomLeft[1] - 2 * padding - 2 * borderWidth - 3 * lineHeight - 2 * lineSpacing)
	# (x, y) = topLeft
	width = round(len(text) * fontSize / 1.4)
	black = (0, 0, 0)

	draw.rectangle([(x, y), (x + width + 2 * padding + 2 * borderWidth, y + height + 2 * padding + 2 * borderWidth)], fill=white)
	draw.rectangle([(x + borderWidth, y + borderWidth), (x + borderWidth + width + 2 * padding, y + borderWidth + height + 2 * padding)], fill=black)
	# draw.rectangle([(x + borderWidth + padding, y + borderWidth + padding), (x + borderWidth + width + padding, y + borderWidth + height + padding)], fill=(0, 0, 255))
	draw.text(xy = (x + borderWidth + padding, y + borderWidth + padding - round(height / 2)), text = text, fill = white, font = font_futura, align ="left")


def drawDiamond(draw, center):
	borderWidth = 4

	width = 20
	(x, y) = center

	draw.polygon([ (x, y - width - borderWidth), (x + width + borderWidth, y), (x, y + width + borderWidth), (x - width - borderWidth, y)], fill=(255, 255, 255))   
	draw.polygon([ (x, y - width), (x + width, y), (x, y + width), (x - width, y)], fill=(0, 0, 0))   


def drawObject(draw, bottomLeft, name, location, status, isValid, fontSize):
	borderWidth = 2

	font_futura = ImageFont.truetype(filename, fontSize) 
	padding = 10
	lineHeight = round(fontSize / 1.3)
	lineSpacing = 7
	height = lineHeight * 3 + 2 * lineSpacing

	# top left
	x = bottomLeft[0]
	y = bottomLeft[1] - 2 * padding - 2 * borderWidth - height

	locationStr = "LOCATION: "+str(location[0])+", "+str(location[1])
	statusStr = "STATUS:  " + status
	fontWidth = fontSize / 1.775
	width = round(max(len(name), len(locationStr), len(statusStr)) * fontWidth)
	lineWidth = round(len("STATUS: ") * fontWidth)


	draw.rectangle([(x, y), (x + width + 2 * padding + 2 * borderWidth, y + height + 2 * padding + 2 * borderWidth)], fill=WHITE)
	draw.rectangle([(x + borderWidth, y + borderWidth), (x + borderWidth + width + 2 * padding, y + borderWidth + height + 2 * padding)], fill=BLACK)
	draw.text(xy = (x + borderWidth + padding, y + borderWidth + padding - round(lineHeight / 2)), text = name, fill = WHITE, font = font_futura, align ="left")
	draw.text(xy = (x + borderWidth + padding, y + borderWidth + padding + lineHeight + lineSpacing - round(lineHeight / 2)), text = locationStr, fill = WHITE, font = font_futura, align ="left")
	draw.text(xy = (x + borderWidth + padding, y + borderWidth + padding + 2 * lineHeight + 2 * lineSpacing - round(lineHeight / 2)), text = "STATUS: ", fill = WHITE, font = font_futura, align ="left")

	statusColorBg = (0, 255, 0)
	statusColorFg = BLACK
	if not isValid:
		statusColorBg = (255, 0, 0)
		statusColorFg = WHITE

	verticalLabelPadding = 3
	horizontalLabelPadding = 2

	draw.rectangle([(x + borderWidth + padding + lineWidth - horizontalLabelPadding, y + borderWidth + padding + 2 * lineHeight + 2 * lineSpacing - verticalLabelPadding), (x + borderWidth + padding + lineWidth + round(len(status) * fontWidth) + horizontalLabelPadding, y + borderWidth + padding + 3 * lineHeight + 2 * lineSpacing + verticalLabelPadding)], fill=statusColorBg)
	draw.text(xy = (x + borderWidth + padding + lineWidth, y + borderWidth + padding + 2 * lineHeight + 2 * lineSpacing - round(lineHeight / 2)), text = status, fill = statusColorFg, font = font_futura, align ="left")


def drawBoundingBox(draw, label, topLeft, size):
	(x, y) = topLeft
	(w, h) = size
	drawBox(draw, (x, y), (x+w, y+h), color=GREEN, thickness=2, gap=6)
	drawLabel(draw, (x, y-5), label.upper(), 15)

def drawObjectBoundingBoxes(draw, objects):
	for object in objects:
		drawBoundingBox(draw, object.label, object.boundingBox.topLeft, object.boundingBox.size)

def drawSkeleton(frame, draw, keypoints_list, detected_keypoints, personwiseKeypoints):
	height, width, _ = frame.shape
	ratioX = width / recognize_pose.POSE_ROI_WIDTH
	ratioY = height / recognize_pose.POSE_ROI_HEIGHT

	if keypoints_list is not None and detected_keypoints is not None and personwiseKeypoints is not None:
		# for i in range(18):
		#     for j in range(len(detected_keypoints[i])):
		#     	(x, y) = detected_keypoints[i][j][0:2]
		# 		x = np.int32(x * ratioX)
		# 		y = np.int32(y * ratioY)
		# 		# cv2.circle(frame, (x, y)  , 5, colors[i], -1, cv2.LINE_AA)
												
		for i in range(17):
			for n in range(len(personwiseKeypoints)):
				index = personwiseKeypoints[n][np.array(recognize_pose.POSE_PAIRS[i])]
				if -1 in index:
					continue

				B = np.int32(keypoints_list[index.astype(int), 0] * ratioX)
				A = np.int32(keypoints_list[index.astype(int), 1] * ratioY)
					
				color = (recognize_pose.colors[i][0], recognize_pose.colors[i][1], recognize_pose.colors[i][2])
				draw.line([(B[0], A[0]), (B[1], A[1])], fill=color, width=3)


def drawStatus(frame, draw, status):
	h, w, c = frame.shape
	drawLabel(draw, (20, h - 20), "STATUS: "+ status.upper(), 20)
