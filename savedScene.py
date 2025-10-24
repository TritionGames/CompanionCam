import os
import numpy as np

import pygame as pg
import threading
from multiprocessing import Process
import moviepy
import time

from datetime import datetime

import UI
import utils
import PIL

class SavedScene:
    def __init__(self, app):
        self.app = app

        self.selected_photo_id = 0
        self.selected_photo: pg.Surface = None
        self.selected_file: str = ""

        self.cached_files = self.app.list_files()

        self.saved_shape = UI.Shape((5, 5), (630, 470))

        self.file_info = {
            "size": True,
            "date": True,
            "resolution": True,
            "sharpness index": False}

        self.viewer_scroll = 0
        self.thumbnails = []
        self.thumbnail_size = min(self.app.settings['thumbnail size'][0], 100), min(self.app.settings['thumbnail size'][1], 100)
        self.thumbnail_x = 610 // self.thumbnail_size[0] - 1
        self.gap_size = 610 - (self.thumbnail_x * self.thumbnail_size[0]) - (10 * self.thumbnail_x)
        self.selected = False
        self.video = False
        self.timestamp = 0
        self.playback = 0
        self.start_playback = 0
        self.frame = 0
        self.loaded_clip = None
        self.should_play_audio = self.app.can_play_audio
        self.pawsed_timestamp = 0
        self.start_pawsed = 0
        self.file_creation_date = None
        self.photo_info_UI = UI.Label((5, 5), self.app.font_small, "", (255, 255, 255))
        self.playback_info_UI = UI.Label((5, 5), self.app.font_small, "", (255, 255, 255))

    def set(self):
        self.app.scene = "saved"
        self.viewer_scroll = 0
        self.selected_photo_id = 0
        self.generate_thumbnails()
        self.render()

    def set_surface_from_video_thumbnail(self, path: str, surface: pg.Surface, timestamp: float = 1.0):
        filepath, filetype = path.split('.')[:2]

        filename = filepath.split('/')[-1]
        cached_file = os.path.join("cache", filename + '.jpg')

        if os.path.isfile(cached_file):
            surface.blit(pg.image.load(cached_file))
        
        else:
            clip = moviepy.VideoFileClip(path)
            array = clip.get_frame(timestamp)
            array = np.ascontiguousarray(array[:,:,:3])

            width, height = array.shape[1], array.shape[0]

            surface.blit(pg.transform.scale(pg.image.frombytes(array.tobytes(), (width, height), "RGB"), self.thumbnail_size))
            surface.blit(self.app.icons.get_slice(1))

            clip.close()

            pg.image.save(surface, cached_file)

        self.app.should_update = True

    def get_surface_from_frame(self, video: moviepy.VideoFileClip, timestamp):
        array = video.get_frame(timestamp)
        array = np.ascontiguousarray(array[:,:,:3])
        width, height = array.shape[1], array.shape[0]
        return self.app.aspect_scale(pg.image.frombytes(array.tobytes(), (width, height), "RGB"), self.app.resolution)

    def get_thumbnail(self, file):
        filename, filetype = file.split('.')[:2]

        exact_path = os.path.join(self.app.settings['folder'], file)

        surface = pg.Surface(self.thumbnail_size)
        is_video = True if filetype in ["mp4"] else False
        
        if is_video:
            # self.set_surface_from_video_thumbnail(exact_path, surface, 15)
            threading.Thread(target=self.set_surface_from_video_thumbnail, args=(exact_path, surface, 15)).start()
        else:
            surface.blit(pg.transform.scale(pg.image.load(exact_path), self.thumbnail_size), (0, 0))

            surface.blit(self.app.icons.get_slice(0))

        return surface, exact_path, file

    def generate_thumbnails(self, start = 0):
        self.thumbnails = []
        path = self.app.settings['folder']
        files = self.app.list_files()

        end_index = (4) * self.thumbnail_x

        for file in files[start:end_index]:
            self.thumbnails.append(self.get_thumbnail(file))
            self.should_update = True

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

    def pause(self):
        self.playback = 1
        self.start_pawsed = time.time()
        if self.should_play_audio:
            pg.mixer.music.pause()

    def unpause(self):
        if not pg.mixer.music.get_busy() and self.should_play_audio:
            pg.mixer.music.play()

        pg.mixer.music.unpause()

        if self.timestamp == 0:
            self.start_playback = time.time()

        self.playback = 0
        
        if self.start_pawsed:
            self.start_playback += (time.time() - self.start_pawsed)
            print((time.time() - self.start_pawsed))
            self.start_pawsed = False

        if self.should_play_audio:
            pg.mixer.music.set_pos(time.time() - self.start_playback)

    def toggle_pause(self):
        if self.playback == 0:
            self.pause()

        elif self.playback == 1:
            self.unpause()

    def skip_forward(self):
        self.timestamp += 5

        # if (time.time() - self.start_playback) > self.loaded_clip.end:
        #     self.playback = 1
        #     self.timestamp = self.loaded_clip.end

        self.app.should_update = True

        if self.timestamp >= self.loaded_clip.end:
            self.timestamp = self.loaded_clip.end
            self.start_pawsed = False
            self.playback = 1
            self.start_playback = time.time() - self.loaded_clip.end
            
            if self.should_play_audio:
                pg.mixer.music.stop()

        else:
            self.start_playback -= 5

        if pg.mixer.music.get_busy() and self.should_play_audio and self.playback == 0:                
            pg.mixer.music.set_pos(self.timestamp)

    def go_back(self):
        # if (time.time() - self.start_playback) > self.loaded_clip.end:
        #     self.start_playback = time.time()
        
        self.timestamp -= 5

        self.app.should_update = True

        if self.timestamp < 0:
            self.start_playback = time.time()
            self.timestamp = 0
            self.start_pawsed = None

        else:
            self.start_playback += 5

        if pg.mixer.music.get_busy() and self.playback == 0 and self.should_play_audio:
            pg.mixer.music.set_pos(self.timestamp)
        
        # if (time.time() - self.start_playback) > self.loaded_clip.end:
        #     self.start_playback = time.time() - self.loaded_clip.end

    def render(self):
        if self.selected:
            if self.video:
                if self.playback == 0:
                    self.timestamp = time.time() - self.start_playback

                    self.app.should_update = True

                    if self.timestamp > self.loaded_clip.end:
                        self.playback = 1
                        self.timestamp = self.loaded_clip.end

                self.app.display.fill((0, 0, 0))
                surface, size = self.get_surface_from_frame(self.loaded_clip, self.timestamp)
                self.app.display.blit(surface, (self.app.resolution[0]/2 - size[0]/2, self.app.resolution[1]/2 - size[1]/2))

                self.playback_info_UI.set(f"""resolution: {int(size[0])}x{int(size[1])}
date: {self.file_creation_date}
size: {utils.return_estimated_file_size(self.selected_file)}
fps: {round(self.loaded_clip.fps, 2)} {f"(displaying: {self.app.settings["max fps"]})" if self.loaded_clip.fps > self.app.settings["max fps"] else ""}
{utils.format_seconds(self.timestamp)}s / {utils.format_seconds(self.loaded_clip.end)}""")
                
                self.playback_info_UI.render(self.app.display)

            else:
                self.app.display.fill((0, 0, 0))
                surface, size = self.app.aspect_scale(self.selected_photo, self.app.resolution)
                self.app.display.blit(surface, (self.app.resolution[0] / 2 - size[0]/2, self.app.resolution[1] / 2 - size[1]/2))

                self.photo_info_UI.render(self.app.display)

        else:
            self.app.display.blit(self.app.background, (0, 0))
            self.saved_shape.render(self.app.display)

            gap = (1) / self.thumbnail_x * self.gap_size

            for i, surface in enumerate(self.thumbnails):
                fill_x = (i % self.thumbnail_x) / self.thumbnail_x * self.gap_size
                y = 25 + (i)//self.thumbnail_x * (self.thumbnail_size[1] + gap + 10)
                pos = (25 + fill_x + (i%self.thumbnail_x) * (self.thumbnail_size[0] + 10), y)
                bordercolor = (25, 25, 25)

                if i == self.selected_photo_id:
                    self.selected_file, self.selected_name = surface[1], surface[2]
                    bordercolor = (255, 0, 0)

                pg.draw.rect(self.app.display, bordercolor, (pos[0] - 5, pos[1] - 5, self.thumbnail_size[0] + 10, self.thumbnail_size[1] + 10))

                self.app.display.blit(surface[0], pos)

    def show_selection(self):
        if self.selected:
            return
            
        self.selected = True

        self.file_format = self.selected_file.split('.')[-1]
        is_video = True if self.file_format in ["mp4"] else False

        try:
            unix_time = self.selected_name[self.selected_name.find("_")+1:self.selected_name.find(".")].replace("_", ".")
            self.file_creation_date = utils.convert_unix_to_date(float(unix_time))
        except:
            self.file_creation_date = utils.get_creation_date(self.selected_file)

        if is_video:
            self.video = True
            self.loaded_clip = moviepy.VideoFileClip(self.selected_file)
            self.should_play_audio = self.loaded_clip.audio and self.app.can_play_audio
            if self.should_play_audio:
	            utils.convert_to_mp3(self.selected_file)
	            pg.mixer.music.load(f"{self.selected_file[:-4]}.mp3")
	            pg.mixer.music.set_volume(self.app.settings["playback volume"])
	            pg.mixer.music.play()
            self.start_playback = time.time()
            self.playback = 0
            self.app.variable_fps = min(self.loaded_clip.fps, self.app.settings['max fps'])
            return

        self.video = False
        self.selected_photo = pg.image.load(self.selected_file)

        string = ""
        if self.file_info["resolution"]:
            string += f"resolution: {self.selected_photo.get_width()}x{self.selected_photo.get_height()}\n"
        if self.file_info["date"]:
            string += f"date: {self.file_creation_date}\n"
        if self.file_info["size"]:
            string += f"size: {utils.return_estimated_file_size(self.selected_file)}\n"
        if self.file_info["sharpness index"]:
            string += f"sharpness index: {utils.get_sharpness_index(self.selected_photo)}\n"

        self.photo_info_UI.set(string)

    def leave(self):
        if self.selected:
            # self.audio_thread.kill()

            if self.app.can_play_audio and pg.mixer.music.get_busy():
                pg.mixer.music.stop()

                pg.mixer.music.unload()

            if self.loaded_clip:
                self.loaded_clip.close()

            self.video = False
            self.selected = False
            self.app.variable_fps = self.app.settings['default fps']
            return
        
        self.selected = None
        self.selected_photo_id = 0
        self.viewer_scroll = 0

        self.app.scene = 'main'
        self.app.should_update = True
