# Minimal ngram-keylogger config

import ngram_keylogger


async def action_generator(event_and_extras_gen):
    gen = ngram_keylogger.aspect.keys_only(event_and_extras_gen)
    async for event, extras in gen:
        yield ngram_keylogger.util.short_key_name(event.code), None
