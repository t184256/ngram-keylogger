# Copyright (c) 2021, see AUTHORS. Licensed under GPLv3+, see LICENSE.


QWERTY = "`QWERTYUIOP{}ASDFGHJKL:ZXCVBNM<>~qwertyuiop[]asdfghjkl;zxcvbmn,.'\""
JCUKEN = "ЁЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЯЧСМИТЬБЮёйцукенгшщзхъфывапролджячсмитьбюэЭ"
RUSSIAN_MAP = {en: f'ru-{ru}' for en, ru in zip(QWERTY, JCUKEN)}
RUSSIAN_MAP.update({en: ru for en, ru in zip('!@#$%^&*()/\\',
                                             '!"№;%:?*().,')})


async def t184256_russian(gen):
    # FIXME: doesn't work with repeats
    while True:
        # normal operation
        async for action in gen:
            if action not in ('control-compose', 'control-shift-compose'):
                yield action  # normal operation
            else:
                break  # to russian handling
        # russian
        async for action in gen:
            if action in RUSSIAN_MAP:
                yield RUSSIAN_MAP[action]
                break  # to normal handling
            elif f'{action}+' in RUSSIAN_MAP:
                yield RUSSIAN_MAP[action[:-1]] + '+'
                break  # to normal handling
