from functools import partial

from .layout import HBox
from .label import Label
from .button import DropdownButton
from .dropdown import Dropdown


class ComboBox(HBox):
    text_padding = 1

    def __init__(self, choices=None, choice_i=None, commit_cb=None, **kwargs):
        self.commit_cb = commit_cb
        self.label = Label(margin=3, border_thickness=1)
        self.button = DropdownButton(self.open_cb)
        super().__init__([self.label, self.button], **kwargs)
        self.dropdown = Dropdown(self, commit_cb=self.choice_updated, text_padding=self.text_padding)
        self.set_choices(choices, choice_i)

    def refresh_label(self):
        text = self.dropdown.choice or ''
        pad = ' ' * self.text_padding
        self.label.set_text(pad + text.ljust(self.n_chars) + pad)

    def set_choice_i(self, choice_i):
        self.dropdown.set_choice_i(choice_i)
        self.refresh_label()

    def set_choice(self, choice):
        self.set_choice_i(self.dropdown.choices.index(choice))

    def set_choices(self, choices, choice_i=None):
        self.n_chars = max(map(len, choices)) if choices else 0
        self.dropdown.set_choices(choices)
        if choices and choice_i is None:
            choice_i = 0
        self.set_choice_i(choice_i)

    def choice_updated(self, choice_i):
        self.refresh_label()
        if self.commit_cb:
            self.commit_cb(choice_i)

    def add_choice(self, choice):
        self.set_choices(self.choices + [choice], self.choice_i)

    def remove_choice(self, choice):
        choices = [c for c in self.dropdown.choices if c != choice]
        old_choice = self.dropdown.choice
        was_selected = choice == old_choice
        if was_selected:
            choice_i = None if not choices else min(self.dropdown.choice_i, len(choices) - 1)
        else:
            choice_i = choices.index(old_choice)
        self.set_choices(choices, choice_i)
        if was_selected:
            self.choice_updated(choice_i)

    @property
    def choice(self):
        return self.dropdown.choice

    @property
    def choice_i(self):
        return self.dropdown.choice_i

    @property
    def choices(self):
        return self.dropdown.choices

    def open_cb(self):
        self.dropdown.open()
        self.dropdown.focus()

    def resolve_tree(self, parent):
        # We do this here as it is the first function called during layout
        self.button.height = self.button.width = self.label.min_height()
        super().resolve_tree(parent)

    def set_enabled(self, enabled):
        super().set_enabled(enabled)
        self.button.set_enabled(enabled)
        self.label.set_enabled(enabled)
