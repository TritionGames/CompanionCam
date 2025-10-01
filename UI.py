import pygame as pg

class Frame:
    def __init__(self, width, height, framesize = (640, 480)):
        self.widgets = [[0 for _ in range(width)] for _ in range(height)]
        self.width = width
        self.height = height
        self.active = None
        self.hover_position = [0, 0]
        self.total_widgets = 0
        self.framesize = framesize
        self.cached = {}
        
    def place(self, widget, pos):
        self.widgets[pos[1]][pos[0]] = widget

        self.total_widgets += 1

        if self.total_widgets == 1:
            self.active = widget

    def move(self, direction):
        "direction: 0 - up\n1 - right\n2 bottom\n3 left"

        x, y = self.xydirection(direction)
        
        if not self.valid(x + self.hover_position[0], y + self.hover_position[1]):
            return 

        self.hover_position[0] += x
        self.hover_position[1] += y

        self.active = self.get_widget(*self.hover_position)

    def get_widget(self, x, y):
        return self.widgets[y][x]

    def xydirection(self, direction):
        if direction == 0:
            return 0, -1
        elif direction == 1:
            return 1, 0
        elif direction == 2:
            return 0, 1
        elif direction == 3:
            return -1, 0
    
    def valid(self, x, y):        
        if x >= self.width or x < 0:
            return False
        
        if y >= self.height or y < 0:
            return False
        
        if not self.widgets[y][x]:
            return False

        return True

    def call_button(self):
        if not self.active or not self.active.callback:
            return

        self.active.callback(*self.active.args)

    def render(self, display, font, active_font):
        gap = self.framesize[0] / self.width, self.framesize[1] / self.height
        padding = gap[0] / 2, gap[1] / 2

        for x in range(self.width):
            for y in range(self.height):
                if not self.valid(x, y):
                    continue

                widget = self.get_widget(x, y)

                color = (255, 255, 255)

                is_active = self.hover_position == [x, y]

                if is_active:
                    color = 255, 255, 255
   
                pg.draw.rect(display, (50, 50, 50), (x * gap[0] + 5, y * gap[1] + 5, gap[0] - 10, gap[1] - 10))  
                pg.draw.rect(display, (25, 25, 25), (x * gap[0] + 5, y * gap[1] + 5, gap[0] - 10, gap[1] - 10), 3)

                if not (widget.title, is_active) in self.cached:
                    self.cached[(widget.title, is_active)] = (active_font if is_active else font).render(widget.title, True, color)
                
                text = self.cached[(widget.title, is_active)]

                center = (x*gap[0] + padding[0], y*gap[1] + padding[1])
                display.blit(text, (center[0] - text.get_width()/2, center[1] - text.get_height()/2))

class Button:
    def __init__(self, callback, title, args = ()):
        self.title = title
        self.callback = callback
        self.args = args

class Shape:
    def __init__(self, pos, size):
        self.pos = pos
        self.size = size
        self.widgets = []

    def render(self, display):
        pg.draw.rect(display, (50, 50, 50), (*self.pos, *self.size))
        pg.draw.rect(display, (25, 25, 25), (*self.pos, *self.size), 3)    

        for widget, pos in self.widgets:
            widget.pos = (pos[0] + self.pos[0], pos[1] + self.pos[1])
            widget.render(display)

    def place(self, widget, pos):
        self.widgets.append((widget, pos))

class Label:
    def __init__(self, pos, font, title, color, outline = True):
        self.title = title
        self.pos = pos
        self.color = color
        self.font = font
        self.text = self.font.render(self.title, True, self.color)
        self.use_outline = outline
        self.generate_outline()

    def generate_outline(self):
        w, h = self.text.get_size()
        self.outline_text = self.font.render(self.title, True, (0, 0, 0))
        self.outline_surface = pg.Surface((w + 8, h + 8), pg.SRCALPHA)

        self.outline_surface.blit(self.outline_text, (0, 2))
        self.outline_surface.blit(self.outline_text, (4, 2))
        self.outline_surface.blit(self.outline_text, (2, 4))
        self.outline_surface.blit(self.outline_text, (2, 0))    

    def render(self, display):
        if self.use_outline:
            display.blit(self.outline_surface, (self.pos[0] - 2, self.pos[1] - 2))

        display.blit(self.text, self.pos)

    def set(self, title):
        if self.use_outline:
            self.title = title
            self.text = self.font.render(title, True, self.color)
            self.generate_outline()
