import pygame as pg

import UI
import utils
import time
# import camera

class VideoScene:
    def __init__(self, app):
        self.app = app
        self.video_info_UI = UI.Label((5, 5), self.app.font_small, "camera not started!", (255, 255, 255), outline=True)
        self.video_mode = 'default'
        self.video_info = {"default": {}}
        self.show_video_info = {"sat": True, "res": True, "gain": True, "sharpness": True}
        self.record_icon = app.icons.get_slice(41)
        self.record_text = UI.Label((470, 5), self.app.font_small, "recording: 0s", (255, 0, 0))
        self.recording = False
        self.crosshair = self.app.icons.get_slice(7)
        self.began_recording = 0

    def render(self):
        if self.app.camera:
            self.app.camera_surface = self.app.camera.get_surface()

        else:
            self.app.display.fill((0, 0, 0))

        if self.app.camera_surface:
            if self.app.camera_surface.get_size() != self.app.resolution:
                self.app.display.blit(pg.transform.scale(self.app.camera_surface, self.app.resolution), (0, 0))
            
            else:
                self.app.display.blit(self.app.camera_surface, (0, 0))

        self.app.display.blit(self.crosshair, (self.app.camera.camera_settings["resolution"][0]/2 - 12, self.app.camera.camera_settings["resolution"][1]/2 - 12))

        self.video_info_UI.render(self.app.display)

        self.app.should_update = True

        if (not self.app.camera) or (not self.app.camera.recording):
            return

        self.record_text.set(f"REC: {utils.format_seconds(time.time() - self.began_recording)}s")
        
        self.app.display.blit(self.record_icon, (self.app.resolution[0] - 29, 5))
        self.record_text.render(self.app.display, (self.app.resolution[0] - self.record_text.text.get_width() - 30, 5))

    def set(self):
        self.update_video_info()
        self.app.scene = 'video'
        self.app.variable_fps = self.app.camera.camera_settings["fps"]

    def update_video_info(self):
        w, h = self.app.camera.camera_settings["resolution"]
        self.video_info[self.video_mode] = {
            "res" : f"{w}x{h}",
            "sat": self.app.camera.camera_settings["saturation"],
            "sharpness": self.app.camera.camera_settings["sharpness"],
            "gain": self.app.camera.camera_settings["gain"]
        }
        self.video_info_UI.set("\n".join([f"{key}: {value}" for key, value in self.video_info[self.video_mode].items() if key in self.show_video_info]))
