# Copyright (c) 2021, see AUTHORS. Licensed under GPLv3+, see LICENSE.

async def repeating(event_and_extras_gen):
    active_repeating = set()
    async for event, extras in event_and_extras_gen:
        if event.value == 0:  # release
            if event.code in active_repeating:
                active_repeating.remove(event.code)
            continue
        repeat = event.value == 2
        if repeat and event.code in active_repeating:
            continue
        if repeat:
            active_repeating.add(event.code)
        yield event, {**extras,
                      'active_repeating': active_repeating, 'repeat': repeat}
