import pygame as pg

import UI
import camera

class PhotoScene:
    def __init__(self, app):
        self.app = app
        self.photo_info_UI = UI.Label((5, 5), self.app.font_small, "camera not started!", (255, 255, 255), outline=True)
        self.photo_mode = 'default'
        self.photo_info = {"default": {}}
        self.show_photo_info = {"sat": True, "res": True, "gain": True, "sharpness": True}

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
        
        self.photo_info_UI.render(self.app.display)
        # app.device_info_UI.render(app.display)

    def initialize_camera(self):
        try:
            self.app.camera = camera.Camera()
            self.app.camera.start()
            self.update_photo_info()

        except Exception as e:
            print("failed to start camera: " + str(e))
    
    def set(self):
        self.initialize_camera()
        self.app.scene = 'photo'

    def update_photo_info(self):
        self.photo_info[self.photo_mode] = {
            "res" : f"{self.app.camera.resolution[0]}x{self.app.camera.resolution[1]}",
            "sat": self.app.camera.saturation,
            "sharpness": self.app.camera.sharpness,
            "gain": f"{self.app.camera.gain}"
        }
        self.photo_info_UI.set("\n".join([f"{key}: {value}" for key, value in self.photo_info[self.photo_mode].items() if key in self.show_photo_info]))
