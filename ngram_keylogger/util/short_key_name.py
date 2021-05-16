# Copyright (c) 2021, see AUTHORS. Licensed under GPLv3+, see LICENSE.

import evdev

KEY_TO_CHARACTER = {
    evdev.ecodes.KEY_GRAVE: '~',
    evdev.ecodes.KEY_COMMA: ',',
    evdev.ecodes.KEY_DOT: '.',
    evdev.ecodes.KEY_SLASH: '/',
    evdev.ecodes.KEY_SEMICOLON: ';',
    evdev.ecodes.KEY_APOSTROPHE: "'",
    evdev.ecodes.KEY_LEFTBRACE: '[',
    evdev.ecodes.KEY_RIGHTBRACE: ']',
    evdev.ecodes.KEY_BACKSLASH: '\\',
    evdev.ecodes.KEY_MINUS: '-',
    evdev.ecodes.KEY_EQUAL: '=',
}


def short_key_name(key_code):
    if key_code in KEY_TO_CHARACTER:
        return KEY_TO_CHARACTER[key_code]
    s = evdev.ecodes.KEY[key_code]
    s = s[0] if isinstance(s, list) else s
    if s.startswith('KEY_'):
        s = s.replace('KEY_', '', 1)
    s = s.lower()
    return s
