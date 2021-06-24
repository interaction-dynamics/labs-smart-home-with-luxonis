import cv2

class Recorder:

	def __init__(self, filename):
		self.frames = []
		self.isRecording = False
		self.filename = filename

	def start(self):
		self.isRecording = True

	def record(self, frame):
		self.frames.append(frame)

	def stop(self):
		self.isRecording = False
		if len(self.frames) > 0:
			(height, width) = self.frames[0].shape[:2]

			video = cv2.VideoWriter(self.filename, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'), 10, (width, height))

			for frame in self.frames: 
				video.write(frame)

			video.release()
			print("Video saved in ", self.filename)
		self.frames = []
