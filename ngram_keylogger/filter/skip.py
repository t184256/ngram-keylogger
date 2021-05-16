# Copyright (c) 2021, see AUTHORS. Licensed under GPLv3+, see LICENSE.

def make_skip(skip_collection):
    async def skip(gen):
        while True:
            async for action in gen:
                if action not in skip_collection:
                    yield action
    return skip
