# Copyright (c) 2021, see AUTHORS. Licensed under GPLv3+, see LICENSE.

import ngram_keylogger


def make_process_scan(func, throttle_sec):
    async def process_scan(gen):
        while True:
            async for action in gen:
                s = ngram_keylogger.util.cached_process_scan(func,
                                                             throttle_sec)
                if s:
                    print(f'detected process {s} temporarily suspends logging')
                else:
                    yield action
    return process_scan
