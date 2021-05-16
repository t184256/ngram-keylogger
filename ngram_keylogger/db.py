# Copyright (c) 2021, see AUTHORS. Licensed under GPLv3+, see LICENSE.

import collections
import os
import sqlite3

import click

import ngram_keylogger


SAVE_MAX = 3000    # actions. Protects against differential DB analysis.
SAVE_MIN = 300     # actions. On exit you might not have enough; discards them.


class Context:
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
    def __init__(self, db, context):
        self.name = context
        self._db = db
        self._latest_actions = [ngram_keylogger.NOTHING] * 3
        self._in_memory_counters = [collections.Counter() for i in range(3)]
        self._unsaved_actions = 0

    def flush_pipeline(self):
        """ Called when inactivity/context switch is detected. """
        for _ in range(3):
            self.account_for_action(ngram_keylogger.NOTHING)

    def account_for_action(self, action):
        self._latest_actions.pop(0)
        self._latest_actions.append(action)
        smth = False
        for n in range(3):
            smth |= bool(self.account_for_ngram(self._latest_actions[-n:]))
        if smth:
            self._unsaved_actions += 1
            if SAVE_MAX <= self._unsaved_actions:
                self.save_to_db()

    def account_for_ngram(self, ngram):
        if not all(e == ngram_keylogger.NOTHING for e in ngram):
            counter = self._in_memory_counters[len(ngram) - 1]
            counter[tuple(ngram)] += 1
            return True


    def save_to_db(self):
        if not self._unsaved_actions:
            return
        if self._unsaved_actions < SAVE_MIN:
            click.echo(f'Context {self.name}: '
                       f'refusing to save {self._unsaved_actions} '
                       f'< {SAVE_MIN} actions to disk.')
            return
        self._db.increment_on_disk(self.name, self._in_memory_counters)
        click.echo(f'Context {self.name}: '
                   f'saved {self._unsaved_actions} actions to disk.')
        self._unsaved_actions = 0
        self._in_memory_counters = [collections.Counter() for i in range(3)]


class StatsDB:
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
                            '(count INT NOT NULL, context TEXT NOT NULL, '
                            f'{a_column_defs}, '
                            f'PRIMARY KEY (context, {a_column_names}))')
        click.echo(f'Database {self._path} is OK.')
        self._contexts = {'default': Context(self, 'default')}
        self._active_context = 'default'

    def switch_context(self, context_name):
        context_name = context_name or 'default'
        if self._active_context != context_name:
            self._contexts[self._active_context].flush_pipeline()
        if context_name not in self._contexts:
            self._contexts[context_name] = Context(self, context_name)
        self._active_context = context_name
        return self._contexts[context_name]

    def flush_pipeline(self):
        self._contexts[self._active_context].flush_pipeline()

    def account_for_action(self, action, context):
        self.switch_context(context).account_for_action(action)

    def save_all_to_disk(self):
        for ctx in self._contexts.values():
            ctx.save_to_db()

    def increment_on_disk(self, context_name, counters):
        with sqlite3.connect(self._path) as con:
            for n, table in ((1, 'keys'), (2, 'bigrams'), (3, 'trigrams')):
                a_column_names = ', '.join(f'a{i + 1}' for i in range(n))
                question_marks = ', '.join(('?',) * n)
                q = (f'INSERT INTO {table} (count, {a_column_names}, context) '
                     f'VALUES (?, {question_marks}, ?) '
                     f'ON CONFLICT (context, {a_column_names}) DO UPDATE '
                     'SET count = count + ? '
                     f'WHERE ({a_column_names}, context) '
                     f'   == ({question_marks}, ?)')
                for ngram, count in counters[n - 1].items():
                    con.execute(q, ((count,) + ngram + (context_name,)) * 2)
