import time

import pygame
import pygame.locals
import pygame._sdl2

from . import keys
from . import mouse
from .widget import Widget, UNLIMITED

TIMER_EVENT = pygame.USEREVENT + 1


def update_init_settings(cls, settings):
    """Arranges for new instances of this class and its subclasses
    to be created with the specified settings by default."""
    relevant = {k: v for k, v in settings.items() if k.islower()}
    if cls.__name__ in settings:
        relevant |= settings[cls.__name__]
    for k, v in relevant.items():
        if hasattr(cls, k):
            setattr(cls, k, v)
    for subcls in cls.__subclasses__():
        update_init_settings(subcls, settings)


class Screen(Widget):
    fixed_width = True
    fixed_height = True
    child_halign = 'center'
    child_valign = 'center'

    bgcolor = 'black'

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.init_screen()
        pygame.display.set_caption(app.title)
        self.rect = self.surface.get_rect()
        self.size = self.rect.size
        self.focus_widget = None

    def init_screen(self):
        self.surface = pygame.display.set_mode(flags=pygame.FULLSCREEN)

    def apply_settings(self, settings):
        super().apply_settings(settings)
        update_init_settings(Widget, settings)
        self.redraw()
        self.relayout()

    def handle_keydown(self, event, keystroke):
        """Tries to find a widget to handle this keystroke, returning True if so or
        False if no widgets wanted it.

        Starts with the focus widget. If a widget rejects the keystroke, tries the
        widget's parent next. Alternatively a widget can delegate a different widget
        to handle the keystroke."""
        widget = self.focus_widget
        while widget and widget is not self:
            result = widget.handle_keydown(event, keystroke)
            if isinstance(result, Widget):
                widget = result
            elif result:
                return True
            else:
                widget = widget.parent
        return False

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
                if not widget.hide:
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


class FixedSizeWindow(Screen):
    def __init__(self, app, resolution):
        self.resolution = resolution
        super().__init__(app)

    def init_screen(self):
        self.surface = pygame.display.set_mode(self.resolution)


class AutoSizeWindow(FixedSizeWindow):
    def __init__(self, app):
        super().__init__(app, (0, 0))
        self._positioned = False

    def init_screen(self):
        # Order matters here: display.Info() gives the screen resolution before the
        # first call to display.set_mode, and the current window size afterwards.
        info = pygame.display.Info()
        self._screen_res = (info.current_w, info.current_h)
        super().init_screen()

    def hlayout(self):
        child_width = max(child.max_width() for child in self.children) if self.children else 0
        assert child_width < UNLIMITED
        self.width = child_width + 2 * self.margin
        super().hlayout()

    def vlayout(self):
        child_height = max(child.max_height() for child in self.children) if self.children else 0
        assert child_height < UNLIMITED
        self.height = child_height + 2 * self.margin
        super().vlayout()

    def finalise_layout(self):
        self.resolution = (self.width, self.height)
        self.init_screen()
        super().finalise_layout()

    def draw(self):
        if not self._positioned:
            # The first time we are drawn, position ourselves in the center of the screen.
            # If we are resized, do not reposition (i.e. keep topleft corner in same place)
            x = max(0, (self._screen_res[0] - self.width) // 2)
            y = max(0, (self._screen_res[1] - self.height) // 2)
            pygame._sdl2.Window.from_display_module().position = (x, y)
            self._positioned = True
        super().draw()


class App:
    framerate = 30
    fullscreen = True
    resolution = None
    title = 'XUI'

    def __init__(self):
        pygame.init()
        if self.fullscreen:
            self.screen = Screen(self)
        elif self.resolution:
            self.screen = FixedSizeWindow(self, self.resolution)
        else:
            self.screen = AutoSizeWindow(self)
        self.size = self.screen.size
        self.timers = []
        self.exiting = False
        self.clock = pygame.time.Clock()
        self.t0 = time.time()

    def add_window(self, window):
        self.screen.children.append(window)

    def remove_window(self, window):
        self.screen.children.remove(window)

    def apply_settings(self, settings):
        self.screen.apply_settings(settings)

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

    def handle_keydown_event(self, event):
        keystroke = keys.event_keystroke(event)
        if keystroke is None:
            return
        if not self.screen.handle_keydown(event, keystroke):
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
            self.screen.redraw()
        elif event.type == pygame.locals.MOUSEBUTTONDOWN:
            self.screen.handle_mouse_down(mouse.event_button(event), event.pos)
        elif event.type == pygame.locals.MOUSEBUTTONUP:
            self.screen.handle_mouse_up(mouse.event_button(event), event.pos)
        elif event.type == pygame.locals.MOUSEMOTION:
            self.screen.handle_mouse_move(event.pos)
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

    def unhandled_keydown_hook(self, event, keystroke):
        pass

    def idle_hook(self, deadline):
        pass

    def pre_exit_hook(self):
        pass
