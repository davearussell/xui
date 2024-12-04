import os

import pygame

DEBUG = os.environ.get('DEBUG')

UNLIMITED = (1 << 32) - 1

NEEDS_REDRAW = 1 << 0
NEEDS_LAYOUT = 1 << 1


def divide_space(total_space, min_sizes, max_sizes):
    if sum(max_sizes) <= total_space:
        return max_sizes

    remaining_space = total_space - sum(min_sizes)
    assert remaining_space >= 0
    if remaining_space == 0:
        return min_sizes

    sizes = list(min_sizes)
    elements = [(hi - lo, i) for i, (lo, hi) in enumerate(zip(min_sizes, max_sizes))]
    elements.sort() # sort by the amount element can grow by
    per_element, rem = divmod(remaining_space, len(elements))
    for gi, (headroom, i) in enumerate(elements):
        target_grow_by = per_element + (1 if (len(elements) - gi <= rem) else 0)
        grow_by = min(target_grow_by, headroom)
        sizes[i] += grow_by
        assert min_sizes[i] <= sizes[i] <= max_sizes[i]
        remaining_space -= grow_by
        if grow_by < target_grow_by:
            per_element, rem = divmod(remaining_space, len(elements) - gi - 1)

    assert sum(sizes) == total_space
    return sizes


class LayoutError(Exception):
    pass

class Widget:
    fixed_width = False
    fixed_height = False
    width = 0
    height = 0

    halign = None
    valign = None
    margin = 0
    spacing = 0

    color = None
    bgcolor = None

    def __init__(self, children=None, **kwargs):
        self.children = children or []
        self.parent = None
        self.depth = 0
        self.rect = pygame.Rect(0, 0, 0, 0)
        self.rel_rect = self.rect
        self.old_rect = self.rect
        self.flags = NEEDS_LAYOUT
        self.root = self
        for k, v in kwargs.items():
            if not hasattr(self, k):
                raise Exception("%s does not have attribute %r" % (type(self).__name__, k))
            setattr(self, k, v)

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
        return 2 * self.margin + self.max_contents_width()

    def min_height(self):
        if self.fixed_height:
            return self.height
        return 2 * self.margin + self.min_contents_height()

    def max_height(self):
        if self.fixed_height:
            return self.height
        return 2 * self.margin + self.max_contents_height()

    def size_updated(self, old_size, new_size):
        pass

    def resolve_tree(self, parent=None):
        self.parent = parent
        if parent:
            self.depth = parent.depth + 1
            self.root = parent.root
        for child in self.children:
            child.resolve_tree(self)

    def layout(self):
        self.log("%s%s: layout at %r, size %r)" % (
            '  ' * self.depth, type(self).__name__, self.rect.topleft, self.rect.size))
        contents_rect = self.rect.inflate(-2 * self.margin, -2 * self.margin)
        for child, child_rect in self.align_children(contents_rect):
            child.width = child_rect.width
            child.height = child_rect.height
            child.rect = child_rect
            child.rel_rect = child_rect.move(-self.rect.left, -self.rect.top)
            child.surface = self.surface.subsurface(child.rel_rect)
            child.layout()
        if self.rect != self.old_rect:
            if self.rect.size != self.old_rect.size:
                self.size_updated(self.old_rect.size, self.rect.size)
            self.old_rect = self.rect
            (self.parent or self).redraw()

        self.flags &= ~NEEDS_LAYOUT

    def align_children(self, rect):
        x, y = rect.topleft
        for child in self.children:
            child_width = min(child.max_width(), rect.width)
            xspace = rect.width - child_width
            halign = child.halign or self.halign
            xoff = xspace * (1 if halign == 'right' else 0.5 if halign == 'center' else 0)
            child_height = min(child.max_height(), rect.height)
            yspace = rect.height - child_height
            valign = child.valign or self.valign
            yoff = yspace * (1 if valign == 'bottom' else 0.5 if valign == 'center' else 0)
            yield child, pygame.Rect(x + xoff, y + yoff, child_width, child_height)

    def has_solid_bg(self):
        return self.bgcolor and pygame.Color(self.bgcolor).a == 255

    def redraw(self):
        widget = self
        # If a widget has a transparent background we cannt redraw it in
        # isolation; we must also redraw any ancestors that may be visible
        # behind it.
        while widget.parent and not widget.has_solid_bg():
            widget = widget.parent
        widget.flags |= NEEDS_REDRAW

    def relayout(self):
        self.flags |= NEEDS_LAYOUT

    def draw(self):
        if self.bgcolor:
            self.surface.fill(self.bgcolor)
        for child in self.children:
            child.draw()
        self.flags &= ~NEEDS_REDRAW


class VBox(Widget):
    def min_contents_height(self):
        total_spacing = self.spacing * (len(self.children) - 1)
        return total_spacing + sum(child.min_height() for child in self.children)

    def max_contents_height(self):
        total_spacing = self.spacing * (len(self.children) - 1)
        return total_spacing + sum(child.max_height() for child in self.children)

    def align_children(self, rect):
        total_spacing = self.spacing * (len(self.children) - 1)
        min_heights = [child.min_height() for child in self.children]
        max_heights = [child.max_height() for child in self.children]
        heights = divide_space(rect.height - total_spacing, min_heights, max_heights)
        x, y = rect.topleft
        for child, child_height in zip(self.children, heights):
            child_width = min(child.max_width(), rect.width)
            xspace = rect.width - child_width
            halign = child.halign or self.halign
            xoff = xspace * (1 if halign == 'right' else 0.5 if halign == 'center' else 0)
            yield child, pygame.Rect(x + xoff, y, child_width, child_height)
            y += child_height + self.spacing


class HBox(Widget):
    def min_contents_width(self):
        total_spacing = self.spacing * (len(self.children) - 1)
        return total_spacing + sum(child.min_width() for child in self.children)

    def max_contents_width(self):
        total_spacing = self.spacing * (len(self.children) - 1)
        return total_spacing + sum(child.max_width() for child in self.children)

    def align_children(self, rect):
        total_spacing = self.spacing * (len(self.children) - 1)
        min_widths = [child.min_width() for child in self.children]
        max_widths = [child.max_width() for child in self.children]
        widths = divide_space(rect.width - total_spacing, min_widths, max_widths)
        x, y = rect.topleft
        for child, child_width in zip(self.children, widths):
            child_height = min(child.max_height(), rect.height)
            yspace = rect.height - child_height
            valign = child.valign or self.valign
            yoff = yspace * (1 if valign == 'right' else 0.5 if valign == 'center' else 0)
            yield child, pygame.Rect(x, y + yoff, child_width, child_height)
            x += child_width + self.spacing


class Stack(Widget):
    pass


class HSpacer(Widget):
    def max_width(self):
        return UNLIMITED

class VSpacer(Widget):
    def max_height(self):
        return UNLIMITED
