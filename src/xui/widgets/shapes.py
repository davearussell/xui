import pygame

from ..widget import Widget


class HBar(Widget):
    halign = 'fill'
    fixed_height = True
    height = 20
    bar_height = 3
    margin = 5
    color = 'white'

    @property
    def bar_width(self):
        return self.width - 2 * self.margin

    def draw(self):
        super().draw()
        rect = pygame.Rect(self.margin, 0, self.width - 2 * self.margin, self.bar_height)
        rect.centery = self.height // 2
        pygame.draw.rect(self.surface, self.color, rect)


class VBar(Widget):
    valign = 'fill'
    fixed_width = True
    width = 20
    bar_width = 3
    margin = 5
    color = 'white'

    @property
    def bar_height(self):
        return self.height - 2 * self.margin

    def draw(self):
        super().draw()
        rect = pygame.Rect(0, self.margin, self.bar_width, self.height - 2 * self.margin)
        rect.centerx = self.width // 2
        pygame.draw.rect(self.surface, self.color, rect)


class Square(Widget):
    fixed_width = True
    fixed_height = True
    side_length = 10

    @property
    def width(self):
        return self.side_length

    @property
    def height(self):
        return self.side_length
