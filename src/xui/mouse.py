import pygame.locals

MOUSE_BUTTONS = {
    pygame.locals.BUTTON_LEFT: 'left',
    pygame.locals.BUTTON_MIDDLE: 'middle',
    pygame.locals.BUTTON_RIGHT: 'right',
    pygame.locals.BUTTON_WHEELUP: 'wheelup',
    pygame.locals.BUTTON_WHEELDOWN: 'wheeldown',
    pygame.locals.BUTTON_X1: 'x1',
    pygame.locals.BUTTON_X2: 'x2',
}

def event_button(event):
    return MOUSE_BUTTONS.get(event.button, 'unknown')
