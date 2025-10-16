import pygame as pg

class Icons:
    def __init__(self, app):
        self.app = app

        self.tileset = pg.image.load("icons_spritesheet.png").convert_alpha()
        
        self.num_x = 8
        self.num_y = 8
        self.icon_size = 12

    def get_slice(self, n):
        surface = pg.Surface((self.icon_size, self.icon_size), pg.SRCALPHA)

        x, y = n % self.num_x, n // self.num_x
        
        surface.blit(self.tileset, (-x * self.icon_size, -y * self.icon_size))

        return pg.transform.scale(surface, (24, 24))