# Copyright (c) 2021, see AUTHORS. Licensed under GPLv3+, see LICENSE.

import sqlite3

import ngram_keylogger

_DEFAULT_PATH = ngram_keylogger.db.DEFAULT_PATH


def _query(query, *parameters, db_path=_DEFAULT_PATH, limit=-1):
    with sqlite3.connect(f'file:{db_path}?mode=ro', uri=True) as con:
        if limit != -1:
            query += ' LIMIT ?'
            parameters = parameters + (limit,)
        r = con.execute(query, parameters)
        return tuple(r.fetchall())


def _contexts_to_sql(contexts):
    contexts = contexts.replace('*', '%')
    contexts = contexts.replace('?', '_')
    contexts = [contexts] if ',' not in contexts else contexts.split(',')
    if not contexts:
        return 'true', []
    return ' OR '.join(['context LIKE ?'] * len(contexts)), tuple(contexts)


def keypresses_count(contexts='*', **qargs):
    contexts_condition, contexts_values = _contexts_to_sql(contexts)
    return _query(f'SELECT SUM(count) FROM keys WHERE {contexts_condition}',
                  *contexts_values, **qargs)[0][0]


def keypresses_by_context(contexts='*', **qargs):
    contexts_condition, contexts_values = _contexts_to_sql(contexts)
    return _query('SELECT SUM(count), context FROM keys '
                  f'WHERE {contexts_condition} GROUP BY context '
                  f'ORDER by SUM(count) DESC',
                  *contexts_values, **qargs)
