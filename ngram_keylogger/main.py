#!/usr/bin/env python
# Copyright (c) 2021, see AUTHORS. Licensed under GPLv3+, see LICENSE.

"""
n-gram keylogger: typing stats that don't leak passwords

Uses evdev to read the device files directly,
and thus requires appropriate permissions.
"""

import asyncio
import collections
import os
import signal
import sqlite3

import click
import evdev

import ngram_keylogger


REST_DURATION = 2  # seconds. Waiting longer than that breaks up n-grams.
SAVE_MAX = 3000    # actions. Protects against differential DB analysis.
SAVE_MIN = 300     # actions. On exit you might not have enough; discards them.
NOTHING = '...'

DBPATH = '/var/lib/ngram-keylogger/db.sqlite'



# action generator (TODO: move to config)


CUSTOM_REPLACEMENT_TABLE = {
    'alt-meta-q': 'workspace-1',
    'alt-meta-w': 'workspace-2',
    'alt-meta-f': 'workspace-3',
    'alt-meta-p': 'workspace-4',
    'alt-meta-g': 'workspace-5',
    'alt-meta-y': 'window-move-to',
    'shift-backspace': 'backspace',  # keyboard firmware bug
    'alt-meta-f11': None,  # used to light up a meta mode indicator
    'alt-meta-f12': None,  # used to light up a meta mode indicator
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
            # click.echo('-flush-')
            for i in range(3):
                yield NOTHING
        repeat = context['repeat']
        active_modifiers_prefix = context['active_modifiers_prefix']

        short = ngram_keylogger.util.short_key_name(event.code)
        short = active_modifiers_prefix + short
        yield short + ('+' if repeat else '')


action_generator = ngram_keylogger.filter.apply_filters(action_generator_, [
    ngram_keylogger.filter.t184256_russian,
    ngram_keylogger.filter.shift_printables,
    ngram_keylogger.filter.abbreviate_controls,
    ngram_keylogger.filter.make_replace(CUSTOM_REPLACEMENT_TABLE),
])


# Stats database

class StatsDB:
    """
    Collects and stores statictics in memory,
    saves it to disk from time to time (see SAVE_MIN, SAVE_MAX).

    Operates on N-grams of actions
    When you type 'hi' after a break and rest again,
    it's gonna (eventually) translate to:
      * keys: +1 to 'h' and 'i'
      * bigrams: +1 to ('...', 'h'), ('h', 'i') and ('i', '...')
      * trigrams: +1 to ('...', '...', 'h'), ('...', 'h', 'i'),
                        ('h', 'i', '...') and ('i', '...', '...')
    That might mean some filtering during the analysis,
    but better have that data than not have it.
    """
    def __init__(self):
        click.echo(f'Checking database {DBPATH}...')
        os.makedirs(os.path.dirname(DBPATH), exist_ok=True)
        with sqlite3.connect(DBPATH) as con:
            for n, table in ((1, 'keys'), (2, 'bigrams'), (3, 'trigrams')):
                a_column_names = ', '.join(f'a{i + 1}' for i in range(n))
                a_column_defs = ', '.join(f'a{i + 1} TEXT NOT NULL'
                                          for i in range(n))
                con.execute(f'CREATE TABLE IF NOT EXISTS {table} '
                            f'(count INT NOT NULL, {a_column_defs}, '
                            f' PRIMARY KEY ({a_column_names}))')
        click.echo(f'Database {DBPATH} is OK.')
        self._latest_actions = [NOTHING] * 3
        self._in_memory_counters = [collections.Counter() for i in range(3)]
        self._unsaved_actions = 0

    def flush_pipeline(self):
        """ Called when inactivity is detected. """
        for _ in range(3):
            self.account_for_action(NOTHING)

    def account_for_action(self, action):
        self._latest_actions.pop(0)
        self._latest_actions.append(action)
        for n in range(3):
            self.account_for_ngram(self._latest_actions[-n:])
        self._unsaved_actions += 1
        if SAVE_MAX <= self._unsaved_actions:
            self.save_to_disk()

    def account_for_ngram(self, ngram):
        if not all(e == NOTHING for e in ngram):
            counter = self._in_memory_counters[len(ngram) - 1]
            counter[tuple(ngram)] += 1

    def save_to_disk(self):
        if not self._unsaved_actions:
            return
        if self._unsaved_actions < SAVE_MIN:
            click.echo(f'Refusing to save {self._unsaved_actions} '
                       f'< {SAVE_MIN} actions to disk.')
            return
        click.echo(f'Saving {self._unsaved_actions} actions to disk...')
        with sqlite3.connect(DBPATH) as con:
            for n, table in ((1, 'keys'), (2, 'bigrams'), (3, 'trigrams')):
                a_column_names = ', '.join(f'a{i + 1}' for i in range(n))
                question_marks = ', '.join(('?',) * n)
                q = (f'INSERT INTO {table} ({a_column_names}, count) '
                     f'VALUES ({question_marks}, ?) '
                     f'ON CONFLICT ({a_column_names}) DO UPDATE '
                     'SET count = count + ? '
                     f'WHERE ({a_column_names}) == ({question_marks})')
                for ngram, count in self._in_memory_counters[n - 1].items():
                    con.execute(q, ngram + (count, count) + ngram)
        self._unsaved_actions = 0
        self._in_memory_counters = [collections.Counter() for i in range(3)]
        click.echo('Saved.')


# CLI & main

@click.group(help=__doc__)
def cli():
    pass


@cli.command()
@click.argument('device_path', nargs=-1, required=True,
                type=click.Path(readable=True))
def collect(device_path):
    """ Collects keystrokes, saves them to disk. """

    statsdb = StatsDB()
    event_and_context_queue = asyncio.Queue()

    async def shutdown(sig, loop):
        click.echo(f'Caught {sig.name}')
        click.echo('Stopping keystroke collection...')
        for task in asyncio.all_tasks():
            if task is not asyncio.current_task():
                task.cancel()
        click.echo('Flushing statistics...')
        statsdb.save_to_disk()
        click.echo('Stopping...')
        await event_and_context_queue.join()
        loop.stop()

    async def collect_events(device_path):
        click.echo(f'Opening device {device_path}...')
        device = evdev.InputDevice(device_path)
        click.echo(f'Opened device {device_path}.')
        async for event in device.async_read_loop():
            # click.echo(evdev.categorize(event), sep=': ')
            await event_and_context_queue.put((event, {}))

    async def unwind_queue(event_and_context_queue):
        while True:
            event, context = await event_and_context_queue.get()
            yield event, context

    for device in device_path:
        asyncio.ensure_future(collect_events(device))

    loop = asyncio.get_event_loop()
    for sig in signal.SIGINT, signal.SIGTERM, signal.SIGHUP:
        loop.add_signal_handler(sig, lambda sig=sig:
                                asyncio.create_task(shutdown(sig, loop)))

    async def process_actions():
        async for a in action_generator(unwind_queue(event_and_context_queue)):
            statsdb.account_for_action(a)
    try:
        loop.run_until_complete(process_actions())
    except asyncio.exceptions.CancelledError:
        print('Stopped.')


if __name__ == '__main__':
    cli()
