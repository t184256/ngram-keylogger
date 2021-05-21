# Copyright (c) 2021, see AUTHORS. Licensed under GPLv3+, see LICENSE.

import sqlite3

import ngram_keylogger

_DEFAULT_PATH = ngram_keylogger.db.DEFAULT_PATH


def pformat(smth):
    return f'{smth*100:.6f}%' if isinstance(smth, float) else str(smth)


def _query(query, *parameters, db_path=_DEFAULT_PATH):
    with sqlite3.connect(f'file:{db_path}?mode=ro', uri=True) as con:
        con.execute('PRAGMA case_sensitive_like = true')
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
    wildcards = wildcards.split(',')
    wildcards = [w.replace('literal-/COMMA/', 'literal-,') for w in wildcards]
    if not wildcards:
        return 'true', []
    sv = []
    for w in wildcards:
        sv.extend(_wildcard_sql(field_name, w))
    return ('(' + ' OR '.join(sql for sql, _ in sv) + ')',
            tuple(value for _, value in sv))


def keypresses_count(table_name='keys', fraction=False,
                     contexts='*', by_context=False, **qargs):
    contexts_condition, contexts_values = _wildcards_sql('context', contexts)
    if not by_context:
        return _query('SELECT SUM(count) FROM keys '
                      f'WHERE {contexts_condition}',
                      *contexts_values, **qargs)[0][0]
    else:
        norm = '/ CAST(? AS REAL)' if fraction else ''
        # FIXME: two consequtive queries can lead to inconsistent results
        return _query(f'SELECT SUM(count) {norm}, context FROM keys '
                      f'WHERE {contexts_condition} '
                      f'GROUP BY context ORDER by SUM(count) DESC',
                      *([keypresses_count(**qargs)] if fraction else []),
                      *contexts_values, **qargs)


def keypresses(key_filter='*',
               fraction=True, contexts='*', by_context=False, **qargs):
    contexts_condition, contexts_values = _wildcards_sql('context', contexts)
    key_filter_condition, key_filter_values = _wildcards_sql('a1', key_filter)
    # FIXME: two consequtive queries can lead to inconsistent results
    norm = '/ CAST(? AS REAL)' if fraction else ''
    if not by_context:
        return _query(f'SELECT SUM(count) {norm}, a1 FROM keys '
                      f'WHERE {contexts_condition} AND {key_filter_condition} '
                      f'GROUP BY a1 ORDER by SUM(count) DESC',
                      *([keypresses_count(**qargs)] if fraction else []),
                      *contexts_values, *key_filter_values, **qargs)
    else:
        return _query(f'SELECT SUM(count) {norm}, context, a1 FROM keys '
                      f'WHERE {contexts_condition} AND {key_filter_condition} '
                      f'GROUP BY context, a1 ORDER by SUM(count) DESC',
                      *([keypresses_count(**qargs)] if fraction else []),
                      *contexts_values, *key_filter_values, **qargs)


def bigrams(key_filter1, key_filter2,
            fraction=True, contexts='*', by_context=False, **qargs):
    contexts_condition, contexts_values = _wildcards_sql('context', contexts)
    key_condition1, key_values1 = _wildcards_sql('a1', key_filter1)
    key_condition2, key_values2 = _wildcards_sql('a2', key_filter2)
    # FIXME: two consequtive queries can lead to inconsistent results
    norm = '/ CAST(? AS REAL)' if fraction else ''
    if not by_context:
        return _query(f'SELECT SUM(count) {norm}, a1, a2 '
                      f'FROM bigrams WHERE {contexts_condition} '
                      f' AND {key_condition1} AND {key_condition2} '
                      f'GROUP BY a1, a2 ORDER by SUM(count) DESC',
                      *([keypresses_count('bigrams', **qargs)]
                        if fraction else []),
                      *contexts_values, *key_values1, *key_values2, **qargs)
    else:
        return _query(f'SELECT SUM(count) {norm}, context, a1, a2 '
                      f'FROM bigrams WHERE {contexts_condition} '
                      f' AND {key_condition1} AND {key_condition2} '
                      f'GROUP BY context, a1, a2 ORDER by SUM(count) DESC',
                      *([keypresses_count('bigrams', **qargs)]
                        if fraction else []),
                      *contexts_values, *key_values1, *key_values2, **qargs)


def trigrams(key_filter1, key_filter2, key_filter3,
             fraction=True, contexts='*', by_context=False, **qargs):
    contexts_condition, contexts_values = _wildcards_sql('context', contexts)
    key_condition1, key_values1 = _wildcards_sql('a1', key_filter1)
    key_condition2, key_values2 = _wildcards_sql('a2', key_filter2)
    key_condition3, key_values3 = _wildcards_sql('a3', key_filter3)
    # FIXME: two consequtive queries can lead to inconsistent results
    norm = '/ CAST(? AS REAL)' if fraction else ''
    if not by_context:
        return _query(f'SELECT SUM(count) {norm}, a1, a2, a3 '
                      f'FROM trigrams WHERE {contexts_condition} '
                      f' AND {key_condition1} '
                      f' AND {key_condition2} '
                      f' AND {key_condition3} '
                      f'GROUP BY a1, a2, a3 ORDER by SUM(count) DESC',
                      *([keypresses_count('trigrams', **qargs)]
                        if fraction else []),
                      *contexts_values,
                      *key_values1, *key_values2, *key_values3, **qargs)
    else:
        return _query(f'SELECT SUM(count) {norm}, context, a1, a2, a3 '
                      f'FROM trigrams WHERE {contexts_condition} '
                      f' AND {key_condition1} '
                      f' AND {key_condition2} '
                      f' AND {key_condition3} '
                      f'GROUP BY context, a1, a2, a3 ORDER by SUM(count) DESC',
                      *([keypresses_count('trigrams', **qargs)]
                        if fraction else []),
                      *contexts_values,
                      *key_values1, *key_values2, *key_values3, **qargs)
