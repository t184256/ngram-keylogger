# Advanced config showing some of the features ngram-keylogger offers

import ngram_keylogger


REST_DURATION = 2  # seconds. Waiting longer than that breaks up n-grams.

CUSTOM_REPLACEMENT_TABLE = {
    'alt-meta-q': 'workspace-1',  # example replacement
    'alt-meta-x': 'workspace-2',  # example ignoring
}


async def action_generator_(event_and_context_gen):
    """
    Converts evdev events to sequences of actions like
    'a', 'Y', '.', '&', 'control-shift-c', 'Left+' or 'close window'.
    """
    gen = event_and_context_gen
    gen = ngram_keylogger.aspect.keys_only(gen)
    gen = ngram_keylogger.aspect.inactivity(gen, timeout=REST_DURATION)
    gen = ngram_keylogger.aspect.modifiers(gen)
    gen = ngram_keylogger.aspect.repeating(gen)

    async for event, context in gen:
        if context['after_inactivity']:
            for i in range(3):
                yield ngram_keylogger.NOTHING
        repeat = context['repeat']
        active_modifiers_prefix = context['active_modifiers_prefix']

        short = ngram_keylogger.util.short_key_name(event.code)
        short = active_modifiers_prefix + short
        yield short + ('+' if repeat else '')


action_generator = ngram_keylogger.filter.apply_filters(action_generator_, [
    ngram_keylogger.filter.shift_printables,
    ngram_keylogger.filter.abbreviate_controls,
    ngram_keylogger.filter.make_replace(CUSTOM_REPLACEMENT_TABLE),
])
