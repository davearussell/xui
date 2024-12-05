from functools import partial
import pygame

from .widget import Widget, HBox
from .label import Label

class Button(Widget):
    enabled = True

    def __init__(self, click_cb=None, **kwargs):
        super().__init__(**kwargs)
        self.click_cb = click_cb
        self.clicked = False

    def set_enabled(self, enabled):
        self.enabled = enabled
        self.redraw()

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


class PushButton(Button):
    margin = 5
    clicked_color = 'yellow'
    disabled_color = (96, 96, 96)

    def __init__(self, text, **kwargs):
        super().__init__(**kwargs)
        self.label = Label(text)
        self.children = [self.label]

    def child_settings(self, child, settings):
        return settings | {
            'color': self.color if self.enabled else self.disabled_color,
        }

    def set_enabled(self, enabled):
        super().set_enabled(enabled)
        self.apply_settings({})
        self.redraw()

    def draw(self):
        super().draw()
        color = self.disabled_color if not self.enabled else self.clicked_color if self.clicked else self.color
        pygame.draw.rect(self.surface, color, self.surface.get_rect(), 2)


class CheckBox(Button):
    fixed_width = True
    fixed_height = True
    width = 16
    height = 16
    margin = 3
    bgcolor = (64, 64, 64)
    clicked_color = (128, 128, 128)
    color = 'white'
    checked = False

    def set_checked(self, checked):
        self.checked = checked
        self.redraw()

    def draw(self):
        super().draw()
        if self.checked or (self.clicked and self.has_mouse_focus):
            self.draw_checkmark(self.color if self.checked else self.clicked_color)

    def draw_checkmark(self, color):
        m = self.margin
        rect = pygame.Rect(m, m, self.width - 2 * m, self.height - 2 * m)
        pygame.draw.rect(self.surface, color, rect)


class LabelledCheckBox(HBox):
    spacing = 2
    valign = 'center'

    def __init__(self, text, keybind=None):
        super().__init__()
        self.label = Label(text, keybind=keybind)
        self.button = CheckBox()
        self.children = [self.button, self.label]

    def set_checked(self, checked):
        self.button.set_checked(checked)

    def set_enabled(self, enabled):
        self.button.set_enabled(enabled)

    @property
    def click_cb(self):
        return self.button.click_cb

    @click_cb.setter
    def click_cb(self, cb):
        self.button.click_cb = cb

    @property
    def checked(self):
        return self.button.checked


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
