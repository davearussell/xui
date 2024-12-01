import pygame

from .widget import HBox
from .label import Label


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


class LineEdit(HBox):
    border_color = (96, 96, 96)
    focus_border_color = (160, 160, 160)
    color = 'white'
    ro_color = 'grey'
    margin = 3

    num_chars = 30
    read_only = False

    def __init__(self, text='', update_cb=None, commit_cb=None, **kwargs):
        self.label = Label()
        super().__init__([self.label], **kwargs)
        self.update_cb = update_cb
        self.commit_cb = commit_cb
        self.text = text
        self.cursor = 0 # index of character after cursor
        self.offset = 0 # index of leftmost displayed character
        self.set_value(text, cb=False)

    def update_text(self, text, offset, cursor, cb=True):
        if cursor < 0:
            cursor = 0
        if cursor > len(text):
            cursor = len(text)

        min_offset = max(0, cursor - self.num_chars)
        max_offset = min(cursor, max(0, len(text) - self.num_chars))
        if offset < min_offset:
            offset = min_offset
        if offset > max_offset:
            offset = max_offset

        self.text = text
        self.cursor = cursor
        self.offset = offset

        label_text = (text[self.offset:] + ' ' * self.num_chars)[:self.num_chars]
        self.label.set_text(label_text)
        if cb and self.update_cb:
            self.update_cb(text)
        self.redraw()

    def get_value(self):
        return self.text

    def set_value(self, text, cb=True):
        offset = max(0, len(text) - self.num_chars)
        cursor = len(text)
        self.update_text(text, offset, cursor, cb)

    def handle_keydown(self, event, keystroke):
        if keystroke in ['backspace', 'CTRL-backspace']:
            n = prev_word_offset(self.text, self.cursor) if 'CTRL' in keystroke else 1
            text = self.text[:self.cursor - n] + self.text[self.cursor:]
            self.update_text(text, self.offset, self.cursor - n)
            return True
        elif keystroke in ['delete', 'CTRL-delete']:
            n = next_word_offset(self.text, self.cursor) if 'CTRL' in keystroke else 1
            text = self.text[:self.cursor] + self.text[self.cursor + n:]
            self.update_text(text, self.offset, self.cursor)
        elif keystroke in ['return', 'KP-enter']:
            if self.commit_cb:
                self.commit_cb()
        elif keystroke == 'left':
            self.update_text(self.text, self.offset, self.cursor - 1)
        elif keystroke == 'right':
            self.update_text(self.text, self.offset, self.cursor + 1)
        elif keystroke == 'CTRL-left':
            self.update_text(self.text, self.offset, prev_word(self.text, self.cursor))
        elif keystroke == 'CTRL-right':
            self.update_text(self.text, self.offset, next_word(self.text, self.cursor))
        elif keystroke == 'home':
            self.update_text(self.text, self.offset, 0)
        elif keystroke == 'end':
            self.update_text(self.text, self.offset, len(self.text))
        elif 'ALT-' not in keystroke and event.unicode and 32 <= ord(event.unicode) <= 126:
            text = self.text[:self.cursor] + event.unicode + self.text[self.cursor:]
            self.update_text(text, self.offset, self.cursor + 1)
        else:
            return False
        return True

    def handle_mouse_down(self, button, pos):
        if button == 'left':
            rel_pos = pos[0] - self.label.rel_rect.left
            char_i = (rel_pos + self.label.char_width // 2) // self.label.char_width
            cursor = min(len(self.text), self.offset + char_i)
            self.update_text(self.text, self.offset, cursor)
            self.focus()
            return True

    def child_settings(self, child, settings):
        return settings | {
            'color': self.ro_color if self.read_only else self.color,
        }

    def draw(self):
        super().draw()
        if not self.read_only:
            color = self.focus_border_color if self.has_focus else self.border_color
            pygame.draw.rect(self.surface, color, self.surface.get_rect(), 1)
        if self.has_focus:
            rect = self.label.rel_rect
            x = rect.left + (self.cursor - self.offset) * self.label.char_width
            cursor_rect = pygame.Rect(x - 1, rect.top, 2, rect.height)
            pygame.draw.rect(self.surface, self.color, cursor_rect, 1)
