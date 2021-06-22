import argparse
import threading
import time
import cv2
import depthai as dai
import numpy as np
import threading
from flask import Response, Flask, render_template, send_from_directory
import os 

from recognize_pose import recognizePose, getNeckPosition, isSitted
from detect_object import detectObjects, Position
from spatial_calculator import computePosition
from distance import computeDistance, computeDistance2D, isStable
from fps import FPSHandler
import draw
import pipeline
from status import Status
from args import parseArgs
from stack import Stack, isClose
from recorder import Recorder

args = parseArgs()

detectedObjects = []
personChestPosition = None
personChestPositionStack = Stack()
realLifeChestPositionStack = Stack()

personPosition = None
status = Status()
globalFrame = None
stack = Stack()

def middle(v1, v2):
	return int((v1+v2)/2)

def calibratePositions():
		global detectedObjects
		for object in detectedObjects:
				if (object.label == 'sofa'):
						(x, y) = object.boundingBox.topLeft
						(width, height) = object.boundingBox.size
						position1 = Position()
						position1.image = (middle(x, x + width / 2), middle(y, y + height * 0.66))
						position2 = Position() 
						position2.image = (middle(x + width / 2, x + width), middle(y, y + height * 0.66))
						object.positions = [position1, position2]
				# elif object.label == 'chair':
				# 		(x, y) = object.boundingBox.topLeft
				# 		(width, height) = object.boundingBox.size
				# 		position = Position()
				# 		position.image = (int(x + width / 2), int(y + height / 2))
				# 		object.positions = [position]

cap = None

if args.video:
		cap = cv2.VideoCapture(str(Path(args.video).resolve().absolute()))
		fps = FPSHandler(cap)
else:
		fps = FPSHandler()

def shouldRun():
		return cap.isOpened() if args.video else True

positioningObjectIndex = 0 
positioningPositionIndex = -1

def updateNextIndexes():
		global detectedObjects, positioningObjectIndex, positioningPositionIndex
		
		if (positioningObjectIndex >=  len(detectedObjects)):
				return

		if (positioningPositionIndex + 1 < len(detectedObjects[positioningObjectIndex].positions)):
				positioningPositionIndex += 1
		else:
			positioningObjectIndex += 1 
			positioningPositionIndex = -1
			updateNextIndexes()

def sendPositionRequest(depthQueue, spatialCalcConfigInQueue, position, frame):
		depthFrame = depthQueue.get().getFrame()
		height, width = frame.shape[:2]
		depthHeight, depthWidth = depthFrame.shape[:2]

		(x, y) = position
		correctedX = int(x * depthWidth / width)
		correctedY = int(y * depthHeight / height)

		topLeft = dai.Point2f(correctedX - 3, correctedY - 3)
		bottomRight = dai.Point2f(correctedX + 3, correctedY + 3)

		regionOfInterest = dai.SpatialLocationCalculatorConfigData()
		regionOfInterest.depthThresholds.lowerThreshold = 100
		regionOfInterest.depthThresholds.upperThreshold = 10000
		regionOfInterest.roi = dai.Rect(topLeft, bottomRight)

		config = dai.SpatialLocationCalculatorConfig()
		config.addROI(regionOfInterest)
		spatialCalcConfigInQueue.send(config)

dirname = os.path.dirname(__file__)
filename = os.path.join(dirname, '../video.avi')
recorder = Recorder(filename)

