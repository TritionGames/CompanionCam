import pygame as pg

RESOLUTION = 640, 480

class StandardUI:
    def __init__(self):
        self.use_icon = False
        self.icon = None

class Frame(StandardUI):
    def __init__(self, width, height, framesize = (640, 480)):
        super().__init__()
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

                if widget.use_icon:
                    icon_size = widget.icon.get_size()

                    display.blit(widget.icon, (x * gap[0] + 30 - icon_size[0]/2, y * gap[1] + 30 - icon_size[1]/2))

                else:
                    if not (widget.title, is_active) in self.cached:
                        self.cached[(widget.title, is_active)] = (active_font if is_active else font).render(widget.title, True, color)
                    
                    text = self.cached[(widget.title, is_active)]

                    center = (x*gap[0] + padding[0], y*gap[1] + padding[1])
                    display.blit(text, (center[0] - text.get_width()/2, center[1] - text.get_height()/2))

class Button(StandardUI):
    def __init__(self, callback, title, args = (), icon = None):
        super().__init__()
        self.title = title
        self.callback = callback
        self.args = args
        self.use_icon = bool(icon)
        self.icon = icon

class Shape(StandardUI):
    def __init__(self, pos, size):
        super().__init__()
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

class Label(StandardUI):
    def __init__(self, pos, font, title, color, outline = True):
        super().__init__()
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

class PopUp(StandardUI):
    def __init__(self, font: pg.font.Font, small_font: pg.font.Font, string: str, options: list):
        super().__init__()
        self.options = options
        self.active_id = 0
        self.string = string
        self.font = font
        self.small_font = small_font
        # self.text = self.font.render(string, False, (255, 255, 255))
        self.label = Label((0, 0), self.font, string, (255, 255, 255))
        self.rect = pg.Rect(50, 50, 540, 380)

    def render(self, display):
        pg.draw.rect(display, (50, 50, 50), self.rect)
        pg.draw.rect(display, (25, 25, 25), self.rect, 3)
        # display.blit(self.text, (RESOLUTION[0] / 2 - self.text.get_width()/2, RESOLUTION[1] / 2 - self.text.get_height()/2 - 100))
        self.label.pos = (RESOLUTION[0] / 2 - self.label.text.get_width()/2, RESOLUTION[1] / 2 - self.label.text.get_height()/2 - 100)
        self.label.render(display)

        for i, options in enumerate(self.options):
            text = self.small_font.render(options, True, (255, 255, 255) if i != self.active_id else (0, 255, 0))
            pg.draw.rect(display, (40, 40, 40), (75 - 8, 230 + i * 35 - 8, text.get_width() + 12, 30))
            pg.draw.rect(display, (25, 25, 25), (75 - 8, 230 + i * 35 - 8, text.get_width() + 12, 30), 3)
            display.blit(text, (75, 230 + i * 35))

    def move_down(self):
        if self.active_id >= len(self.options) - 1:
            return
        
        self.active_id += 1

    def move_up(self):
        if self.active_id <= 0:
            return
        
        self.active_id -= 1

    def call(self, app):
        print('hello', self.options[self.active_id])

        app.back()