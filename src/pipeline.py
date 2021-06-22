import cv2
import numpy as np 
import depthai as dai
from pathlib import Path

import recognize_pose
import detect_object

def getPath(basename):
    return str((Path(__file__).parent / Path('../models/' + basename)).resolve().absolute())

def to_planar(arr: np.ndarray, shape: tuple) -> list:
		return cv2.resize(arr, shape).transpose(2,0,1).flatten()

POSE_NN_OUT = 'pose_nn_out'
CAMERA_OUT = 'camera_out'
OBJECT_DETECTION_OUT = 'object_detection_out'
SPATIAL_CALCULATOR_OUT = 'spatial_calculator_out'
SPATIAL_CALCULATOR_CONFIG_IN = 'spatial_calculator_config_in'
DEPTH_OUT = 'depth_out'

POSE_NN_IN = 'pose_nn_in'
OBJECT_DETECTION_IN = 'object_detection_in'


def create_pipeline(useVideo):
		print("Creating pipeline...")
		pipeline = dai.Pipeline()

		print("Creating Human Pose Estimation Neural Network...")
		poseNeuralNetwork = pipeline.createNeuralNetwork()
		if useVideo:
				poseNeuralNetwork.setBlobPath(getPath("human-pose-estimation-0001_openvino_2021.2_8shave.blob"))
		else:
				poseNeuralNetwork.setBlobPath(getPath("human-pose-estimation-0001_openvino_2021.2_6shave.blob"))
		poseNeuralNetwork.setNumInferenceThreads(2) # Increase threads for detection
		poseNeuralNetwork.input.setQueueSize(1)
		poseNeuralNetwork.input.setBlocking(False)

		poseNeuralNetworkOut = pipeline.createXLinkOut()
		poseNeuralNetworkOut.setStreamName(POSE_NN_OUT)
		poseNeuralNetwork.out.link(poseNeuralNetworkOut.input)
		
		if useVideo:
				print("Creating Mocked Camera...")
				mockedCam = pipeline.createXLinkIn()
				mockedCam.setStreamName(POSE_NN_IN)
				mockedCam.out.link(poseNeuralNetwork.input)
		else:
				print("Creating Color Camera...")
				cam = pipeline.createColorCamera()
				cam.setPreviewSize(recognize_pose.POSE_ROI_WIDTH, recognize_pose.POSE_ROI_HEIGHT)
				cam.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)
				cam.setInterleaved(False)
				cam.setPreviewKeepAspectRatio(False)
				cam.setBoardSocket(dai.CameraBoardSocket.RGB)

				cam_xout = pipeline.createXLinkOut()
				cam_xout.setStreamName(CAMERA_OUT)
				cam.video.link(cam_xout.input)
				cam.preview.link(poseNeuralNetwork.input)


		print("Creating Object Detector Neural Network...")
		objectDetector = pipeline.createMobileNetDetectionNetwork()
		objectDetector.setConfidenceThreshold(0.5)
		objectDetector.setBlobPath(getPath(detect_object.modelFilename))
		objectDetector.setNumInferenceThreads(2)
		objectDetector.input.setBlocking(False)
		objectDetector.input.setQueueSize(1)

		objectDetectorOut = pipeline.createXLinkOut()
		objectDetectorOut.setStreamName(OBJECT_DETECTION_OUT)
		objectDetector.out.link(objectDetectorOut.input)

		if useVideo:
				print("Creating Mocked Camera...")
				mockedCam = pipeline.createXLinkIn()
				mockedCam.setStreamName(OBJECT_DETECTION_IN)
				mockedCam.out.link(objectDetector.input)
		else:
				manip2 = pipeline.createImageManip()
				manip2.initialConfig.setResize(detect_object.OBJECT_DETECTOR_ROI_WIDTH, detect_object.OBJECT_DETECTOR_ROI_HEIGHT)
				manip2.initialConfig.setKeepAspectRatio(False)
				# The NN model expects BGR input. By default ImageManip output type would be same as input (gray in this case)
				manip2.initialConfig.setFrameType(dai.ImgFrame.Type.BGR888p)
				cam.preview.link(manip2.inputImage)
				manip2.out.link(objectDetector.input)	

		# Define a source - two mono (grayscale) cameras
		monoLeft = pipeline.createMonoCamera()
		monoRight = pipeline.createMonoCamera()
		stereo = pipeline.createStereoDepth()
		spatialLocationCalculator = pipeline.createSpatialLocationCalculator()

		xoutDepth = pipeline.createXLinkOut()
		xoutSpatialData = pipeline.createXLinkOut()
		xinSpatialCalcConfig = pipeline.createXLinkIn()

		xoutDepth.setStreamName(DEPTH_OUT)
		xoutSpatialData.setStreamName(SPATIAL_CALCULATOR_OUT)
		xinSpatialCalcConfig.setStreamName(SPATIAL_CALCULATOR_CONFIG_IN)

		# MonoCamera
		monoLeft.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
		monoLeft.setBoardSocket(dai.CameraBoardSocket.LEFT)
		monoRight.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
		monoRight.setBoardSocket(dai.CameraBoardSocket.RIGHT)

		# StereoDepth
		# stereo.setOutputDepth(True)
		# stereo.setOutputRectified(False)
		stereo.setConfidenceThreshold(255)
		stereo.setConfidenceThreshold(200)
		stereo.setRectifyEdgeFillColor(0) # Black, to better see the cutout
		stereo.setMedianFilter(median = dai.StereoDepthProperties.MedianFilter.KERNEL_7x7) # KERNEL_7x7 default
		stereo.setLeftRightCheck(False)
		stereo.setSubpixel(False)

		monoLeft.out.link(stereo.left)
		monoRight.out.link(stereo.right)

		spatialLocationCalculator = pipeline.createSpatialLocationCalculator()
		stereo.depth.link(spatialLocationCalculator.inputDepth)
		spatialLocationCalculator.passthroughDepth.link(xoutDepth.input)

		topLeft = dai.Point2f(0.4, 0.4)
		bottomRight = dai.Point2f(0.6, 0.6)

		spatialLocationCalculator.setWaitForConfigInput(False)
		config = dai.SpatialLocationCalculatorConfigData()
		config.depthThresholds.lowerThreshold = 100
		config.depthThresholds.upperThreshold = 10000
		config.roi = dai.Rect(topLeft, bottomRight)
		spatialLocationCalculator.initialConfig.addROI(config)
		spatialLocationCalculator.out.link(xoutSpatialData.input)
		xinSpatialCalcConfig.out.link(spatialLocationCalculator.inputConfig)

		return pipeline

