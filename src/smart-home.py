import argparse
import threading
import time
import cv2
import depthai as dai
import numpy as np
import threading
from flask import Response, Flask, render_template, send_from_directory

from recognize_pose import recognizePose
from detect_object import detectObjects
from spatial_calculator import computePosition
from get_path import getPath
from distance import computeDistance
from fps import FPSHandler
import draw
import pipeline
from status import Status
from args import parseArgs

args = parseArgs()

detectedObjects = []
status = Status()
globalFrame = None

# def calibratePositions(objects):
# 		global objectPositions
# 		objectPositions = []
# 		if status != "calibrating":
# 				return
# 		for object in objects:
# 				if (object.label == 'sofa' or object.label == 'chair'):
# 						detectedObjects.append(object)

cap = None

if args.video:
		cap = cv2.VideoCapture(str(Path(args.video).resolve().absolute()))
		fps = FPSHandler(cap)
else:
		fps = FPSHandler()

def shouldRun():
		return cap.isOpened() if args.video else True

def compute_image():

		keypoints_list = None
		detected_keypoints = None
		personwiseKeypoints = None
		detections = []

		global fps, cap, globalFrame

		# Pipeline is defined, now we can connect to the device
		with dai.Device(pipeline.create_pipeline(args.video)) as device:

				if args.video:				
						(poseIn, objectDetectorIn) = pipeline.getVideoInputs(device)

				(cam_out, objectDetection, pose_nn, spatialCalcQueue) = pipeline.getOutputs(device)
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
						detectedObjects = detectObjects(frame, objectDetection)
						positions = computePosition(frame, spatialCalcQueue)

				


						# if newPosition or isCalibrating:
						# 		config = dai.SpatialLocationCalculatorConfigData()
						# 		config.depthThresholds.lowerThreshold = 100
						# 		config.depthThresholds.upperThreshold = 10000

						# 		height, width = frame.shape[:2]
						# 		depthHeight, depthWidth = depthFrame.shape[:2]
						# 		if isCalibrating and sofaBoundingBox is not None: 
						# 				(x, y) = sofaCenterPosition
						# 		elif humanChestPosition is not None :
						# 				x = humanChestPosition[0]
						# 				y = humanChestPosition[1]
						# 		else:
						# 				x = 100
						# 				y = 100

						# 		correctedX = int(x * depthWidth / width)
						# 		correctedY = int(y * depthHeight / height)

						# 		topLeft = dai.Point2f(correctedX - 3, correctedY - 3)
						# 		bottomRight = dai.Point2f(correctedX + 3, correctedY + 3)

						# 		config.roi = dai.Rect(topLeft, bottomRight)
						# 		cfg = dai.SpatialLocationCalculatorConfig()
						# 		cfg.addROI(config)
						# 		spatialCalcConfigInQueue.send(cfg)

						# if sofaCenterPosition is not None:
						# 		cv2.circle(frame, sofaCenterPosition, 10, WHITE, -1, cv2.LINE_AA)
						# 		(xmin,ymin) = sofaCenterPosition
						# 		cv2.putText(frame, f"X: {sofaCenterPositionInRealWorld[0]} cm", (xmin + 10, ymin + 20), cv2.FONT_HERSHEY_TRIPLEX, 0.5, WHITE)
						# 		cv2.putText(frame, f"Y: {sofaCenterPositionInRealWorld[1]} cm", (xmin + 10, ymin + 35), cv2.FONT_HERSHEY_TRIPLEX, 0.5, WHITE)
						# 		cv2.putText(frame, f"Z: {sofaCenterPositionInRealWorld[2]} cm", (xmin + 10, ymin + 50), cv2.FONT_HERSHEY_TRIPLEX, 0.5, WHITE)

						# 		if humanChestPosition is not None:

						# 				distance = int(computeDistance(humanChestPositionInRealWorld, sofaCenterPositionInRealWorld))
						# 				cv2.putText(frame, f"Distance: {distance} cm", (xmin + 10, ymin + 65), cv2.FONT_HERSHEY_TRIPLEX, 0.5, WHITE)

						# 				color = RED if distance > 150 else GREEN
									
						# 				cv2.line(frame, humanChestPosition, sofaCenterPosition, color, 5, cv2.LINE_AA)


						(image, d) = draw.init(frame)


						draw.drawObjectBoundingBoxes(d, detectedObjects)
						draw.drawSkeleton(frame, d, keypoints_list, detected_keypoints, personwiseKeypoints)

						draw.drawStatus(frame, d, status.label())


						globalFrame = draw.convert(image)

						if not args.remote:
								cv2.imshow("RGB", globalFrame)    

								key = cv2.waitKey(1) & 0xFF

								if key == ord("c"):
									status.set(Status.CALIBRATION)
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
