import pygame as pg

import UI

class PhotoScene:
    def __init__(self, app):
        self.app = app
        self.photo_info_UI = UI.Label((5, 5), self.app.font_small, "camera not started!", (255, 255, 255), outline=True)
        self.photo_mode = 'default'

    def render(self):
        if self.app.camera:
            self.app.camera_surface = self.app.camera.get_surface()

        else:
            self.app.display.fill((0, 0, 0))

        if self.app.camera_surface:
            if self.app.camera_surface.resolution != self.app.resolution:
                self.app.display.blit(pg.transform.scale(self.app.camera_surface, self.app.resolution), (0, 0))
            
            else:
                self.app.display.blit(self.app.camera_surface, (0, 0))
        
        self.photo_info_UI.render(self.app.display)
        # app.device_info_UI.render(app.display)

    def initialize_camera(self, camera):
        try:
            self.camera = camera.Camera()
            self.camera.start()
            self.update_photo_info()

        except Exception as e:
            print("failed to start camera: " + str(e))
    
    def set(self):
        self.initialize_camera(self.app.camera)
        self.app.scene = 'photo'

    def update_photo_info(self):
        self.photo_info[self.photo_mode] = {
            "expo" : f"{self.camera.resolution[0]}x{self.camera.resolution[1]}",
            "sat": self.camera.saturation,
            "sharpness": self.camera.sharpness,
            "gain": f"{self.camera.gain}"
        }
        self.photo_info_UI.set("\n".join([f"{key}: {value}" for key, value in self.photo_info[self.photo_mode].items() if key in self.show_photo_info]))