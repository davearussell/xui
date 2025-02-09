import os

import pygame

from .label import Label
from .scroll import ScrollArea
from .dropdown import Dropdown


def next_word(text, i):
    while i < len(text) and not text[i].isspace():
        i += 1
    while i < len(text) and text[i].isspace():
        i += 1
    return i

def next_word_offset(text, i):
    return next_word(text, i) - i

def prev_word(text, i):
    while i and text[i - 1].isspace():
        i -= 1
    while i and not text[i - 1].isspace():
        i -= 1
    return i

def prev_word_offset(text, i):
    return i - prev_word(text, i)


class LineEdit(ScrollArea):
    halign = 'fill'
    horizontal = True
    border_color = (96, 96, 96)
    focus_border_color = (160, 160, 160)
    margin = 3

    num_chars = 30

    def __init__(self, text='', update_cb=None, commit_cb=None, completions=None, **kwargs):
        super().__init__(Label(text), **kwargs)
        self.update_cb = update_cb
        self.commit_cb = commit_cb
        self.completions = sorted(completions or [])
        self.dropdown = Dropdown(self, update_cb=self.comp_update, commit_cb=self.comp_commit,
                                 autohide_bars=False)
        self.cursor = 0 # index of character after cursor

    def set_enabled(self, enabled):
        super().set_enabled(enabled)
        self.body.set_enabled(enabled)

    def max_contents_width(self):
        return self.num_chars * self.body.char_width

    def comp_commit(self, _):
        self.set_value(self.dropdown.choice)
        self.commit_cb()

    def comp_update(self, _):
        self.set_value(self.dropdown.choice)

    def focus_lost(self):
        if self.dropdown.active:
            self.dropdown.close()

    def update_cursor(self, cursor):
        if cursor < 0:
            cursor = 0
        if cursor > len(self.body.text):
            cursor = len(self.body.text)
        self.cursor = cursor
        self.update_viewport()
        self.redraw()

    def update_text(self, text, cursor=None, cb=True):
        self.body.set_text(text)
        if cursor is not None:
            self.update_cursor(cursor)
        if cb and self.update_cb:
            self.update_cb(text)
        self.redraw()

    def get_value(self):
        return self.body.text

    def set_value(self, text):
        self.update_text(text)
        self.update_cursor(len(text))
        if self.update_cb:
            self.update_cb(text)

    def refresh_dropdown(self):
        if not self.has_focus:
            return
        completions = [word for word in self.completions if word.startswith(self.body.text)]
        if completions and not self.dropdown.active:
            self.dropdown.open()
        elif self.dropdown.active and not completions:
            self.dropdown.close()
        if completions != self.dropdown.choices:
            self.dropdown.set_choices(completions)

    def handle_keydown(self, event, keystroke):
        if self.dropdown.active and keystroke in ['up', 'down']:
            return self.dropdown

        text = self.body.text
        cursor = self.cursor
        if keystroke in ['backspace', 'CTRL-backspace']:
            n = prev_word_offset(text, cursor) if 'CTRL' in keystroke else 1
            text = text[:cursor - n] + text[cursor:]
            self.update_text(text, cursor=cursor - n)
        elif keystroke in ['delete', 'CTRL-delete']:
            n = next_word_offset(text, cursor) if 'CTRL' in keystroke else 1
            text = text[:cursor] + text[cursor + n:]
            self.update_text(text)
            self.update_viewport()
        elif keystroke in ['return', 'KP-enter']:
            if self.commit_cb:
                self.commit_cb()
        elif keystroke == 'left':
            self.update_cursor(cursor - 1)
        elif keystroke == 'right':
            self.update_cursor(cursor + 1)
        elif keystroke == 'CTRL-left':
            self.update_cursor(prev_word(text, cursor))
        elif keystroke == 'CTRL-right':
            self.update_cursor(next_word(text, cursor))
        elif keystroke == 'home':
            self.update_cursor(0)
        elif keystroke == 'end':
            self.update_cursor(len(text))
        elif 'ALT-' not in keystroke and event.unicode and 32 <= ord(event.unicode) <= 126:
            text = text[:cursor] + event.unicode + text[cursor:]
            self.update_text(text, cursor + 1)
        elif keystroke == 'tab':
            if self.dropdown.active:
                text = os.path.commonprefix(self.dropdown.choices)
                if text != self.body.text:
                    self.update_text(text, cursor=len(text))
        else:
            return False
        self.refresh_dropdown()
        return True

    def update_viewport(self):
        if not self.body.viewport:
            return # not laid out yet, we'll try again from finalize_layout
        body_rect = self.body_rect()
        self.body.viewport.clamp_ip(body_rect)
        cursor_x = self.cursor * self.body.char_width
        if self.body.viewport.right < cursor_x:
            self.body.viewport.right = cursor_x
        elif self.body.viewport.left > cursor_x:
            self.body.viewport.left = cursor_x

    def finalise_layout(self):
        super().finalise_layout()
        self.update_viewport()

    def handle_mouse_down(self, button, pos):
        if button == 'left':
            rel_pos = self.body.mouse_rel_pos(pos)
            if rel_pos:
                char_i = (rel_pos[0] + self.body.char_width // 2) // self.body.char_width
                self.update_cursor(char_i)
            self.focus()
            return True

    def draw(self):
        self.body.color = self.color
        super().draw()
        if self.enabled:
            color = self.focus_border_color if self.has_focus else self.border_color
            pygame.draw.rect(self.surface, color, self.surface.get_rect(), 1)
        if self.has_focus:
            cursor_x = self.cursor * self.body.char_width + self.margin - self.body.viewport.left
            cursor_rect = pygame.Rect(cursor_x - 1, self.margin, 2, self.body.height)
            pygame.draw.rect(self.surface, self.color, cursor_rect, 1)
