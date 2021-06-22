labels = {
  "calibration": "Calibrating...",
  "active": "Active",
  "scan": "Scanning objects...",
  "positioning": "Positioning...",
  "waiting_for_calibration": "Waiting for calibration..."
}

class Status:

  CALIBRATION = 'calibration'
  ACTIVE = 'active'
  SCAN = 'scan'
  POSITIONING = 'positioning'
  WAITING_FOR_CALIBRATION = 'waiting_for_calibration'

  def __init__(self):
    self.current = 'waiting_for_calibration'

  def get(self):
    return self.current 
  
  def set(self, status):
    self.current = status

  def toggleScan(self):
    if self.current == self.SCAN:
      self.current = self.CALIBRATION 
    else:
      self.current = self.SCAN

  def label(self):
    return labels[self.current]
