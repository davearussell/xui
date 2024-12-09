import pygame

from ..widget import Widget, UNLIMITED


class ScrollBar(Widget):
    min_button_length = 25
    vertical = True
    clicked = False

    def __init__(self, body, scroll_cb, **kwargs):
        self.body = body
        self.scroll_cb = scroll_cb
        super().__init__(**kwargs)

    def length(self):
        return self.size[self.vertical]

    def body_length(self):
        return self.body.size[self.vertical]

    def button_length(self):
        target_length = self.length() ** 2 // self.body_length()
        return max(self.min_button_length, target_length)

    def draw(self):
        super().draw()
        viewport_length = self.body.viewport.size[self.vertical]
        body_length = self.body_length()
        if body_length <= viewport_length:
            return

        viewport_center = self.body.viewport.center[self.vertical]
        body_frac = (viewport_center - viewport_length / 2) / (body_length - viewport_length)
        button_length = self.button_length()
        button_center = button_length // 2 + int(body_frac * (self.length() - button_length))
        button_start = button_center - button_length // 2

        if self.vertical:
            button = pygame.Rect(0, button_start, self.width, button_length)
        else:
            button = pygame.Rect(button_start, 0, button_length, self.height)
        pygame.draw.rect(self.surface, self.color, button)

    def jump_to_pos(self, pos):
        offset = pos[self.vertical]
        button_length = self.button_length()
        bar_frac = (offset - button_length // 2) / (self.length() - button_length)

        viewport = self.body.viewport.copy()
        viewport_length = viewport.size[self.vertical]
        body_length = self.body_length()
        viewport_center = viewport_length // 2 + int(bar_frac * (body_length - viewport_length))
        if self.vertical:
            viewport.centery = viewport_center
            if viewport.bottom > body_length:
                viewport.bottom = body_length
            if viewport.top < 0:
                viewport.top = 0
        else:
            viewport.centerx = viewport_center
            if viewport.right > body_length:
                viewport.right = body_length
            if viewport.left < 0:
                viewport.left = 0
        self.scroll_cb(viewport)

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


class HScrollBar(ScrollBar):
    fixed_height = True
    vertical = False


class VScrollBar(ScrollBar):
    fixed_width = True
    vertical = True


class ScrollArea(Widget):
    # int: scroll by N pixels
    # float: scroll by N * self.height pixels
    mousewheel_scroll = 0.2
    bar_thickness = 20
    bar_bgcolor = (64, 64, 64)

    horizontal = False
    vertical = False
    left_bar = False
    right_bar = False
    top_bar = False
    bottom_bar = False

    def __init__(self, body, **kwargs):
        self.body = body
        super().__init__([body], **kwargs)
        self.body.viewport = pygame.Rect(0, 0, 0, 0)
        self.bars = []
        if self.left_bar:
            self._left_bar = VScrollBar(self.body, scroll_cb=self.ensure_visible,
                                        width=self.bar_thickness, bgcolor=self.bar_bgcolor)
            self.bars.append(self._left_bar)
        if self.right_bar:
            self._right_bar = VScrollBar(self.body, scroll_cb=self.ensure_visible,
                                         width=self.bar_thickness,bgcolor=self.bar_bgcolor)
            self.bars.append(self._right_bar)
        if self.top_bar:
            self._top_bar = HScrollBar(self.body, scroll_cb=self.ensure_visible,
                                       height=self.bar_thickness, bgcolor=self.bar_bgcolor)
            self.bars.append(self._top_bar)
        if self.bottom_bar:
            self._bottom_bar = HScrollBar(self.body, scroll_cb=self.ensure_visible,
                                          height=self.bar_thickness, bgcolor=self.bar_bgcolor)
            self.bars.append(self._bottom_bar)
        self.children += self.bars
        self.vertical |= (self.left_bar or self.right_bar)
        self.horizontal |= (self.top_bar or self.bottom_bar)

    def apply_settings(self, settings):
        super().apply_settings(settings)
        self.body.apply_settings(settings)
        for bar in self.bars:
            dimension = 'width' if bar.fixed_width else 'height'
            bar.apply_settings(settings | {
                'bgcolor': self.bar_bgcolor,
                dimension: self.bar_thickness,
            })

    def min_contents_height(self):
        bar_height = self.bar_thickness * (bool(self.top_bar) + bool(self.bottom_bar))
        return bar_height + (0 if self.vertical else self.body.min_height())

    def max_contents_height(self):
        bar_height = self.bar_thickness * (bool(self.top_bar) + bool(self.bottom_bar))
        return bar_height + self.body.max_height()

    def min_contents_width(self):
        bar_width = self.bar_thickness * (bool(self.left_bar) + bool(self.right_bar))
        return bar_width + (0 if self.horizontal else self.body.min_width())

    def max_contents_width(self):
        bar_width = self.bar_thickness * (bool(self.left_bar) + bool(self.right_bar))
        return bar_width + self.body.max_width()

    def body_rect(self):
        width = max(self.body.width, self.body.viewport.width)
        height = max(self.body.height, self.body.viewport.height)
        return pygame.Rect(0, 0, width, height)

    def vlayout(self):
        bar_height = self.bar_thickness * (bool(self.top_bar) + bool(self.bottom_bar))
        self.body.viewport.height = self.height - 2 * self.margin - bar_height

        y = self.y + self.margin
        if self.top_bar:
            self._top_bar.y = y
            y += self.bar_thickness
        self.body.y = y
        if self.vertical:
            if self.left_bar:
                self._left_bar.y = self.body.y
                self._left_bar.set_height(self.body.viewport.height)
            if self.right_bar:
                self._right_bar.y = self.body.y
                self._right_bar.set_height(self.body.viewport.height)
            self.body.set_height(self.body.max_height())
            assert self.body.height < UNLIMITED
        else:
            self.body.set_height(self.body.viewport.height)
        self.body.vlayout()
        if self.bottom_bar:
            self._bottom_bar.y = self.body.y + self.body.viewport.height

    def hlayout(self):
        bar_width = self.bar_thickness * (bool(self.left_bar) + bool(self.right_bar))
        self.body.viewport.width = self.width - 2 * self.margin - bar_width

        x = self.x + self.margin
        if self.left_bar:
            self._left_bar.x = x
            x += self.bar_thickness
        self.body.x = x
        if self.horizontal:
            if self.top_bar:
                self._top_bar.x = self.body.x
                self._top_bar.set_width(self.body.viewport.width)
            if self.bottom_bar:
                self._bottom_bar.x = self.body.x
                self._bottom_bar.set_width(self.body.viewport.width)
            self.body.set_width(self.body.max_width())
            assert self.body.width < UNLIMITED
        else:
            self.body.set_width(self.body.viewport.width)
        self.body.hlayout()
        if self.right_bar:
            self._right_bar.x = self.body.x + self.body.viewport.width

    def ensure_visible(self, rect):
        body_rect = self.body_rect()
        assert body_rect.contains(rect)
        self.body.viewport.clamp_ip(body_rect)
        tmp = rect.clamp(self.body.viewport)
        self.body.viewport.move_ip(rect.left - tmp.left, rect.top - tmp.top)
        assert body_rect.contains(self.body.viewport)
        assert self.body.viewport.contains(rect)
        self.redraw()

    def handle_mouse_down(self, button, pos):
        if button in ['wheeldown', 'wheelup'] and (self.vertical or self.horizontal):
            pixels = self.mousewheel_scroll * (1 if button == 'wheeldown' else -1)
            if isinstance(pixels, float):
                pixels = int(pixels * (self.height if self.vertical else self.width))
            offset = (0, pixels) if self.vertical else (pixels, 0)
            self.ensure_visible(self.body.viewport.move(*offset).clamp(self.body_rect()))
            return True
        return super().handle_mouse_down(button, pos)
