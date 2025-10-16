import time
import os
import threading
from datetime import date, datetime

import pydub
import pygame as pg

import UI
import utils
import photoScene
import savedScene
import iconManager
# import camera

class App:
    def __init__(self):
        pg.init()

        self.resolution = (640, 480)
        self.display = pg.display.set_mode(self.resolution)
        pg.display.set_caption("companioncam")

        self.settings = utils.load_json("settings.json")
        self.running = True
        self.clock = pg.time.Clock()
        self.listen_clock = pg.time.Clock()

        self.load_fonts()

        self.request_update = False
        self.variable_fps = 60

        self.background = pg.image.load("background.png").convert()

        self.start_up_screen()

        self.load_assets()

        self.photo_info = {
            "default": {"gain": "1",
            "sat": "x1.25",
            "sharpness": "1",
            "res": "640x480"}
        }

        self.video_info = {
            "default": {"gain": "1",
            "sat": "x1.25",
            "sharpness": "1",
            "res": "640x480",
            "fps": 60}
        }

        self.video_mode = "default"
        self.show_photo_info = ["gain", "sat", "res", "sharpness"]
        self.show_video_info = ["gain", "sat", "res", "sharpness", "fps"]

        self.photo_scene = photoScene.PhotoScene(self)
        self.saved_scene = savedScene.SavedScene(self)

        self.icons = iconManager.Icons(self)

        self.initialize_main_ui()

        time.sleep(0.3)
        self.should_update = True

        self.camera_surface = pg.Surface((640, 480))
        self.scene = "main"

        self.camera = None
        self.camera_surface = None

        # self.popup = UI.PopUp(self.font, self.font_smaller, "set resolution:", ['1920x1080', '640x480'])
        self.pop_ups = None

    def load_assets(self):
        self.video_overlay = pg.image.load("video_overlay.png").convert_alpha()

    def initialize_main_ui(self):
        self.ui = UI.Frame(2, 2, (420, 420))
        self.ui.place(UI.Button(self.video_scene, "Video"), (1,  0))
        self.ui.place(UI.Button(self.photo_scene.set, "Photo"), (0, 0))
        self.ui.place(UI.Button(self.saved_scene.set, "Saved"), (0, 1))
        self.ui.place(UI.Button(self.options_scene, "Options"), (1, 1))

        self.formatted_date = date.today().strftime("%d/%m/%y")

        self.bottom_shape = UI.Shape((5, 420), (630, 55))
        self.battery_level_UI = UI.Label((0, 0), self.font_small_bold, f"CHARGE: 100    WELCOME HOME! xD", (255, 255, 255))
        self.bottom_shape.place(self.battery_level_UI, (15, 20))

        self.device_info_UI = UI.Label([self.resolution[0], 5], self.font_small, "BAT: ?", (255, 255, 255))
        self.device_info_UI.pos[0] -= self.device_info_UI.text.get_width() + 5

        self.about_shape_UI = UI.Shape((425, 5), (210, 410))
        self.about_shape_UI.place(UI.Label((0, 0), self.font_tiny, utils.load_file("about.txt"), (255, 255, 255)), (5, 5))

        self.video_info_UI = UI.Label((5, 5), self.font_small, "camera not started!", (255, 255, 255), outline=True)

    def list_files(self):
        return utils.list_dir(self.settings['folder'])

    def video_scene(self):
        self.scene = 'video'
        self.update_video_info()

    def update_video_info(self):
        # self.video_info[self.video_mode] = {
        #     "expo" : f"{self.camera.resolution[0]}x{self.camera.resolution[1]}",
        #     "sat": self.camera.saturation,
        #     "sharpness": self.camera.sharpness,
        #     "gain": f"{self.camera.gain}",
        #     "fps": 60
        # }
        self.video_info_UI.set("\n".join([f"{key}: {value}" for key, value in self.video_info[self.video_mode].items() if key in self.show_video_info]))

    def options_scene(self):
        self.scene = "options"

    def start_up_screen(self):
        self.display.blit(self.background, (0, 0))
        self.display.blit(self.font.render("CompanionCam!", False, (255, 255, 255)), (5, 5))
        self.display.blit(self.font_small_bold.render("loading...", False, (255, 255, 255)), (5, 45))

        pg.display.update()

    def load_fonts(self):
        self.font = pg.font.Font('F25_Bank_Printer.ttf', 40)
        self.font_bold = pg.font.Font('F25_Bank_Printer_Bold.ttf', 40)
        self.font_medium = pg.font.Font('F25_Bank_Printer.ttf', 30)
        self.font_small_bold = pg.font.Font('F25_Bank_Printer_Bold.ttf', 20)
        self.font_small = pg.font.Font('F25_Bank_Printer_Bold.ttf', 20)
        self.font_tiny = pg.font.Font('F25_Bank_Printer_Bold.ttf', 16)
        self.font_smaller = pg.font.Font('F25_Bank_Printer_Bold.ttf', 18)

    def close_camera(self):
        if self.camera:
            self.camera.close()

    def back(self):
        if self.scene == "photo":
            self.scene = "main"
            self.close_camera()

        elif self.scene == "saved":
            self.saved_scene.leave()

        else:
            self.scene = "main"

    #https://www.pygame.org/pcr/transform_scale/index.php
    def aspect_scale(self, img, size):
        bx, by = size
        ix,iy = img.get_size()
        if ix > iy:
            # fit to width
            scale_factor = bx/float(ix)
            sy = scale_factor * iy
            if sy > by:
                scale_factor = by/float(iy)
                sx = scale_factor * ix
                sy = by
            else:
                sx = bx
        else:
            # fit to height
            scale_factor = by/float(iy)
            sx = scale_factor * ix
            if sx > bx:
                scale_factor = bx/float(ix)
                sx = bx
                sy = scale_factor * iy
            else:
                sy = by

        return pg.transform.smoothscale(img, (sx,sy)), (sx, sy)

    def run(self):
        while self.running:
            self.clock.tick(self.variable_fps)

            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.running = False

                if event.type == pg.KEYDOWN:
                    if self.pop_ups:           
                        if event.key == pg.K_s:
                            self.pop_ups.move_down()
                        if event.key == pg.K_w:
                            self.pop_ups.move_up()
                        if event.key == pg.K_SPACE:
                            self.pop_ups.call(self)

                    else:         
                        if self.scene == 'photo':
                            if event.key == pg.K_SPACE:
                                self.camera.take_photo()

                        if self.scene == 'main':
                            if event.key == pg.K_w:
                                self.ui.move(0)

                            if event.key == pg.K_d:
                                self.ui.move(1)

                            if event.key == pg.K_s:
                                self.ui.move(2)
                            
                            if event.key == pg.K_a:
                                self.ui.move(3)

                            if event.key == pg.K_SPACE:
                                self.ui.call_button()

                        elif self.scene == "saved":
                            if event.key == pg.K_SPACE and not self.saved_scene.selected:
                                self.saved_scene.show_selection()

                            elif event.key == pg.K_SPACE and self.saved_scene.video:
                                self.saved_scene.toggle_pause()
                            
                            if event.key == pg.K_RIGHT:
                                self.saved_scene.skip_forward()

                            if event.key == pg.K_LEFT:
                                self.saved_scene.go_back()

                            self.saved_scene.move_selection(event.key)

                        if event.key == pg.K_ESCAPE:
                            self.back()

                    self.should_update = True

            if self.scene == "photo":
                self.should_update = True
            
            if not self.should_update:
                continue
            
            self.should_update = False

            if self.pop_ups:
                self.pop_ups.render(self.display)

            if self.scene == "main":
                self.display.blit(self.background, (0, 0))
                self.bottom_shape.render(self.display)
                self.about_shape_UI.render(self.display)
                self.ui.render(self.display, self.font_medium, self.font_bold)

            elif self.scene == "photo":
                self.photo_scene.render()

            elif self.scene == "saved":
                self.saved_scene.render()

            elif self.scene == "video":
                self.display.fill((0, 0, 0))
                self.video_info_UI.render(self.display)

            elif self.scene == "options":
                self.display.blit(self.background, (0, 0))

            pg.display.update()

    def start(self):
        self.run()

if __name__ == "__main__":
    App().start()
