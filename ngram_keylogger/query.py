# Copyright (c) 2021, see AUTHORS. Licensed under GPLv3+, see LICENSE.

import sqlite3


def _query(db_path, limit, query, *parameters):
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


def keypresses_count(db_path, contexts, limit):
    contexts_condition, contexts_values = _contexts_to_sql(contexts)
    return _query(db_path, limit,
                  f'SELECT SUM(count) FROM keys WHERE {contexts_condition}',
                  *contexts_values)[0][0]


def keypresses_by_context(db_path, contexts, limit):
    contexts_condition, contexts_values = _contexts_to_sql(contexts)
    return _query(db_path, limit,
                  'SELECT SUM(count), context FROM keys '
                  f'WHERE {contexts_condition} GROUP BY context '
                  f'ORDER by SUM(count) DESC',
                  *contexts_values)
