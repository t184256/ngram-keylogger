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

REST_DURATION = 2  # seconds. Waiting longer than that breaks up n-grams.
SAVE_MAX = 3000    # actions. Protects against differential DB analysis.
SAVE_MIN = 300     # actions. On exit you might not have enough; discards them.
NOTHING = '...'

DBPATH = '/var/lib/ngram-keylogger/db.sqlite'


# helpers for action generators

async def unwind_queue(event_and_context_queue):
    while True:
        event, context = await event_and_context_queue.get()
        #event_and_context_queue.task_done()  # TODO: do I need this?
        yield event, context


async def aspect_keys_only(event_and_context_queue):
    async for event, context in event_and_context_queue:
        if event.type == evdev.ecodes.EV_KEY:
            yield event, context


async def aspect_repeating(event_and_context_queue):
    active_repeating = set()
    async for event, context in event_and_context_queue:
        if event.value == 0:  # release
            if event.code in active_repeating:
                active_repeating.remove(event.code)
            continue
        repeat = event.value == 2
        if repeat and event.code in active_repeating:
            continue
        if repeat:
            active_repeating.add(event.code)
        yield event, {**context,
                      'active_repeating': active_repeating, 'repeat': repeat}


MODIFIERS = {
    evdev.ecodes.KEY_LEFTCTRL: 'Control',
    evdev.ecodes.KEY_LEFTALT: 'Alt',
    evdev.ecodes.KEY_LEFTMETA: 'Meta',
    evdev.ecodes.KEY_LEFTSHIFT: 'Shift',
    evdev.ecodes.KEY_RIGHTCTRL: 'Control',
    evdev.ecodes.KEY_RIGHTALT: 'Alt',
    evdev.ecodes.KEY_RIGHTMETA: 'Meta',
    evdev.ecodes.KEY_RIGHTSHIFT: 'Shift',
}


async def aspect_modifiers(event_and_context_queue):
    active_modifiers = set()
    active_modifiers_prefix = ''
    async for event, context in event_and_context_queue:
        if event.code in MODIFIERS:
            if event.value:
                active_modifiers.add(event.code)
            elif event.code in active_modifiers:
                active_modifiers.remove(event.code)
            active_modifiers_prefix = ''.join(f'{MODIFIERS[m]}-'
                                              for m in active_modifiers)
            continue
        yield event, {**context,
                      'active_modifiers': active_modifiers,
                      'active_modifiers_prefix': active_modifiers_prefix}


async def aspect_inactivity(event_and_context_queue, timeout):
    prev_event_time = None
    async for event, context in event_and_context_queue:
        inactivity = (not prev_event_time
                      or event.timestamp() - prev_event_time > timeout)
        yield event, {**context, 'after_inactivity': inactivity}
        prev_event_time = event.timestamp()


# action generator (TODO: move to config)


ALPHABET = 'abcdefghijklmnopqrstuvwxyz'
DIGITS, SHIFTED_DIGITS = '1234567890', '!@#$%^&*()'
PUNCTUATION, SHIFTED_PUNCTUATION = "~,./;'[]\\-=", r'`<>?:"{}|_+'
PRINTABLES = ALPHABET + DIGITS + PUNCTUATION
SHIFTED_PRINTABLES = ALPHABET.upper() + SHIFTED_DIGITS + SHIFTED_PUNCTUATION
assert len(PRINTABLES) == len(SHIFTED_PRINTABLES)
SHIFTED_REPLACEMENT_TABLE = {
    f'Shift-{c}': shifted_c
    for c, shifted_c in zip(PRINTABLES, SHIFTED_PRINTABLES)
}
CONTROL_REPLACEMENT_TABLE = {f'Control-{c}': f'^{c.upper()}' for c in ALPHABET}
CUSTOM_REPLACEMENT_TABLE = {
    'Alt-Meta-q': 'workspace-1',
    'Alt-Meta-w': 'workspace-2',
    'Alt-Meta-f': 'workspace-3',
    'Alt-Meta-p': 'workspace-4',
    'Alt-Meta-g': 'workspace-5',
    'Alt-Meta-y': 'window-move-to',
}
CUSTOM_SKIPLIST = {
    'Meta-Alt-f11',
    'Meta-Alt-f12',
}

#SINGLES = evdev.util.find_ecodes_by_regex(r'KEY_.')
#SINGLES_NAMES = evdev.util.resolve_ecodes(ecodes.KEY, SINGLES)
KEY_TO_CHARACTER = {
    evdev.ecodes.KEY_GRAVE: '~',
    evdev.ecodes.KEY_COMMA: ',',
    evdev.ecodes.KEY_DOT: '.',
    evdev.ecodes.KEY_SLASH: '/',
    evdev.ecodes.KEY_SEMICOLON: ';',
    evdev.ecodes.KEY_APOSTROPHE: "'",
    evdev.ecodes.KEY_LEFTBRACE: '[',
    evdev.ecodes.KEY_RIGHTBRACE: ']',
    evdev.ecodes.KEY_BACKSLASH: '\\',
    evdev.ecodes.KEY_MINUS: '-',
    evdev.ecodes.KEY_EQUAL: '=',
}


def short_key_name(key_code):
    if key_code in KEY_TO_CHARACTER:
        return KEY_TO_CHARACTER[key_code]
    s = evdev.ecodes.KEY[key_code]
    s = s[0] if isinstance(s, list) else s
    if s.startswith('KEY_'):
        s = s.replace('KEY_', '', 1)
    s = s.lower()
    return s


# TODO: do another layer of aspectful filtering, but this time on results?
async def action_generator(event_and_context_queue):
    """
    Converts evdev events to sequences of actions like
    'a', 'Y', '.', '&', 'Control-Shift-c', 'Left+' or 'close window'.
    """
    gen = unwind_queue(event_and_context_queue)
    gen = aspect_keys_only(gen)
    gen = aspect_inactivity(gen, timeout=REST_DURATION)
    gen = aspect_modifiers(gen)
    gen = aspect_repeating(gen)
    async for event, context in gen:
        if context['after_inactivity']:
            # click.echo('-flush-')
            for i in range(3):
                yield NOTHING
        repeat = context['repeat']
        active_modifiers_prefix = context['active_modifiers_prefix']

        short = short_key_name(event.code)
        short = active_modifiers_prefix + short
        if short in CUSTOM_SKIPLIST:
            continue
        if short in SHIFTED_REPLACEMENT_TABLE:
            short = SHIFTED_REPLACEMENT_TABLE[short]
        if short in CONTROL_REPLACEMENT_TABLE:
            short = CONTROL_REPLACEMENT_TABLE[short]
        if short in CUSTOM_REPLACEMENT_TABLE:
            short = CUSTOM_REPLACEMENT_TABLE[short]
        yield short + ('+' if repeat else '')


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
def cli(): pass


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

    for device in device_path:
        asyncio.ensure_future(collect_events(device))

    loop = asyncio.get_event_loop()
    for sig in signal.SIGINT, signal.SIGTERM, signal.SIGHUP:
        loop.add_signal_handler(sig, lambda sig=sig:
                                asyncio.create_task(shutdown(sig, loop)))

    async def process_actions():
        async for action in action_generator(event_and_context_queue):
            statsdb.account_for_action(action)
    try:
        loop.run_until_complete(process_actions())
    except asyncio.exceptions.CancelledError:
        print('Stopped.')


if __name__ == '__main__':
    cli()
