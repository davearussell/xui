import os

import pygame

DEBUG = os.environ.get('DEBUG')

UNLIMITED = (1 << 32) - 1


class LayoutError(Exception):
    pass

class Widget:
    fixed_width = False
    fixed_height = False

    greedy_width = False
    greedy_height = False
    width = 0
    height = 0

    halign = None
    valign = None
    child_halign = None
    child_valign = None
    margin = 0
    spacing = 0

    color = 'white'
    bgcolor = None

    def __init__(self, children=None, **kwargs):
        self.children = children or []
        self.parent = None
        self.depth = 0
        self.x = 0
        self.y = 0
        self.rect = pygame.Rect(0, 0, 0, 0)
        self.rel_rect = self.rect
        self.surface = None
        self._laid_out = None
        self._redraw = True
        self.root = self
        for k, v in kwargs.items():
            if not hasattr(self, k):
                raise Exception("%s does not have attribute %r" % (type(self).__name__, k))
            setattr(self, k, v)
        self.has_focus = False

    @property
    def size(self):
        return self.width, self.height

    @size.setter
    def size(self, size):
        self.width, self.height = size

    def error(self, msg, *args):
        raise LayoutError("%s: %s" % (type(self).__name__, msg % args))

    def log(self, msg):
        if DEBUG:
            print(msg)

    def __repr__(self):
        return "%s at %r" % (type(self).__name__, self.rect)

    def focus(self):
        self.log("Focus %r" % (self,))
        old_focus = self.root.focus_widget
        if old_focus is self:
            return
        self.root.focus_widget = self
        if old_focus:
            old_focus.has_focus = False
            old_focus.focus_lost()
        self.has_focus = True
        self.focus_gained()
        self.redraw()

    def unfocus(self):
        self.log("Unfocus %r" % (self,))
        assert self.root.focus_widget is self
        self.root.focus_widget = None
        self.has_focus = False
        self.focus_lost()
        self.redraw()

    def focus_gained(self):
        pass

    def focus_lost(self):
        pass

    def min_contents_width(self):
        return max(child.min_width() for child in self.children) if self.children else 0

    def max_contents_width(self):
        return max(child.max_width() for child in self.children) if self.children else 0

    def min_contents_height(self):
        return max(child.min_height() for child in self.children) if self.children else 0

    def max_contents_height(self):
        return max(child.max_height() for child in self.children) if self.children else 0

    def min_width(self):
        if self.fixed_width:
            return self.width
        return 2 * self.margin + self.min_contents_width()

    def max_width(self):
        if self.fixed_width:
            return self.width
        if self.greedy_width:
            return UNLIMITED
        return 2 * self.margin + self.max_contents_width()

    def min_height(self):
        if self.fixed_height:
            return self.height
        return 2 * self.margin + self.min_contents_height()

    def max_height(self):
        if self.fixed_height:
            return self.height
        if self.greedy_height:
            return UNLIMITED
        return 2 * self.margin + self.max_contents_height()

    def resolve_tree(self, parent=None):
        self.parent = parent
        if parent:
            self.depth = parent.depth + 1
            self.root = parent.root
        for child in self.children:
            child.resolve_tree(self)

    def width_updated(self):
        pass

    def height_updated(self):
        pass

    def set_width(self, width):
        if width != self.width:
            assert not self.fixed_width
            self.width = width
            self.width_updated()

    def set_height(self, height):
        if height != self.height:
            assert not self.fixed_height
            self.height = height
            self.height_updated()

    def hlayout(self):
        x = self.x + self.margin
        width = self.width - 2 * self.margin
        for child in self.children:
            lo, hi = child.min_width(), child.max_width()
            if lo > width:
                self.error("width=%d, margin=%d, child %s requires %d",
                           self.width, self.margin, type(child).__name__, lo)
            child.set_width(min(hi, width))
            gap = width - child.width
            align = child.halign or self.child_halign
            offset = gap * (1 if align == 'right' else 0.5 if align == 'center' else 0)
            child.x = x + offset
            child.hlayout()

    def vlayout(self):
        y = self.y + self.margin
        height = self.height - 2 * self.margin
        for child in self.children:
            lo, hi = child.min_height(), child.max_height()
            if lo > height:
                self.error("height=%d, margin=%d, child %s requires %d",
                           self.height, self.margin, type(child).__name__, lo)
            child.set_height(min(hi, height))
            gap = height - child.height
            align = child.valign or self.child_valign
            offset = gap * (1 if align == 'bottom' else 0.5 if align == 'center' else 0)
            child.y = y + offset
            child.vlayout()

    def finalise_layout(self):
        old_rect = self.rect.copy()
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.log("%s%s: layout at %r, size %r)" % (
            '  ' * self.depth, type(self).__name__, self.rect.topleft, self.rect.size))
        if self.parent:
            self.rel_rect = self.rect.move(-self.parent.rect.left, -self.parent.rect.top)
        for child in self.children:
            child.finalise_layout()
        if self.rect != old_rect:
            (self.parent or self).redraw()
        self._laid_out = self.children.copy()

    def setup_surface(self):
        for child in self.children:
            child.surface = self.surface.subsurface(child.rel_rect)
            child.setup_surface()

    def redraw(self):
        self._redraw = True

    def relayout(self):
        self._laid_out = None

    def needs_layout(self):
        if self._laid_out != self.children:
            return True
        return any(child.needs_layout() for child in self.children)

    def to_redraw(self):
        if self._redraw:
            return [self]
        return [widget for child in self.children for widget in child.to_redraw()]

    def draw(self):
        if self.bgcolor:
            self.surface.fill(self.bgcolor)
        for child in self.children:
            child.draw()
        self._redraw = False
