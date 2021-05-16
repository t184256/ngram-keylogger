# Copyright (c) 2021, see AUTHORS. Licensed under GPLv3+, see LICENSE.

import asyncio

from i3ipc.aio import Connection
from i3ipc import Event


async def get_current_window_title(i3):
    tree = await i3.get_tree()
    focused = tree.find_focused()
    return focused.name


async def monitor_window_title_changes(i3, window_title_queue):
    async def on_everything(i3, *_):
        tree = await i3.get_tree()
        focused = tree.find_focused()
        await window_title_queue.put(focused.name)

    i3.on(Event.WINDOW_TITLE, on_everything)
    i3.on(Event.WINDOW_FOCUS, on_everything)

    await i3.main()


async def current_window_titles():
    i3 = await Connection().connect()

    window_title_queue = asyncio.Queue()
    coro = monitor_window_title_changes(i3, window_title_queue)
    asyncio.run_coroutine_threadsafe(coro, loop=asyncio.get_running_loop())

    window_title = await get_current_window_title(i3)

    while True:
        try:
            window_title = window_title_queue.get_nowait()
            yield window_title
            window_title_queue.task_done()
        except asyncio.QueueEmpty:
            yield window_title
