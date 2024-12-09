import os

import pygame
from .mouse import MOUSE_BUTTONS

DEBUG = os.environ.get('DEBUG')

UNLIMITED = (1 << 32) - 1


class LayoutError(Exception):
    pass

class Widget:
    supports_viewport = False
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
    border_thickness = 0

    # Default settings (not all widgets use all of these)
    color = 'white'
    bgcolor = None
    highlight_color = 'yellow'
    disabled_color = 'grey'
    border_color = None
    font = 'Liberation Mono'
    font_size = 20


    def __init__(self, children=None, **kwargs):
        self.children = children or []
        self.parent = None
        self.depth = 0
        self.x = 0
        self.y = 0
        self.viewport = None
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
        self.mouse_in_children = set()
        self.mouse_down_child = {button: None for button in MOUSE_BUTTONS.values()}
        self.has_mouse_focus = False
        self.has_focus = False

    def _apply_settings(self, settings):
        relevant = {k: v for k, v in settings.items() if k.islower()}
        cls_name = type(self).__name__
        if cls_name in settings:
            relevant |= settings[cls_name]
        for k, v in relevant.items():
            if hasattr(self, k):
                setattr(self, k, v)

    def apply_settings(self, settings):
        self._apply_settings(settings)
        self.apply_child_settings(settings)
        self.settings_updated()

    def apply_child_settings(self, settings):
        for child in self.children:
            child.apply_settings(settings)

    def settings_updated(self):
        pass

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

    def call_later(self, delay, fn, *args, **kwargs):
        return self.root.app.call_later(delay, fn, *args, **kwargs)

    def cancel_call(self, token):
        self.root.app.cancel_call(token)

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

    def handle_keydown(self, event, keystroke):
        return False

    def mouse_rel_pos(self, pos):
        if pos is None:
            return None

        if self.viewport:
            rect = pygame.Rect(self.rel_rect.left, self.rel_rect.top,
                               self.viewport.width, self.viewport.height)
            xoff, yoff = self.viewport.topleft
        else:
            rect = self.rel_rect
            xoff = yoff = 0

        if not rect.collidepoint(pos):
            return None

        x = pos[0] - self.rel_rect.left
        y = pos[1] - self.rel_rect.top
        return pos[0] - rect.left + xoff, pos[1] - rect.top + yoff

    def handle_mouse_down(self, button, pos):
        # Iter children in reverse. For most containers, order is not
        # important as children cannot overlap. For Stacks, we want the
        # frontmost child to have priority on handling the click.
        for child in self.children[::-1]:
            rel_pos = child.mouse_rel_pos(pos)
            if rel_pos and child.handle_mouse_down(button, rel_pos):
                self.mouse_down_child[button] = child
                return True
        return False

    def handle_mouse_up(self, button, pos):
        child = self.mouse_down_child[button]
        self.mouse_down_child[button] = None
        if child:
            rel_pos = child.mouse_rel_pos(pos)
            child.handle_mouse_up(button, rel_pos)

    def handle_mouse_move(self, pos):
        old = self.mouse_in_children
        new = set()
        for child in self.children:
            rel_pos = child.mouse_rel_pos(pos)
            if rel_pos:
                new.add(child)
                if child not in old:
                    child.handle_mouse_enter()
                child.handle_mouse_move(rel_pos)
            elif child in old:
                child.handle_mouse_exit()
        self.mouse_in_children = new

    def handle_mouse_enter(self):
        self.has_mouse_focus = True

    def handle_mouse_exit(self):
        self.has_mouse_focus = False
        for child in self.mouse_in_children:
            child.handle_mouse_exit()
        self.mouse_in_children = set()

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
            if child.halign == 'fill':
                hi = width
            child.set_width(min(hi, width))
            gap = width - child.width
            align = child.halign or self.child_halign
            if align == 'fixed':
                child.x = child.rect.left
            else:
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
            if child.valign == 'fill':
                hi = height
            child.set_height(min(hi, height))
            gap = height - child.height
            align = child.valign or self.child_valign
            if align == 'fixed':
                child.y = child.rect.top
            else:
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
            if child.viewport:
                if child.supports_viewport:
                    rect = child.rel_rect.copy()
                    rect.size = child.viewport.size
                    child.surface = self.surface.subsurface(rect)
                else:
                    child.surface = pygame.Surface(child.rect.size, pygame.SRCALPHA)
            else:
                child.surface = self.surface.subsurface(child.rel_rect)
            child.setup_surface()

    def redraw(self):
        self._redraw = True
        if self.viewport:
            self.parent.redraw()

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
        elif self.viewport and not self.supports_viewport:
            # In this mode we have our own surface so must clear previous contents before drawing
            self.surface.fill((0, 0, 0, 0))
        for child in self.children:
            child.draw()
            if child.viewport and not child.supports_viewport:
                self.surface.blit(child.surface, child.rel_rect, child.viewport)
        if self.border_thickness:
            rect = self.surface.get_rect()
            color = self.border_color or self.color
            pygame.draw.rect(self.surface, color, rect, self.border_thickness)
        self._redraw = False
