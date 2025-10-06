import time
import os
import threading
from datetime import date, datetime

import pygame as pg

import UI
import utils
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

        self.viewer_scroll = 0

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

        self.file_info = {
            "size": True,
            "date": True,
            "resolution": True}

        self.thumbnails = []
        self.video_mode = "default"
        self.photo_mode = "default"
        self.show_photo_info = ["gain", "sat", "res", "sharpness"]
        self.show_video_info = ["gain", "sat", "res", "sharpness", "fps"]

        self.thumbnail_size = min(self.settings['thumbnail size'][0], 100), min(self.settings['thumbnail size'][1], 100)
        self.thumbnail_x = 610 // self.thumbnail_size[0] - 1
        self.gap_size = 610 - (self.thumbnail_x * self.thumbnail_size[0]) - (10 * self.thumbnail_x)

        self.initialize_main_ui()
        self.initialize_saved_ui()

        time.sleep(0.3)
        self.should_update = True

        self.camera_surface = pg.Surface((640, 480))
        self.scene = "main"

        self.selected_photo_id = 0
        self.selected_photo: pg.Surface = None
        self.selected_file: str = ""

        self.cached_files = self.list_files()

        self.camera = None
        self.camera_surface = None

        # self.popup = UI.PopUp(self.font, self.font_smaller, "set resolution:", ['1920x1080', '640x480'])
        self.pop_ups = None

    def initialize_main_ui(self):
        self.ui = UI.Frame(2, 2, (420, 420))
        self.ui.place(UI.Button(self.video_scene, "Video"), (1,  0))
        self.ui.place(UI.Button(self.photo_scene, "Photo"), (0, 0))
        self.ui.place(UI.Button(self.saved_scene, "Saved"), (0, 1))
        self.ui.place(UI.Button(self.options_scene, "Options"), (1, 1))

        self.formatted_date = date.today().strftime("%d/%m/%y")

        self.bottom_shape = UI.Shape((5, 420), (630, 55))
        self.battery_level_UI = UI.Label((0, 0), self.font_small_bold, f"CHARGE: 100    WELCOME HOME! xD", (255, 255, 255))
        self.bottom_shape.place(self.battery_level_UI, (15, 20))

        self.photo_info_UI = UI.Label((5, 5), self.font_small, "", (255, 255, 255))
        self.device_info_UI = UI.Label([self.resolution[0], 5], self.font_small, "BAT: ?", (255, 255, 255))
        self.device_info_UI.pos[0] -= self.device_info_UI.text.get_width() + 5

        self.about_shape_UI = UI.Shape((425, 5), (210, 410))
        self.about_shape_UI.place(UI.Label((0, 0), self.font_tiny, utils.load_file("about.txt"), (255, 255, 255)), (5, 5))

        self.photo_info_UI = UI.Label((5, 5), self.font_small, "camera not started!", (255, 255, 255), outline=True)
        self.video_info_UI = UI.Label((5, 5), self.font_small, "camera not started!", (255, 255, 255), outline=True)

    def list_files(self):
        return utils.list_dir(self.settings['folder'])

    def initialize_saved_ui(self):
        self.saved_shape = UI.Shape((5, 5), (630, 470))

    def initialize_video_ui(self):
        pass
    
    def generate_thumbnails(self, start = 0):
        self.thumbnails = []
        path = self.settings['folder']
        files = self.list_files()

        end_index = (4) * self.thumbnail_x

        for file in files[start:end_index]:
            self.thumbnails.append(self.get_thumbnail(file))
            self.should_update = True

    def get_thumbnail(self, file):
        filename, filetype = file.split('.')

        exact_path = os.path.join(self.settings['folder'], file)

        surface = pg.Surface(self.thumbnail_size)
        surface.blit(pg.transform.scale(pg.image.load(exact_path), self.thumbnail_size), (0, 0))

        surface.blit(self.font_tiny.render("."+filetype, True, (0, 0, 0)), (2, self.thumbnail_size[1] - 17))
        surface.blit(self.font_tiny.render("."+filetype, True, (255, 255, 255)), (4, self.thumbnail_size[1] - 15))

        return surface, exact_path

    def scroll_thumbnails(self, down: bool):
        if down:
            self.viewer_scroll += 1
            self.thumbnails = self.thumbnails[self.thumbnail_x:]
            for file in (self.cached_files[(self.viewer_scroll+3)*self.thumbnail_x:(self.viewer_scroll+4)*self.thumbnail_x]):
                self.thumbnails.append(self.get_thumbnail(file))

            self.selected_photo_id -= self.thumbnail_x

        else:
            self.viewer_scroll -= 1
            self.thumbnails = self.thumbnails[:(self.viewer_scroll+3)*self.thumbnail_x]

            for file in reversed(self.cached_files[self.viewer_scroll*self.thumbnail_x:(self.viewer_scroll+1)*self.thumbnail_x]):
                self.thumbnails.insert(0, self.get_thumbnail(file))
            self.thumbnails = self.thumbnails[:20]

            self.selected_photo_id += self.thumbnail_x

        self.should_update = True

    def video_scene(self):
        self.scene = 'video'
        self.update_video_info()
        
    def update_photo_info(self):
        self.photo_info[self.photo_mode] = {
            "expo" : f"{self.camera.resolution[0]}x{self.camera.resolution[1]}",
            "sat": self.camera.saturation,
            "sharpness": self.camera.sharpness,
            "gain": f"{self.camera.gain}"
        }
        self.photo_info_UI.set("\n".join([f"{key}: {value}" for key, value in self.photo_info[self.photo_mode].items() if key in self.show_photo_info]))

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

    def initialize_camera(self):
        try:
            self.camera = camera.Camera()
            self.camera.start()
            self.update_photo_info()

        except Exception as e:
            print("failed to start camera: " + str(e))
    
    def photo_scene(self):
        self.scene = "photo"
        self.initialize_camera()

    def saved_scene(self):
        self.scene = "saved"
        self.viewer_scroll = 0
        self.selected_photo_id = 0
        threading.Thread(target=self.generate_thumbnails).start()

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

        elif self.scene == "watch":
            self.scene = "saved"

        else:
            self.scene = "main"

    def move_selection(self, key):
        if key == pg.K_w and self.selected_photo_id >= self.thumbnail_x:
            self.selected_photo_id -= self.thumbnail_x

        if key == pg.K_d and self.selected_photo_id < len(self.thumbnails):
            self.selected_photo_id += 1

        if key == pg.K_s and self.selected_photo_id < len(self.thumbnails) - self.thumbnail_x:
            self.selected_photo_id += self.thumbnail_x

        if key == pg.K_a and self.selected_photo_id > 0:
            self.selected_photo_id -= 1

        if self.selected_photo_id // self.thumbnail_x > 2:
            self.scroll_thumbnails(True)

        if self.selected_photo_id // self.thumbnail_x < 1 and not self.viewer_scroll == 0:
            self.scroll_thumbnails(False)

        self.selected_photo_id = min(self.selected_photo_id, len(self.thumbnails)-1)

    def show_selection(self):
        self.scene = "watch"
        self.selected_photo = pg.image.load(self.selected_file)
        file_type = self.selected_file.split('.')[-1]
        creation_timestamp = os.path.getctime(self.selected_file)
        creation_time = datetime.fromtimestamp(creation_timestamp).strftime('%d %b %Y %H:%M:%S')
        size = round(os.path.getsize(self.selected_file)/1000, 2)

        string = ""
        if self.file_info["resolution"]:
            string += f"resolution: {self.selected_photo.get_width()}x{self.selected_photo.get_height()}\n"
        if self.file_info["date"]:
            string += f"date: {creation_time}\n"
        if self.file_info["size"]:
            string += f"size: {size} kb ({file_type})\n"

        self.photo_info_UI.set(string)

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

        return pg.transform.scale(img, (sx,sy)), (sx, sy)

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
                            if event.key == pg.K_SPACE:
                                self.show_selection()

                            self.move_selection(event.key)

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
                if self.camera:
                    self.camera_surface = self.camera.get_surface()

                else:
                    self.display.fill((0, 0, 0))

                if self.camera_surface:
                    if self.camera_surface.resolution != self.resolution:
                        self.display.blit(pg.transform.scale(self.camera_surface, self.resolution), (0, 0))
                    
                    else:
                        self.display.blit(self.camera_surface, (0, 0))
                
                self.photo_info_UI.render(self.display)
                self.device_info_UI.render(self.display)

            elif self.scene == "saved":
                self.display.blit(self.background, (0, 0))
                self.saved_shape.render(self.display)

                gap = (1) / self.thumbnail_x * self.gap_size

                for i, surface in enumerate(self.thumbnails):
                    fill_x = (i % self.thumbnail_x) / self.thumbnail_x * self.gap_size
                    y = 25 + (i)//self.thumbnail_x * (self.thumbnail_size[1] + gap + 10)
                    pos = (25 + fill_x + (i%self.thumbnail_x) * (self.thumbnail_size[0] + 10), y)
                    bordercolor = (25, 25, 25)

                    if i == self.selected_photo_id:
                        self.selected_file = surface[1]
                        bordercolor = (255, 0, 0)

                    pg.draw.rect(self.display, bordercolor, (pos[0] - 5, pos[1] - 5, self.thumbnail_size[0] + 10, self.thumbnail_size[1] + 10))

                    self.display.blit(surface[0], pos)

            elif self.scene == "watch":
                self.display.fill((0, 0, 0))

                surface, size = self.aspect_scale(self.selected_photo, self.resolution)
                self.display.blit(surface, (self.resolution[0] / 2 - size[0]/2, self.resolution[1] / 2 - size[1]/2))

                self.photo_info_UI.render(self.display)

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
