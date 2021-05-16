# Copyright (c) 2021, see AUTHORS. Licensed under GPLv3+, see LICENSE.

import collections
import os
import sqlite3

import click

import ngram_keylogger


SAVE_MAX = 3000    # actions. Protects against differential DB analysis.
SAVE_MIN = 300     # actions. On exit you might not have enough; discards them.


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
    def __init__(self, path):
        self._path = path
        click.echo(f'Checking database {self._path}...')
        os.makedirs(os.path.dirname(self._path), exist_ok=True)
        with sqlite3.connect(self._path) as con:
            for n, table in ((1, 'keys'), (2, 'bigrams'), (3, 'trigrams')):
                a_column_names = ', '.join(f'a{i + 1}' for i in range(n))
                a_column_defs = ', '.join(f'a{i + 1} TEXT NOT NULL'
                                          for i in range(n))
                con.execute(f'CREATE TABLE IF NOT EXISTS {table} '
                            f'(count INT NOT NULL, {a_column_defs}, '
                            f' PRIMARY KEY ({a_column_names}))')
        click.echo(f'Database {self._path} is OK.')
        self._latest_actions = [ngram_keylogger.NOTHING] * 3
        self._in_memory_counters = [collections.Counter() for i in range(3)]
        self._unsaved_actions = 0

    def flush_pipeline(self):
        """ Called when inactivity is detected. """
        for _ in range(3):
            self.account_for_action(ngram_keylogger.NOTHING)

    def account_for_action(self, action):
        self._latest_actions.pop(0)
        self._latest_actions.append(action)
        for n in range(3):
            self.account_for_ngram(self._latest_actions[-n:])
        self._unsaved_actions += 1
        if SAVE_MAX <= self._unsaved_actions:
            self.save_to_disk()

    def account_for_ngram(self, ngram):
        if not all(e == ngram_keylogger.NOTHING for e in ngram):
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
        with sqlite3.connect(self._path) as con:
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



