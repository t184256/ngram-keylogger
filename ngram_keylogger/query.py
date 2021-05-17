# Copyright (c) 2021, see AUTHORS. Licensed under GPLv3+, see LICENSE.

import sqlite3

import ngram_keylogger

_DEFAULT_PATH = ngram_keylogger.db.DEFAULT_PATH


def pformat(smth):
    return f'{smth*100:.6f}%' if isinstance(smth, float) else str(smth)


def _query(query, *parameters, db_path=_DEFAULT_PATH, limit=-1):
    with sqlite3.connect(f'file:{db_path}?mode=ro', uri=True) as con:
        con.execute('PRAGMA case_sensitive_like = true')
        if limit != -1:
            query += ' LIMIT ?'
            parameters = parameters + (limit,)
        r = con.execute(query, parameters)
        return tuple(r.fetchall())


def _wildcard_sql(field_name, wildcard):
    if wildcard.lower().startswith('literal'):
        yield f'{field_name} = ?', wildcard[len('literal') + 1:]
    if wildcard.startswith('[') and wildcard.endswith(']'):  # [a-z123]
        chars = wildcard[1:-1]
        i = 0
        while i < len(chars):
            if i + 2 < len(chars) and chars[i + 1] == '-':
                t, f = ord(chars[i]), ord(chars[i + 2])
                for j in range(min(t, f), max(t, f) + 1):
                    yield f'{field_name} = ?', chr(j)
                i += 1
            else:
                yield f'{field_name} = ?', chars[i]
            i += 1
    else:
        wildcard = wildcard.replace('*', '%')
        wildcard = wildcard.replace('?', '_')
    yield f'{field_name} LIKE ?', wildcard


def _wildcards_sql(field_name, wildcards):
    wildcards = wildcards.replace('literal-,', 'literal-/COMMA/')
    wildcards = [wildcards] if ',' not in wildcards else wildcards.split(',')
    wildcards = [w.replace('literal-/COMMA/', 'literal-,') for w in wildcards]
    if not wildcards:
        return 'true', []
    sv = []
    for w in wildcards:
        sv.extend(_wildcard_sql(field_name, w))
    return ('(' + ' OR '.join(sql for sql, _ in sv) + ')',
            tuple(value for _, value in sv))


def keypresses_count(contexts='*', **qargs):
    contexts_condition, contexts_values = _wildcards_sql('context', contexts)
    return _query(f'SELECT SUM(count) FROM keys WHERE {contexts_condition}',
                  *contexts_values, **qargs)[0][0]


def keypresses_total_by_context(contexts='*', **qargs):
    contexts_condition, contexts_values = _wildcards_sql('context', contexts)
    # FIXME: two consequtive queries can lead to inconsistent results
    return _query('SELECT SUM(count) / CAST(? AS REAL), context FROM keys '
                  f'WHERE {contexts_condition} '
                  f'GROUP BY context ORDER by SUM(count) DESC',
                  keypresses_count(**qargs),
                  *contexts_values, **qargs)


def keypresses(key_filter='*', contexts='*', **qargs):
    contexts_condition, contexts_values = _wildcards_sql('context', contexts)
    key_filter_condition, key_filter_values = _wildcards_sql('a1', key_filter)
    # FIXME: two consequtive queries can lead to inconsistent results
    return _query('SELECT SUM(count) / CAST(? AS REAL), a1 FROM keys '
                  f'WHERE {contexts_condition} AND {key_filter_condition} '
                  f'GROUP BY a1 ORDER by SUM(count) DESC',
                  keypresses_count(**qargs),
                  *contexts_values, *key_filter_values, **qargs)
