import pygame

from . import widget

class Border(widget.Widget):
    margin = 5
    border_thickness = 1
    color = 'white'

    def draw(self):
        super().draw()
        if self.color:
            rect = self.surface.get_rect()
            pygame.draw.rect(self.surface, self.color, rect, self.border_thickness)
