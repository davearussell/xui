import pygame

from ..widget import Widget
from .scroll import ScrollArea


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


class TextAreaBody(Widget):
    fixed_width = True
    fixed_height = True
    supports_viewport = True

    cursor_flash_period = 0.5

    def __init__(self, text, update_cb, commit_cb, highlight_cb):
        super().__init__()
        self.rows = text.split('\n')
        self.n_rows = len(self.rows)
        self.n_cols = max(map(len, self.rows))
        self.update_cb = update_cb
        self.commit_cb = commit_cb
        self.highlight_cb = highlight_cb
        self.cursor_row = 0
        self.cursor_col = 0
        self.draw_cursor = False
        self.flash_timer = None
        self.resolve_size()

    def resolve_size(self):
        self.char_width, self.char_height = self.render_text(' ').get_size()
        self.height = self.char_height * len(self.rows)
        self.width = self.char_width * (1 + max(map(len, self.rows)))

    def maybe_resize(self):
        n_rows = len(self.rows)
        n_cols = max(map(len, self.rows))
        if (n_rows, n_cols) != (self.n_rows, self.n_cols):
            self.n_rows = n_rows
            self.n_cols = n_cols
            self.resolve_size()
            self.relayout()

    def focus_gained(self):
        self.flash_cursor()

    def focus_lost(self):
        self.cancel_call(self.flash_timer)
        self.draw_cursor = False

    def flash_cursor(self):
        if self.has_focus:
            self.draw_cursor = not self.draw_cursor
            self.flash_timer = self.call_later(self.cursor_flash_period, self.flash_cursor)
            self.redraw()

    def show_cursor(self):
        self.cancel_call(self.flash_timer)
        self.draw_cursor = False
        self.flash_cursor()

    def settings_updated(self):
        self.resolve_size()

    def get_value(self):
        return '\n'.join(self.rows)

    def set_value(self, text):
        self.rows = text.split('\n')
        self.cursor_row = self.cursor_col = 0
        self.maybe_resize()
        self.redraw()

    def text_updated(self):
        if self.update_cb:
            self.update_cb()
        self.maybe_resize()

    def update_cursor(self, row, col):
        assert 0 <= row < len(self.rows)
        assert 0 <= col <= len(self.rows[row])
        self.cursor_row = row
        self.cursor_col = col
        self.update_viewport()
        self.redraw()

    def handle_backspace(self, word=False):
        if self.cursor_col == 0:
            if self.cursor_row > 0:
                col = len(self.rows[self.cursor_row - 1])
                self.rows[self.cursor_row - 1] += self.rows.pop(self.cursor_row)
                self.text_updated()
                self.update_cursor(self.cursor_row - 1, col)
        else:
            text = self.rows[self.cursor_row]
            n = prev_word_offset(text, self.cursor_col) if word else 1
            self.rows[self.cursor_row] = text[:self.cursor_col - n] + text[self.cursor_col:]
            self.text_updated()
            self.update_cursor(self.cursor_row, self.cursor_col - n)

    def handle_delete(self, word=False):
        text = self.rows[self.cursor_row]
        if self.cursor_col == len(text):
            if self.cursor_row < len(self.rows) - 1:
                self.rows[self.cursor_row] += self.rows.pop(self.cursor_row + 1)
                self.text_updated()
        else:
            n = next_word_offset(text, self.cursor_col) if word else 1
            self.rows[self.cursor_row] = text[:self.cursor_col] + text[self.cursor_col + n:]
            self.text_updated()
        self.update_viewport()

    def handle_left(self, word=False):
        text = self.rows[self.cursor_row]
        if self.cursor_col > 0:
            n = prev_word_offset(text, self.cursor_col) if word else 1
            self.update_cursor(self.cursor_row, self.cursor_col - n)
        elif self.cursor_row > 0:
            self.update_cursor(self.cursor_row - 1, len(self.rows[self.cursor_row - 1]))

    def handle_right(self, word=False):
        text = self.rows[self.cursor_row]
        if self.cursor_col < len(text):
            n = next_word_offset(text, self.cursor_col) if word else 1
            self.update_cursor(self.cursor_row, self.cursor_col + n)
        elif self.cursor_row < len(self.rows) - 1:
            self.update_cursor(self.cursor_row + 1, 0)

    def handle_up(self):
        if self.cursor_row > 0:
            col = min(self.cursor_col, len(self.rows[self.cursor_row - 1]))
            self.update_cursor(self.cursor_row - 1, col)

    def handle_down(self):
        if self.cursor_row < len(self.rows) - 1:
            col = min(self.cursor_col, len(self.rows[self.cursor_row + 1]))
            self.update_cursor(self.cursor_row + 1, col)

    def handle_home(self, ctrl_mod=False):
        self.update_cursor(0 if ctrl_mod else self.cursor_row, 0)

    def handle_end(self, ctrl_mod=False):
        row = (len(self.rows) - 1) if ctrl_mod else self.cursor_row
        self.update_cursor(row, len(self.rows[row]))

    def handle_enter(self, ctrl_mod=False):
        if ctrl_mod:
            if self.commit_cb:
                self.commit_cb()
        else:
            text = self.rows[self.cursor_row]
            self.rows[self.cursor_row] = text[:self.cursor_col]
            self.rows.insert(self.cursor_row + 1, text[self.cursor_col:])
            self.text_updated()
            self.update_cursor(self.cursor_row + 1, 0)

    def handle_char(self, char):
        text = self.rows[self.cursor_row]
        self.rows[self.cursor_row] = text[:self.cursor_col] + char + text[self.cursor_col:]
        self.text_updated()
        self.update_cursor(self.cursor_row, self.cursor_col + 1)

    def handle_keydown(self, event, keystroke):
        ctrl_mod = 'CTRL-' in keystroke
        if ctrl_mod:
            keystroke = keystroke.replace('CTRL-', '')
        if keystroke == 'backspace':
            self.handle_backspace(ctrl_mod)
        elif keystroke == 'delete':
            self.handle_delete(ctrl_mod)
        elif keystroke in ['return', 'KP-enter']:
            self.handle_enter(ctrl_mod)
        elif keystroke == 'left':
            self.handle_left(ctrl_mod)
        elif keystroke == 'right':
            self.handle_right(ctrl_mod)
        elif keystroke == 'up' and not ctrl_mod:
            self.handle_up()
        elif keystroke == 'down' and not ctrl_mod:
            self.handle_down()
        elif keystroke == 'home':
            self.handle_home(ctrl_mod)
        elif keystroke == 'end':
            self.handle_end(ctrl_mod)
        elif ('ALT-' not in keystroke
              and not ctrl_mod
              and event.unicode and 32 <= ord(event.unicode) <= 126):
            self.handle_char(event.unicode)
        else:
            return False
        self.show_cursor()
        return True

    def cursor_rect(self):
        x = self.cursor_col * self.char_width
        y = self.cursor_row * self.char_height
        return pygame.Rect(x, y, self.char_width, self.char_height)

    def update_viewport(self):
        if self.viewport:
            self.parent.ensure_visible(self.cursor_rect())

    def finalise_layout(self):
        super().finalise_layout()
        self.update_viewport()

    def handle_mouse_down(self, button, pos):
        if button == 'left':
            x, y = pos
            row = min(y // self.char_height, len(self.rows) - 1)
            col = min(x // self.char_width, len(self.rows[row]))
            self.update_cursor(row, col)
            self.show_cursor()
            self.focus()
            return True

    def draw(self):
        super().draw()
        left, top = self.viewport.topleft
        bottom = self.viewport.bottom
        for i, line in enumerate(self.rows):
            y = i * self.char_height
            if (top - self.char_height) < y < bottom:
                if self.highlight_cb:
                    blocks = []
                    for text, color in self.highlight_cb(line):
                        blocks.append(self.render_text(text, color=color))
                else:
                    blocks = [self.render_text(line)]
                x = -left
                for block in blocks:
                    self.surface.blit(block, (x, y - top))
                    x += block.get_width()
        if self.draw_cursor:
            rect = self.cursor_rect().move(-left, -top)
            if self.cursor_col < len(self.rows[self.cursor_row]):
                char = self.rows[self.cursor_row][self.cursor_col]
                text_color = 'black' # XXX choose me
                text = self.render_text(char, color=text_color, bgcolor=self.color)
                self.surface.blit(text, rect)
            else:
                pygame.draw.rect(self.surface, self.color, rect)


class TextArea(ScrollArea):
    halign = 'fill'
    valign = 'fill'

    bottom_bar = True
    right_bar = True

    border_color = (96, 96, 96)
    focus_border_color = (160, 160, 160)
    margin = 3

    num_cols = 80
    num_rows = 24

    def __init__(self, text='', update_cb=None, commit_cb=None, highlight_cb=None, **kwargs):
        body = TextAreaBody(text, update_cb, commit_cb, highlight_cb)
        super().__init__(body, **kwargs)

    def max_contents_width(self):
        return self.num_cols * self.body.char_width

    def max_contents_height(self):
        return self.num_rows * self.body.char_height

    def get_value(self):
        return self.body.get_value()

    def set_value(self, text):
        self.body.set_value(text)

    def focus(self):
        self.body.focus()

    def draw(self):
        self.body.color = self.color
        super().draw()
        if self.enabled:
            color = self.focus_border_color if self.has_focus else self.border_color
            pygame.draw.rect(self.surface, color, self.surface.get_rect(), 1)
