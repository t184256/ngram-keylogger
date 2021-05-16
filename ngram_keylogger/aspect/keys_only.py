# Copyright (c) 2021, see AUTHORS. Licensed under GPLv3+, see LICENSE.

import evdev


async def keys_only(event_and_context_gen):
    async for event, context in event_and_context_gen:
        if event.type == evdev.ecodes.EV_KEY:
            yield event, context
