#!/usr/bin/env python
# Copyright (c) 2021, see AUTHORS. Licensed under GPLv3+, see LICENSE.

"""
n-gram keylogger: typing stats that don't leak passwords

Uses evdev to read the device files directly,
and thus requires appropriate permissions.
"""

import asyncio
import signal

import click
import evdev

import ngram_keylogger


DBPATH = '/var/lib/ngram-keylogger/db.sqlite'


# CLI & main

@click.group(help=__doc__)
def cli():
    pass


@cli.command()
@click.argument('device_path', nargs=-1, required=True,
                type=click.Path(readable=True))
@click.option('--config', default=ngram_keylogger.config.default_path(),
              type=click.Path(readable=True))
def collect(device_path, config):
    """ Collects keystrokes, saves them to disk. """
    config = ngram_keylogger.config.read(config)
    action_generator = config['action_generator']

    statsdb = ngram_keylogger.db.StatsDB(DBPATH)
    event_and_extras_queue = asyncio.Queue()

    async def shutdown(sig, loop):
        click.echo(f'Caught {sig.name}')
        click.echo('Stopping keystroke collection...')
        for task in asyncio.all_tasks():
            if task is not asyncio.current_task():
                task.cancel()
        click.echo('Flushing statistics...')
        statsdb.save_to_disk()
        click.echo('Stopping...')
        await event_and_extras_queue.join()
        loop.stop()

    async def collect_events(device_path):
        click.echo(f'Opening device {device_path}...')
        device = evdev.InputDevice(device_path)
        click.echo(f'Opened device {device_path}.')
        async for event in device.async_read_loop():
            # click.echo(evdev.categorize(event), sep=': ')
            await event_and_extras_queue.put((event, {}))

    async def unwind_queue(event_and_extras_queue):
        while True:
            event, extras = await event_and_extras_queue.get()
            yield event, extras

    for device in device_path:
        asyncio.ensure_future(collect_events(device))

    loop = asyncio.get_event_loop()
    for sig in signal.SIGINT, signal.SIGTERM, signal.SIGHUP:
        loop.add_signal_handler(sig, lambda sig=sig:
                                asyncio.create_task(shutdown(sig, loop)))

    async def process_actions():
        async for a in action_generator(unwind_queue(event_and_extras_queue)):
            statsdb.account_for_action(a)
    try:
        loop.run_until_complete(process_actions())
    except asyncio.exceptions.CancelledError:
        click.echo('Stopped.')


if __name__ == '__main__':
    cli()
