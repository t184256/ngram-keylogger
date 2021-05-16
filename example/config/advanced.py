# Advanced config showing some of the features ngram-keylogger offers

import ngram_keylogger


REST_DURATION = 2  # seconds. Waiting longer than that breaks up n-grams.
PROMPTERS = ['i3lock', 'swaylock', 'pinentry', 'screensaver']
PROMPTERS_RESCAN = 5

CUSTOM_REPLACEMENT_TABLE = {
    'alt-meta-q': 'workspace-1',  # example replacement
    'alt-meta-x': 'workspace-2',  # example ignoring
}


def detect_prompters(p):
    for s in PROMPTERS:
        if s in p.name():
            return p.name()


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
            yield ngram_keylogger.NOTHING, None
        repeat = extras['repeat']
        active_modifiers_prefix = extras['active_modifiers_prefix']

        short = ngram_keylogger.util.short_key_name(event.code)
        short = active_modifiers_prefix + short
        yield short + ('+' if repeat else ''), None


action_generator = ngram_keylogger.filter.apply_filters(action_generator_, [
    ngram_keylogger.filter.shift_printables,
    ngram_keylogger.filter.abbreviate_controls,
    ngram_keylogger.filter.make_replace(CUSTOM_REPLACEMENT_TABLE),
    ngram_keylogger.filter.make_process_scan(detect_prompters,
                                             PROMPTERS_RESCAN),
])
