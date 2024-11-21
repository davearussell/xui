import pygame.key

MOD_LABELS = [
    (pygame.KMOD_CTRL, 'CTRL'),
    (pygame.KMOD_ALT, 'ALT'),
    (pygame.KMOD_SHIFT, 'SHIFT'),
]

KP_MAP = {'[' + s + ']': s for s in '0123456789/.-+*'}
KP_MAP['enter'] = 'enter'

MOD_KEYS = ['left ctrl', 'left shift', 'left alt',
            'right ctrl', 'right shift', 'right alt',
            'left meta', 'right meta', '']

def event_keystroke(event):
    name = pygame.key.name(event.key)
    if name in MOD_KEYS:
        # Don't report modifer keydown; instead we report it as a modifier
        # if the user presses another key while the modifier key is down.
        return None
    mods = [label for (mask, label) in MOD_LABELS if event.mod & mask]
    if name in KP_MAP:
        name = KP_MAP[name]
        mods.append('KP')
    return '-'.join(mods + [name.replace(' ', '')])
