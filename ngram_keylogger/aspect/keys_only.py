# Copyright (c) 2021, see AUTHORS. Licensed under GPLv3+, see LICENSE.

import evdev


async def keys_only(event_and_extras_gen):
    async for event, extras in event_and_extras_gen:
        if event.type == evdev.ecodes.EV_KEY:
            yield event, extras
