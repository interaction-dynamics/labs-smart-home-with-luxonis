labels = {
  "calibration": "Calibrating..."
}

class Status:

  CALIBRATION = 'calibration'

  def __init__(self):
    self.current = 'calibration'

  def get(self):
    return self.current 
  
  def set(self, status):
    self.current = status

  def label(self):
    return labels[self.current]
