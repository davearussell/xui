from functools import partial
import pygame

from ..widget import Widget
from .label import Label

class Button(Widget):
    def __init__(self, click_cb=None, **kwargs):
        self.click_cb = click_cb
        self.clicked = False
        super().__init__(**kwargs)

    def handle_mouse_down(self, button, pos):
        if button == 'left' and self.enabled:
            self.clicked = True
            self.redraw()
            return True

    def handle_mouse_up(self, button, pos):
        if button == 'left' and self.clicked:
            self.clicked = False
            self.redraw()
            if pos and self.click_cb:
                self.click_cb()

    def handle_mouse_enter(self):
        super().handle_mouse_enter()
        self.redraw()

    def handle_mouse_exit(self):
        super().handle_mouse_exit()
        self.redraw()


class IconButton(Button):
    fixed_width = True
    fixed_height = True

    def draw_icon(self, color):
        pass

    def draw(self):
        super().draw()
        border_color = self.disabled_color if not self.enabled else self.color
        icon_color = self.highlight_color if self.clicked else border_color
        pygame.draw.rect(self.surface, border_color, self.surface.get_rect(), 1)
        self.draw_icon(icon_color)


class PushButton(Button):
    margin = 5

    def __init__(self, text, **kwargs):
        self.label = Label(text)
        super().__init__(children=[self.label], **kwargs)
        self.label.set_enabled(self.enabled)

    def apply_child_settings(self, settings):
        self.label.apply_settings(settings)

    def set_enabled(self, enabled):
        super().set_enabled(enabled)
        self.label.set_enabled(enabled)

    def draw(self):
        super().draw()
        color = (self.disabled_color if not self.enabled
                 else self.highlight_color if self.clicked
                 else self.color)
        pygame.draw.rect(self.surface, color, self.surface.get_rect(), 2)


class CheckBox(Button):
    fixed_width = True
    fixed_height = True
    width = 16
    height = 16
    margin = 3
    bgcolor = (64, 64, 64)
    highlight_color = (128, 128, 128)
    checked = False

    def set_checked(self, checked):
        self.checked = checked
        self.redraw()

    def draw(self):
        super().draw()
        if self.checked or (self.clicked and self.has_mouse_focus):
            self.draw_checkmark(self.color if self.checked else self.highlight_color)

    def draw_checkmark(self, color):
        m = self.margin
        rect = pygame.Rect(m, m, self.width - 2 * m, self.height - 2 * m)
        pygame.draw.rect(self.surface, color, rect)


class RadioButtonGroup:
    def __init__(self, buttons=None, select_cb=None):
        self.select_cb = select_cb
        self.buttons = buttons
        self.selected = None
        self.buttons = []
        if buttons:
            for button in buttons:
                self.add_button(button)

    def add_button(self, button):
        self.buttons.append(button)
        button.click_cb = partial(self.click_cb, len(self.buttons) - 1)

    def select_button(self, i):
        if self.selected is not None:
            self.buttons[self.selected].set_checked(False)
        self.selected = i
        if self.selected is not None:
            self.buttons[self.selected].set_checked(True)

    def click_cb(self, i):
        self.select_button(i)
        if self.select_cb:
            self.select_cb(i)
