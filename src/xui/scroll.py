import pygame

from .widget import Widget, HBox, UNLIMITED


class Scrollable(Widget):
    scroll_area = None # set by parent during layout
    full_height = None # subclasses should set this once known (e.g. by hooking size_updated)

    def mouse_rel_pos(self, pos):
        rel_pos = super().mouse_rel_pos(pos)
        if self.scroll_area and rel_pos is not None:
            x, y = rel_pos
            wx, wy = self.scroll_area.window.topleft
            return x + wx, y + wy
        return rel_pos


class ScrollBar(Widget):
    fixed_width = True
    width = 20
    min_button_height = 25
    bgcolor = (64, 64, 64)
    color = 'white'
    clicked = False

    def button_height(self):
        target_height = (self.height * self.parent.window.height) // self.parent.body.full_height
        return max(self.min_button_height, target_height)

    def draw(self):
        super().draw()
        window = self.parent.window
        body_height = self.parent.body.full_height
        if body_height <= window.height:
            return
        button_height = self.button_height()
        body_frac = (window.centery - window.height / 2) / (body_height - window.height)
        button = pygame.Rect(0, 0, self.width, button_height)
        button.centery = button_height // 2 + int(body_frac * (self.height - button_height))
        pygame.draw.rect(self.surface, self.color, button)

    def jump_to_pos(self, pos):
        _, y = pos
        button_height = self.button_height()
        bar_frac = (y - button_height // 2) / (self.height - button_height)

        window = self.parent.window.copy()
        body_height = self.parent.body.full_height
        window.centery = window.height // 2 + int(bar_frac * (body_height - window.height))
        if window.bottom > body_height:
            window.bottom = body_height
        if window.top < 0:
            window.top = 0
        self.parent.ensure_visible(window)

    def handle_mouse_down(self, button, pos):
        if button != 'left':
            return False
        self.clicked = True
        self.jump_to_pos(pos)
        return True

    def handle_mouse_move(self, pos):
        if pos and self.clicked:
            self.jump_to_pos(pos)

    def handle_mouse_up(self, button, pos):
        if button == 'left':
            self.clicked = False


class ScrollArea(HBox):
    # int: scroll by N pixels
    # float: scroll by N * self.height pixels
    mousewheel_scroll = 0.2

    def __init__(self, body, **kwargs):
        assert isinstance(body, Scrollable)
        self.body = body
        self.bar = ScrollBar()
        super().__init__([self.body, self.bar], **kwargs)
        self.window = pygame.Rect(0, 0, 0, 0)

    def min_height(self):
        return 0

    def max_height(self):
        return UNLIMITED

    def body_rect(self):
        max_height = max(self.body.height, self.body.full_height)
        return pygame.Rect(0, 0, self.body.width, max_height)

    def align_children(self, rect):
        assert self.children == [self.body, self.bar]
        body_rect = pygame.Rect(rect.left, rect.top, rect.width - self.bar.width, rect.height)
        bar_rect = pygame.Rect(body_rect.right, rect.top, self.bar.width, rect.height)
        self.window.size = body_rect.size
        self.body.scroll_area = self
        yield self.body, body_rect
        yield self.bar, bar_rect

    def ensure_visible(self, rect):
        body_rect = self.body_rect()
        assert body_rect.contains(rect)
        if rect.top < self.window.top:
            self.window.top = rect.top
        elif rect.bottom > self.window.bottom:
            self.window.bottom = rect.bottom
        assert body_rect.contains(self.window)
        self.redraw()

    def handle_mouse_down(self, button, pos):
        if button in ['wheeldown', 'wheelup']:
            pixels = self.mousewheel_scroll * (1 if button == 'wheeldown' else -1)
            if isinstance(pixels, float):
                pixels = int(pixels * self.height)
            self.ensure_visible(self.window.move(0, pixels).clamp(self.body_rect()))
            return True
        return super().handle_mouse_down(button, pos)
