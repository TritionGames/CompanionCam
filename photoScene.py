import pygame as pg

import UI
import camera
import utils

class PhotoScene:
    def __init__(self, app):
        self.app = app
        self.photo_info_UI = UI.Label((5, 5), self.app.font_small, "bug", (255, 255, 255), outline=True)
        self.photo_mode = 'default'
        self.photo_info = {"default": {}}
        self.show_photo_info = {"sat": True, "res": True, "gain": True, "sharpness": True}
        self.crosshair = self.app.icons.get_slice(7)

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
        
        self.app.display.blit(self.crosshair, (self.app.resolution[0]/2 - 12, self.app.resolution[1]/2 - 12))
        
        self.photo_info_UI.render(self.app.display)
        # app.device_info_UI.render(app.display)

    def set(self):
        self.update_photo_info()
        self.app.scene = 'photo'
        self.app.variable_fps = 30

    def update_photo_info(self):
        w, h = self.app.camera.camera_settings["resolution"]
        self.photo_info[self.photo_mode] = {
            "res" : f"{w}x{h}",
            "sat": self.app.camera.camera_settings["saturation"],
            "sharpness": self.app.camera.camera_settings["sharpness"],
            "gain": self.app.camera.camera_settings["gain"]
        }
        self.photo_info_UI.set("\n".join([f"{key}: {value}" for key, value in self.photo_info[self.photo_mode].items() if key in self.show_photo_info]))
