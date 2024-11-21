import time

import pygame
import pygame.locals

from .widget import Widget

TIMER_EVENT = pygame.USEREVENT + 1


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
        self.timers = []
        self.exiting = False
        self.clock = pygame.time.Clock()
        self.t0 = time.time()

    def add_window(self, window):
        self.screen.children.append(window)

    def remove_window(self, window):
        self.screen.children.remove(window)

    def log(self, msg):
        print("%.3fs: %s" % (time.time() - self.t0, msg))

    def start_event_timer(self, delay_s):
        millis = max(1, int(delay_s * 1000))
        pygame.time.set_timer(TIMER_EVENT, millis=millis, loops=1)

    def call_later(self, delay_s, fn, *args, **kwargs):
        expiry = time.time() + delay_s
        if not self.timers or expiry < self.timers[0][0]:
            self.start_event_timer(delay_s)
        token = (expiry, fn, args, kwargs)
        self.timers.append(token)
        self.timers.sort()
        return token

    def cancel_call(self, token):
        if token in self.timers:
            self.timers.remove(token)

    def check_timers(self):
        now = time.time()
        while self.timers and (self.timers[0][0] - .002) < now:
            # if a timer is up to 2ms in the future, fire it now: if we go to sleep again
            # now, then it would be very late by the time we wake up again and fire it.
            _, fn, args, kwargs = self.timers.pop(0)
            fn(*args, **kwargs)
        if self.timers:
            self.start_event_timer(self.timers[0][0] - now)

    def handle_event(self, event):
        if event.type == pygame.locals.QUIT:
            self.exiting = True
        elif event.type == TIMER_EVENT:
            self.check_timers()
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

    def idle(self, deadline):
        self.idle_hook(deadline)
        self.clock.tick(self.framerate)

    def run(self):
        self.screen.update()
        while not self.exiting:
            now = time.time()
            if not self.handle_events():
                self.idle(now + 1 / self.framerate)
            self.screen.update()
        self.pre_exit_hook()
        pygame.quit()

    def quit(self):
        self.exiting = True

    def idle_hook(self, deadline):
        pass

    def pre_exit_hook(self):
        pass
