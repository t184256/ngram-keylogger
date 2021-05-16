# Example config that t184256 uses

import ngram_keylogger


REST_DURATION = 2  # seconds. Waiting longer than that breaks up n-grams.

CUSTOM_REPLACEMENT_TABLE = {
    'alt-meta-q': 'workspace-1',
    'alt-meta-w': 'workspace-2',
    'alt-meta-f': 'workspace-3',
    'alt-meta-p': 'workspace-4',
    'alt-meta-g': 'workspace-5',
    'alt-meta-y': 'window-move-to',
    'shift-backspace': 'backspace',  # keyboard firmware bug
    'alt-meta-f11': None,  # used to light up a meta mode indicator
    'alt-meta-f12': None,  # used to light up a meta mode indicator
}


async def action_generator_(event_and_extras_gen):
    """
    Converts evdev events to sequences of actions like
    'a', 'Y', '.', '&', 'control-shift-c', 'Left+' or 'close window'.
    """
    gen = event_and_extras_gen
    gen = ngram_keylogger.aspect.keys_only(gen)
    gen = ngram_keylogger.aspect.inactivity(gen, timeout=REST_DURATION)
    gen = ngram_keylogger.aspect.modifiers(gen)
    gen = ngram_keylogger.aspect.repeating(gen)

    async for event, extras in gen:
        if extras['after_inactivity']:
            # click.echo('-flush-')
            for i in range(3):
                yield ngram_keylogger.NOTHING
        repeat = extras['repeat']
        active_modifiers_prefix = extras['active_modifiers_prefix']

        short = ngram_keylogger.util.short_key_name(event.code)
        short = active_modifiers_prefix + short
        yield short + ('+' if repeat else '')


action_generator = ngram_keylogger.filter.apply_filters(action_generator_, [
    ngram_keylogger.filter.t184256_russian,
    ngram_keylogger.filter.shift_printables,
    ngram_keylogger.filter.abbreviate_controls,
    ngram_keylogger.filter.make_replace(CUSTOM_REPLACEMENT_TABLE),
])
