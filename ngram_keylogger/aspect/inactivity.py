# Copyright (c) 2021, see AUTHORS. Licensed under GPLv3+, see LICENSE.

async def inactivity(event_and_extras_gen, timeout):
    prev_event_time = None
    async for event, extras in event_and_extras_gen:
        inactivity = (not prev_event_time
                      or event.timestamp() - prev_event_time > timeout)
        yield event, {**extras, 'after_inactivity': inactivity}
        prev_event_time = event.timestamp()
