import time

import pygame
import pygame.locals

from . import keys
from .widget import Widget, Stack, NEEDS_REDRAW, NEEDS_LAYOUT

TIMER_EVENT = pygame.USEREVENT + 1


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

    def focus(self):
        raise Exception("Cannot focus main window")

    def handle_keydown(self, event, keystroke):
        widget = self.focus_widget
        while widget is not self:
            if widget.handle_keydown(event, keystroke):
                return True
            widget = widget.parent
        return False

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
        self.timers = []
        self.exiting = False
        self.clock = pygame.time.Clock()
        self.t0 = time.time()

    def log(self, msg):
        print("%.3fs: %s" % (time.time() - self.t0, msg))

    def apply_settings(self, settings):
        Widget.set_default_settings(settings)
        self.window.apply_settings(settings)

    def start_event_timer(self, delay_s):
        millis = max(1, int(delay_s * 1000))
        pygame.time.set_timer(TIMER_EVENT, millis=millis, loops=1)

    def call_later(self, delay_s, fn, *args, **kwargs):
        expiry = time.time() + delay_s
        if not self.timers or expiry < self.timers[0][0]:
            self.start_event_timer(delay_s)
        self.timers.append((expiry, fn, args, kwargs))
        self.timers.sort()

    def handle_keydown_event(self, event):
        keystroke = keys.event_keystroke(event)
        if keystroke is None:
            return
        if not self.window.handle_keydown(event, keystroke):
            self.unhandled_keydown_hook(event, keystroke)

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
        elif event.type == pygame.locals.KEYDOWN:
            self.handle_keydown_event(event)
        elif event.type == TIMER_EVENT:
            self.check_timers()
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

    def idle(self, deadline):
        self.idle_hook(deadline)
        self.clock.tick(self.framerate)

    def run(self):
        self.window.update()
        while not self.exiting:
            now = time.time()
            if self.handle_events():
                self.window.update()
            else:
                self.idle(now + 1 / self.framerate)
        self.pre_exit_hook()
        pygame.quit()

    def quit(self):
        self.exiting = True

    def unhandled_keydown_hook(self, event, keystroke):
        return False

    def idle_hook(self, deadline):
        pass

    def pre_exit_hook(self):
        pass
