# Copyright (c) 2021, see AUTHORS. Licensed under GPLv3+, see LICENSE.

def make_replace(replacement_dict):
    async def replace(gen):
        while True:
            async for action in gen:
                if action not in replacement_dict:
                    yield action
                else:
                    repl = replacement_dict[action]
                    if repl is not None:
                        yield repl
    return replace


ALPHABET = 'abcdefghijklmnopqrstuvwxyz'
DIGITS, SHIFTED_DIGITS = '1234567890', '!@#$%^&*()'
PUNCTUATION, SHIFTED_PUNCTUATION = "~,./;'[]\\-=", r'`<>?:"{}|_+'
PRINTABLES = ALPHABET + DIGITS + PUNCTUATION
SHIFTED_PRINTABLES = ALPHABET.upper() + SHIFTED_DIGITS + SHIFTED_PUNCTUATION
assert len(PRINTABLES) == len(SHIFTED_PRINTABLES)
SHIFTED_REPLACEMENT_TABLE = {
    f'shift-{c}': shifted_c
    for c, shifted_c in zip(PRINTABLES, SHIFTED_PRINTABLES)
}
CONTROL_REPLACEMENT_TABLE = {f'control-{c}': f'^{c.upper()}' for c in ALPHABET}

shift_printables = make_replace(SHIFTED_REPLACEMENT_TABLE)
abbreviate_controls = make_replace(CONTROL_REPLACEMENT_TABLE)
