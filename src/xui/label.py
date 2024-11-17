import pygame

from . import widget

class Label(widget.Widget):
    font = 'Liberation Mono'
    color = 'white'
    font_size = 20
    keybind = None

    def __init__(self, text='', **kwargs):
        self.text = text
        self.char_width = None
        super().__init__(**kwargs)

    def min_contents_width(self):
        return self.text_width

    def max_contents_width(self):
        return self.text_width

    def min_contents_height(self):
        return self.text_height

    def max_contents_height(self):
        return self.text_height

    def set_keybind(self, keybind):
        self.keybind = keybind
        self.render()

    def render(self):
        font = pygame.font.SysFont(self.font, self.font_size)
        self.text_surface = font.render(self.text, True, self.color)
        self.text_width, self.text_height = self.text_surface.get_size()

        if self.text:
            self.char_width, rem = divmod(self.text_width, len(self.text))
            assert not rem, (self.text, self.font_size, self.text_surface)
        else:
            self.char_width = 0

        if self.keybind:
            i = self.text.lower().find(self.keybind.lower())
            if i != -1:
                width, height = self.text_surface.get_size()
                char_width, rem = divmod(width, len(self.text))
                assert rem == 0, (self.text_surface, self.text)
                pos = pygame.Rect(i * char_width, height - 1, char_width - 1, 1)
                pygame.draw.rect(self.text_surface, self.color, pos)

        self.redraw()

    def set_text(self, text):
        if text == self.text:
            return
        if len(text) != len(self.text):
            self.relayout()
        self.text = text
        self.render()

    def apply_settings(self, settings):
        super().apply_settings(settings)
        self.render()

    def draw(self):
        super().draw()
        self.surface.blit(self.text_surface, (self.margin, self.margin))
