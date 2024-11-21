import time

import pygame
import pygame.locals

from .widget import Widget


class Screen(Widget):
    fixed_width = True
    fixed_height = True
    child_halign = 'center'
    child_valign = 'center'

    bgcolor = 'black'

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.surface = pygame.display.set_mode(flags=pygame.FULLSCREEN)
        self.rect = self.surface.get_rect()
        self.size = self.rect.size
        self.focus_widget = None

    def update(self):
        updated = False
        while self.needs_layout():
            updated = True
            self.layout()

        widgets = self.to_redraw()
        if widgets:
            updated = True
            if widgets == [self] and len(self.children) > 1:
                for child in self.children:
                    if child.bgcolor is None:
                        # bgcolor=None means the child should inherit our bgcolor.
                        # Our top level children each have their own surface so we
                        # must fill it explicitly
                        child.surface.fill(self.bgcolor)
            for widget in widgets:
                if widget.bgcolor is None:
                    # bgcolor=None means the child should inherit the parent's background
                    # color. Normally this just works as we'll draw the parent before the
                    # child, but if we're not drawing the parent we must expicitly draw
                    # the background.
                    parent = widget.parent
                    while parent.bgcolor is None:
                        parent = parent.parent
                    widget.surface.fill(parent.bgcolor)
                widget.draw()

            if len(self.children) > 1:
                region = widgets[0].rect.unionall([w.rect for w in widgets[1:]])
                pygame.draw.rect(self.surface, self.bgcolor, region)
                for child in self.children:
                    child_region = child.rect.clip(region)
                    if child_region:
                        rel_region = child_region.move(-child.rect.left, -child.rect.top)
                        self.surface.blit(child.surface, child_region, rel_region)

            if updated:
                pygame.display.update([widget.rect for widget in widgets])

    def setup_surface(self):
        if len(self.children) < 2:
            # With a single child we let it draw directly onto the screen,
            # saving a bit each frame
            super().setup_surface()
            return
        for child in self.children:
            if not (child.surface and
                    child.surface.get_size() == child.size and
                    child.surface.get_parent() is None):
                child.surface = pygame.Surface(child.size, pygame.SRCALPHA)
            child.setup_surface()

    def layout(self):
        self.resolve_tree()
        self.hlayout()
        self.vlayout()
        self.finalise_layout()
        self.setup_surface()
        self.redraw()

class App:
    framerate = 30

    def __init__(self):
        pygame.init()
        self.screen = Screen(self)
        self.size = self.screen.size
        self.exiting = False
        self.clock = pygame.time.Clock()
        self.t0 = time.time()

    def add_window(self, window):
        self.screen.children.append(window)

    def remove_window(self, window):
        self.screen.children.remove(window)

    def log(self, msg):
        print("%.3fs: %s" % (time.time() - self.t0, msg))

    def handle_event(self, event):
        if event.type == pygame.locals.QUIT:
            self.exiting = True
        elif event.type in [pygame.locals.WINDOWFOCUSGAINED, pygame.locals.WINDOWSHOWN]:
            self.screen.redraw()
        else:
            return False
        return True

    def handle_events(self):
        any_events = False
        for event in pygame.event.get():
            any_events |= self.handle_event(event)
        return any_events

    def run(self):
        self.screen.update()
        while not self.exiting:
            now = time.time()
            if not self.handle_events():
                self.clock.tick(self.framerate)
            self.screen.update()
        self.pre_exit_hook()
        pygame.quit()

    def quit(self):
        self.exiting = True

    def pre_exit_hook(self):
        pass
