import pygame as pg
import os
import numpy as np
import time

import utils

from picamera2 import Picamera2
from picamera2.encoders import H264Encoder

class Camera:
 def __init__(self, app):
  self.app = app
  self.camera_settings = self.app.settings["camera settings"]
  self.picam2 = Picamera2()
  video_config = self.picam2.create_video_configuration(main={"size": self.camera_settings['resolution']}, buffer_count = 4)
  self.picam2.configure(video_config)

  self.camera_settings = utils.load_json("settings.json")["camera settings"]
  self.picam2.set_controls({"FrameRate": self.camera_settings['fps'],
           "Sharpness": self.camera_settings['sharpness'],
           "Contrast": self.camera_settings['contrast'],
           'Saturation': self.camera_settings['saturation'],
           "ColourGains": self.camera_settings['color gains'],
           "AeEnable": True,
           "AnalogueGain": self.camera_settings['gain']})

  self.encoder = H264Encoder(self.camera_settings['bitrate'])

  self.recording = False
  self.active = False

 def take_photo(self):
  self.picam2.capture_file(f"saved/IMG_{str(time.time()).replace('.', '_')}.png")

 def start_video(self):
  self.recording = True
  self.app.video_scene.began_recording = time.time()
  self.picam2.start_encoder(self.encoder, "temp.h264")

 def end_video(self):
  self.picam2.stop_encoder()
  self.recording = False
  fps = self.camera_settings["fps"]

  if state := os.system(f"ffmpeg -r {fps} -i temp.h264 -c:v copy -r {fps} saved/MP4_{str(time.time()).replace('.', '_')}.mp4"):
   print(f"ffmpeg failed to compile ({state})")

 def toggle_video(self):
  if not self.recording:
    self.start_video()
  else:
    self.end_video()

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
