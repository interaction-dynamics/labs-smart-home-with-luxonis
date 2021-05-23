import time

class FPSHandler:
		def __init__(self, cap=None):
				self.timestamp = time.time()
				self.start = time.time()
				self.framerate = cap.get(cv2.CAP_PROP_FPS) if cap is not None else None

				self.frame_cnt = 0
				self.ticks = {}
				self.ticks_cnt = {}

		def next_iter(self):
				# if not args.camera:
				# 		frame_delay = 1.0 / self.framerate
				# 		delay = (self.timestamp + frame_delay) - time.time()
				# 		if delay > 0:
				# 				time.sleep(delay)
				self.timestamp = time.time()
				self.frame_cnt += 1

		def tick(self, name):
				if name in self.ticks:
						self.ticks_cnt[name] += 1
				else:
						self.ticks[name] = time.time()
						self.ticks_cnt[name] = 0

		def tick_fps(self, name):
				if name in self.ticks:
						return self.ticks_cnt[name] / (time.time() - self.ticks[name])
				else:
						return 0

		def fps(self):
				return self.frame_cnt / (self.timestamp - self.start)