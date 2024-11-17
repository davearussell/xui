import pygame

from ..widget import Widget

class Label(Widget):
    supports_viewport = True
    keybind = None

    def __init__(self, text='', **kwargs):
        assert isinstance(text, str)
        self.text = text
        super().__init__(**kwargs)
        self.resolve_size()

    def settings_updated(self):
        self.resolve_size()

    def min_width(self):
        return self.char_width * len(self.text) + 2 * self.margin
    max_width = min_width

    def min_height(self):
        return self.char_height + 2 * self.margin
    max_height = min_height

    def resolve_size(self):
        self.char_width, self.char_height = self.render_text(' ').get_size()

    def set_keybind(self, keybind):
        self.keybind = keybind
        self.redraw()

    def set_text(self, text):
        assert isinstance(text, str)
        if text == self.text:
            return
        len_updated = len(text) != len(self.text)
        self.text = text
        if len_updated:
            self.resolve_size()
            self.relayout()
        self.redraw()

    def draw(self):
        super().draw()

        text_surface = self.render_text(self.text)
        if self.keybind:
            i = self.text.lower().find(self.keybind.lower())
            if i != -1:
                pos = pygame.Rect(i * self.char_width, self.char_height - 1, self.char_width - 1, 1)
                color = self.color if self.enabled else self.disabled_color
                pygame.draw.rect(text_surface, color, pos)

        if self.viewport:
            pos = (self.margin - self.viewport.left, self.margin - self.viewport.top)
        else:
            pos = (self.margin, self.margin)
        self.surface.blit(text_surface, pos)
