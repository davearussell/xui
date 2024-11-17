import time

import pygame
import pygame.locals

from .widget import Stack, NEEDS_REDRAW, NEEDS_LAYOUT


class Window(Stack):
    fixed_width = True
    fixed_height = True
    halign = 'center'
    valign = 'center'

    def __init__(self):
        super().__init__()
        self.surface = pygame.display.set_mode(flags=pygame.FULLSCREEN)
        self.rect = self.surface.get_rect()
        self.size = self.rect.size

    def flagged_widgets(self, flag):
        to_check = [self]
        flagged = []
        while to_check:
            widget = to_check.pop()
            if widget.flags & flag:
                flagged.append(widget)
            else:
                to_check += widget.children
        return flagged

    def update(self):
        if self.flagged_widgets(NEEDS_LAYOUT):
            self.layout() # TODO: can we be more selective?

        to_redraw = self.flagged_widgets(NEEDS_REDRAW)
        for widget in to_redraw:
            widget.draw()
        if to_redraw:
            pygame.display.update([widget.rect for widget in to_redraw])

    def layout(self):
        self.resolve_tree()
        # TODO: check that we fit in width/height
        super().layout()

class App:
    framerate = 30

    def __init__(self):
        pygame.init()
        self.window = Window()
        self.size = self.window.size
        self.exiting = False
        self.clock = pygame.time.Clock()
        self.t0 = time.time()

    def log(self, msg):
        print("%.3fs: %s" % (time.time() - self.t0, msg))

    def handle_event(self, event):
        if event.type == pygame.locals.QUIT:
            self.exiting = True
        elif event.type in [pygame.locals.WINDOWFOCUSGAINED, pygame.locals.WINDOWSHOWN]:
            self.window.redraw()
        else:
            return False
        return True

    def handle_events(self):
        any_events = False
        for event in pygame.event.get():
            any_events |= self.handle_event(event)
        return any_events

    def run(self):
        self.window.update()
        while not self.exiting:
            now = time.time()
            if self.handle_events():
                self.window.update()
            else:
                self.clock.tick(self.framerate)
        self.pre_exit_hook()
        pygame.quit()

    def quit(self):
        self.exiting = True

    def pre_exit_hook(self):
        pass