def compute_image():

		keypoints_list = None
		detected_keypoints = None
		personwiseKeypoints = None
		detections = []

		global fps, cap, globalFrame, detectedObjects, positioningObjectIndex, positioningPositionIndex, personChestPosition, personPosition, lastPosition, recorder

		# Pipeline is defined, now we can connect to the device
		with dai.Device(pipeline.create_pipeline(args.video)) as device:

				if args.video:				
						(poseIn, objectDetectorIn) = pipeline.getVideoInputs(device)

				(cam_out, objectDetection, pose_nn, spatialCalcQueue, depthQueue) = pipeline.getOutputs(device)
				(spatialCalcConfigInQueue) = pipeline.getInputs(device)

				while shouldRun():
						frame = None
						if args.video:
								(readCorrectly, frame) = cap.read()
								if not readCorrectly:
										break
								pipeline.setVideoInputs(frame, poseIn, objectDetectorIn)
						else:
								frame = cam_out.get().getCvFrame()

						frame = frame.copy() # TODO see if useful

						fps.next_iter()

						try:
								rawPose = pose_nn.get() # tryGet doesn't work
						except RuntimeError: 
								print(RuntimeError)		
								continue

						fps.tick('nn')
				
						detected_keypoints, keypoints_list, personwiseKeypoints = recognizePose(rawPose)
						objects = detectObjects(frame, objectDetection)
						for object in objects: 
								if object.label == 'human':
										personPosition = object.boundingBox.topLeft

						if status.get() == Status.SCAN:
								detectedObjects = objects
								personChestPositionStack.reinitialize()
						elif status.get() == Status.CALIBRATION:
								calibratePositions()
								positioningObjectIndex = 0 
								positioningPositionIndex = -1
								updateNextIndexes()
								if positioningPositionIndex >= 0 and positioningObjectIndex < len(detectedObjects) and positioningPositionIndex < len(detectedObjects[positioningObjectIndex].positions):
										position = detectedObjects[positioningObjectIndex].positions[positioningPositionIndex]
										sendPositionRequest(depthQueue, spatialCalcConfigInQueue, position.image, frame)
										status.set(Status.POSITIONING)
						elif status.get() == Status.POSITIONING:
								position = computePosition(frame, spatialCalcQueue)
								if stack.isStable(position):
										detectedObjects[positioningObjectIndex].positions[positioningPositionIndex].realLife = position
										stack.reinitialize()
										updateNextIndexes()
										if positioningPositionIndex >= 0 and positioningObjectIndex < len(detectedObjects) and positioningPositionIndex < len(detectedObjects[positioningObjectIndex].positions):
												position = detectedObjects[positioningObjectIndex].positions[positioningPositionIndex]
												sendPositionRequest(depthQueue, spatialCalcConfigInQueue, position.image, frame)
										else:
												status.set(Status.ACTIVE)
								else:
									print('is not stable')
						elif status.get() == Status.ACTIVE:
								newChestPosition = getNeckPosition(detected_keypoints, frame)
								if newChestPosition != None:
										if personChestPosition == None:
												personChestPosition = Position()
												personChestPosition.image = newChestPosition
										else:
												if isClose(newChestPosition, personChestPosition.image):
														personChestPosition.image = newChestPosition
												else:
														if personChestPositionStack.isStable(newChestPosition, 0):
																personChestPosition.image = newChestPosition
										personChestPositionStack.add(newChestPosition)

								if personChestPosition != None:
										sendPositionRequest(depthQueue, spatialCalcConfigInQueue, personChestPosition.image, frame)

										position = computePosition(frame, spatialCalcQueue)
										if realLifeChestPositionStack.isStable(position):
												personChestPosition.realLife = position

						humanStatus = 'SITTING' if isSitted(keypoints_list, personwiseKeypoints, frame) else 'STANDING'
						isValid = False
						closestObject = None 
						closestObjectPosition = None
						shortestDistance = 100000

						if personPosition != None:
								if personChestPosition != None and personChestPosition.realLife != None:
										for object in detectedObjects:
												if object.label == 'sofa':
														for position in object.positions:
																if position.realLife != None:
																		distance = computeDistance(personChestPosition.realLife, position.realLife)
																		if (distance < shortestDistance):
																				closestObject = object 
																				shortestDistance = distance
																				closestObjectPosition = position
										isValid = shortestDistance < 120
										positionStatus =  ''
										if closestObject != None:
											distance = str(int(shortestDistance))+'cm'
											if isValid:
												positionStatus = ' ON SOFA ('+distance+')'
											else:
												positionStatus = ' NOT ON SOFA ('+distance+')'
										humanStatus = humanStatus + positionStatus

						(image, d) = draw.init(frame)

						if isValid:
								draw.drawLink(d, personChestPosition.image, closestObjectPosition.image)
																														
						draw.drawSkeleton(frame, d, keypoints_list, detected_keypoints, personwiseKeypoints)

						if status.get() == Status.SCAN:
								draw.drawObjectBoundingBoxes(d, detectedObjects)
			
						for object in detectedObjects:
								for position in object.positions:
										draw.drawDiamond(d, position.image)
										labelPosition = ( position.image[0],  position.image[1] - 20)
										if position.realLife == None:
												draw.drawLabel(d, labelPosition, object.label, 15)
										else:
												draw.drawObject(d, labelPosition, object.label, position.realLife, 15)

						if personPosition != None and status.get() != Status.SCAN:
								if personChestPosition == None:
										draw.drawLabel(d, personPosition, 'HUMAN', 15)
								elif personChestPosition != None and personChestPosition.realLife != None: 
										draw.drawObjectWithStatus(d, personPosition, 'Human', personChestPosition.realLife, humanStatus, isValid, 15)
										draw.drawDiamond(d, personChestPosition.image)

						draw.drawStatus(frame, d, status.label())


						globalFrame = draw.convert(image)

						if recorder.isRecording:
							recorder.record(globalFrame)

						if not args.remote:
								cv2.imshow("RGB", globalFrame)    

								key = cv2.waitKey(1) & 0xFF

								if key == ord("c"):
									status.toggleCalibration()
								elif key == ord("q"):
									break			




