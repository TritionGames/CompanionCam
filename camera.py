import pygame as pg
import os
import numpy as np
import time

from picamera2 import Picamera2
from picamera2.encoders import H264Encoder

class Camera:
 def __init__(self):
  self.fps = 60
  self.sharpness = 5
  self.contrast = 1.2
  self.resolution = (320, 240)
  self.saturation = 0.8
  self.gain = 4
  self.picam2 = Picamera2()
  video_config = self.picam2.create_video_configuration(main={"size": self.resolution}, buffer_count = 3)
  self.picam2.configure(video_config)
  self.picam2.set_controls({"FrameRate": self.fps,
           "Sharpness": self.sharpness,
           "Contrast": self.contrast,
           'Saturation': self.saturation,
           "ColourGains": (2.5, 2),
           "AeEnable": True,
           "AnalogueGain": self.gain})

  self.encoder = H264Encoder(10000000)

  self.recording = False
  self.active = False

 def take_photo(self):
  self.picam2.capture_file(f"saved/IMG_{str(time.time()).replace('.', '_')}.png")

 def start_video(self):
  self.start_recording = True
  self.picam2.start_recording(self.encoder, "temp.h264")

 def end_video(self):
  self.picam2.stop_recording()
  self.recording = False

  if state := os.system(f"ffmpeg -r {self.fps} -i temp.h264 -c:v copy -r {self.fps} MP4_{time.time()}.mp4"):
   print(f"ffmpeg failed to compile ({state})")

 def get_surface(self):
  if not self.active:
   print("WARNING: camera not active")
   return None

  r = self.picam2.capture_request()
  array = r.make_array("main")
  array = np.ascontiguousarray(array[:,:,:3])

  width, height = array.shape[1], array.shape[0]

  s = pg.image.fromstring(array.tobytes(), (width, height), "RGB")

  r.release()

  return s

 def start(self):
  self.picam2.start()
  self.active = True

 def close(self):
  self.picam2.close()
  self.active = False