def getOutputs(device):
	return (
		device.getOutputQueue(CAMERA_OUT, 1, False),  
		device.getOutputQueue(OBJECT_DETECTION_OUT, 1, False), 
		device.getOutputQueue(POSE_NN_OUT, 1, False),
		device.getOutputQueue(name=SPATIAL_CALCULATOR_OUT, maxSize=4, blocking=False),
		device.getOutputQueue(name=DEPTH_OUT, maxSize=4, blocking=False)
	)

def getInputs(device):
	return (
		device.getInputQueue(SPATIAL_CALCULATOR_CONFIG_IN)
	)

def getVideoInputs(device):
	return (
			device.getInputQueue(POSE_NN_IN),
			device.getInputQueue(OBJECT_DETECTION_IN)
	)

def setVideoInputs(frame, poseIn, objectDetectorIn):
	nn_data = dai.NNData()
	nn_data.setLayer("input", to_planar(frame, (detect_object.OBJECT_DETECTOR_ROI_WIDTH, detect_object.OBJECT_DETECTOR_ROI_HEIGHT)))
	objectDetectorIn.send(nn_data)

	pose_nn_data = dai.NNData()
	pose_nn_data.setLayer("input", to_planar(frame, (recognize_pose.POSE_ROI_WIDTH, recognize_pose.POSE_ROI_HEIGHT)))
	poseIn.send(pose_nn_data)