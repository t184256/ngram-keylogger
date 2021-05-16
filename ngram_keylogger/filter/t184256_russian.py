# Copyright (c) 2021, see AUTHORS. Licensed under GPLv3+, see LICENSE.

# ru-prefixed
QWERTY = "~qwertyuiop[]asdfghjkl;zxcvbnm,.'"
JCUKEN = 'ёйцукенгшщзхъфывапролджячсмитьбюэ'
JCUKEN_SHIFT = 'ЁЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЯЧСМИТЬБЮЭ'
RUSSIAN_MAP = {en: f'ru-{ru}' for en, ru in zip(QWERTY, JCUKEN)}
RUSSIAN_MAP.update({f'shift-{en}': f'ru-{ru}' for en, ru in zip(QWERTY,
                                                                JCUKEN_SHIFT)})

# non-ru-prefixed
QWERTY_ = '1234567890/'
JCUKEN_ = '1234567890.'
JCUKEN_SHIFT_ = '!"№;%:?*(),'
RUSSIAN_MAP.update({en: ru for en, ru in zip(QWERTY_, JCUKEN_)})
RUSSIAN_MAP.update({f'shift-{en}': ru for en, ru in zip(QWERTY_,
                                                        JCUKEN_SHIFT_)})


async def t184256_russian(gen):
    # FIXME: doesn't work with repeats
    while True:
        # normal operation
        async for action, context in gen:
            if action not in ('control-compose', 'control-shift-compose'):
                yield action, context  # normal operation
            else:
                break  # to russian handling
        # russian
        async for action, context in gen:
            if action in RUSSIAN_MAP:
                yield RUSSIAN_MAP[action], context
                break  # to normal handling
            elif f'{action}+' in RUSSIAN_MAP:
                yield RUSSIAN_MAP[action[:-1]] + '+', context
                break  # to normal handling
