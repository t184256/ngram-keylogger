# Copyright (c) 2021, see AUTHORS. Licensed under GPLv3+, see LICENSE.

import evdev

MODIFIERS = {
    evdev.ecodes.KEY_LEFTCTRL: 'control',
    evdev.ecodes.KEY_LEFTALT: 'alt',
    evdev.ecodes.KEY_LEFTMETA: 'meta',
    evdev.ecodes.KEY_LEFTSHIFT: 'shift',
    evdev.ecodes.KEY_RIGHTCTRL: 'control',
    evdev.ecodes.KEY_RIGHTALT: 'alt',
    evdev.ecodes.KEY_RIGHTMETA: 'meta',
    evdev.ecodes.KEY_RIGHTSHIFT: 'shift',
}


async def modifiers(event_and_extras_gen):
    active_modifiers = set()
    active_modifiers_prefix = ''
    async for event, extras in event_and_extras_gen:
        if event.code in MODIFIERS:
            if event.value:
                active_modifiers.add(event.code)
            elif event.code in active_modifiers:
                active_modifiers.remove(event.code)
            active_modifiers_prefix = ''.join(f'{m}-'
                                              for c, m in MODIFIERS.items()
                                              if c in active_modifiers)
            continue
        yield event, {**extras,
                      'active_modifiers': active_modifiers,
                      'active_modifiers_prefix': active_modifiers_prefix}
