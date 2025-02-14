from functools import partial

import pygame

from ..widget import Widget
from .layout import VBox
from .label import Label
from .scroll import ScrollArea


class Overlay(Widget):
    greedy_width = True
    greedy_height = True
    bgcolor = (0, 0, 0, 0)

    def __init__(self, dropdown):
        self.dropdown = dropdown
        super().__init__([dropdown])

    def hlayout(self):
        self.dropdown.set_width(self.dropdown.max_width())
        self.dropdown.hlayout()

    def vlayout(self):
        self.dropdown.set_height(self.dropdown.max_height())
        self.dropdown.vlayout()

    def resolve_tree(self, parent):
        super().resolve_tree(parent)
        def descendants(widget):
            yield widget
            for child in widget.children:
                yield from descendants(child)
        if self.dropdown.owner not in descendants(self.root):
            self.dropdown.close()

    def handle_mouse_down(self, button, pos):
        if not super().handle_mouse_down(button, pos):
            self.dropdown.close()
        return True


class DropdownBody(Widget):
    supports_viewport = True
    fixed_width = True
    fixed_height = True

    bgcolor = (0, 0, 0, 224)
    selected_color = (0, 0, 192, 224)
    double_click_period = 0.5

    margin = 5
    spacing = 0
    text_padding = 0

    def __init__(self, dropdown, update_cb, commit_cb):
        self.dropdown = dropdown
        self.choices = []
        self.choice_i = None
        self.mouseover_i = None
        self.update_cb = update_cb
        self.commit_cb = commit_cb
        super().__init__()
        self.resolve_size()

    def settings_updated(self):
        self.resolve_size()

    def resolve_size(self):
        self.char_width, self.char_height = self.render_text(' ').get_size()
        self.width = 2 * self.margin
        self.height = 2 * self.margin
        if self.choices:
            self.width += self.char_width * (max(map(len, self.choices)) + 2 * self.text_padding)
            self.height += (self.char_height + self.spacing) * len(self.choices) - self.spacing
        self.relayout()

    def set_choice_i(self, i):
        self.choice_i = i
        if self.parent and self.choices:
            y = self.margin + (i or 0) * (self.char_height + self.spacing)
            choice_rect = pygame.Rect(0, y - self.spacing,
                                      self.width, self.char_height + 2 * self.spacing)
            self.parent.ensure_visible(choice_rect)
        self.redraw()

    def set_choices(self, choices, choice_i=None):
        self.choices = choices
        self.set_choice_i(choice_i)
        self.resolve_size()

    def pos_to_row(self, pos):
        x, y = pos
        row_height = self.char_height + self.spacing
        row_i, offset = divmod(y - self.margin, row_height)
        if offset < self.char_height and 0 <= row_i < len(self.choices):
            return row_i
        return None

    def handle_mouse_down(self, button, pos):
        if button != 'left':
            return False
        row_i = self.pos_to_row(pos)
        if row_i is None:
            return False
        self.set_choice_i(row_i)
        if self.commit_cb:
            self.commit_cb(row_i)
        return True

    def set_mouseover_i(self, i):
        if i != self.mouseover_i:
            self.mouseover_i = i
            self.redraw()

    def handle_mouse_move(self, pos):
        row_i = self.pos_to_row(pos)
        if row_i is not None:
            self.set_mouseover_i(row_i)

    def handle_keydown(self, event, keystroke):
        if keystroke in ['up', 'down']:
            if self.choices:
                choice_i = self.mouseover_i if self.mouseover_i else self.choice_i
                self.set_mouseover_i(None)
                if choice_i is None:
                    choice_i = (len(self.choices) - 1) if keystroke == 'up' else 0
                else:
                    choice_i = (choice_i + (-1 if keystroke == 'up' else 1)) % len(self.choices)
                self.set_choice_i(choice_i)
                if self.update_cb:
                    self.update_cb(choice_i)
            return True
        elif keystroke in ['return', 'KP-enter'] and self.choice_i is not None:
            self.commit_cb(self.choice_i)
            return True
        return self.dropdown.owner

    def draw(self):
        super().draw()
        top = self.viewport.top
        bottom = self.viewport.bottom
        x = y = self.margin
        highlight_i = self.choice_i if self.mouseover_i is None else self.mouseover_i
        for i, choice in enumerate(self.choices):
            if y >= bottom:
                break
            if (y + self.char_height) > top:
                if i == highlight_i:
                    rect = pygame.Rect(0, y - top, self.width, self.char_height)
                    pygame.draw.rect(self.surface, self.selected_color, rect)
                pad = ' ' * self.text_padding
                self.surface.blit(self.render_text(pad + choice + pad), (x, y - top))
            y += self.char_height + self.spacing


class Dropdown(ScrollArea):
    border_thickness = 1
    text_padding = 0
    bar_thickness = 10
    right_bar = True

    max_choices = 10

    def __init__(self, owner, choices=None, choice_i=None, update_cb=None, commit_cb=None, **kwargs):
        self.owner = owner
        self.overlay = Overlay(self)
        self.commit_cb = commit_cb
        self.body = DropdownBody(self, update_cb, self._commit_cb)
        self.active = False
        if choices:
            self.body.set_choices(choices)
        if choice_i is not None:
            self.body.set_choice_i(choice_i)
        super().__init__(self.body, **kwargs)
        self.body.text_padding = self.text_padding
        self.body.resolve_size()

    def max_contents_height(self):
        limit = (self.body.char_height + self.body.spacing) * self.max_choices
        return min(limit, self.body.max_height())

    def set_choices(self, choices):
        self.body.set_choices(choices)

    def set_choice_i(self, i):
        self.body.set_choice_i(i)

    @property
    def choices(self):
        return self.body.choices

    @property
    def choice_i(self):
        return self.body.choice_i

    @property
    def choice(self):
        if self.body.choice_i is None:
            return None
        return self.body.choices[self.body.choice_i]

    def focus(self):
        self._old_focus = self.body.root.focus_widget
        self.body.focus()

    def handle_keydown(self, event, keystroke):
        return self.body.handle_keydown(event, keystroke)

    def open(self):
        self.x, self.y = self.owner.rect.bottomleft
        self.owner.root.children.append(self.overlay)
        self.owner.root.relayout()
        self.body.root = self.owner.root # lets owner call self.focus() pre-layout, if desired
        self.active = True

    def close(self):
        if self.body.has_focus:
            self.body.unfocus()
            if self._old_focus:
                self._old_focus.focus()
        assert self.root.children.pop() is self.overlay
        self.root.relayout()
        self.active = False

    def _commit_cb(self, choice_i):
        assert self.active
        self.close()
        if self.commit_cb:
            self.commit_cb(choice_i)