if not args.remote:
		compute_image()
else:
		lock = threading.Lock()
		app = Flask(__name__, static_url_path='')

		@app.route("/")
		def index():
			# return the rendered template
			return render_template("index.html")

		@app.route("/assets/<path:path>")
		def assets(path):
			return send_from_directory('assets', path)

		@app.route("/currentStatus")
		def currentStatus():
			global status
			return Response('{"status": "'+status.get()+'"}', status=200, mimetype='application/json')

		@app.route("/calibrate", methods=['POST'])
		def calibrate():
			global status
			status.toggleScan()
			# return the response generated along with the specific media
			# type (mime type)
			return Response('{"status": "'+status.get()+'"}', status=200, mimetype='application/json')

		@app.route("/isRecording")
		def isRecording():
			global recorder
			recordingStatus = "true" if recorder.isRecording else "false"
			return Response('{"recording": '+recordingStatus+'}', status=200, mimetype='application/json')

		@app.route("/record", methods=['POST'])
		def record():
			global recorder
			if recorder.isRecording:
				recorder.stop()
			else:
				recorder.start()
			recordingStatus = "true" if recorder.isRecording else "false"
			return Response('{"recording": '+recordingStatus+'}', status=200, mimetype='application/json')

		def generate():
			# grab global references to the output frame and lock variables
			global globalFrame, lock
			# loop over frames from the output stream
			while True:
				# wait until the lock is acquired
				with lock:
					# check if the output frame is available, otherwise skip
					# the iteration of the loop
					if globalFrame is None:
						continue
					# encode the frame in JPEG format
					(flag, encodedImage) = cv2.imencode(".jpg", globalFrame)
					# ensure the frame was successfully encoded
					if not flag:
						continue
				# yield the output frame in the byte format
				yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + 
					bytearray(encodedImage) + b'\r\n')

		@app.route("/video_feed")
		def video_feed():
			# return the response generated along with the specific media
			# type (mime type)
			return Response(generate(),
				mimetype = "multipart/x-mixed-replace; boundary=frame")


		t = threading.Thread(target=compute_image)
		t.daemon = True
		t.start()

		# start the flask app
		app.run(host=args.host, port=args.port, debug=True, threaded=True, use_reloader=False)
