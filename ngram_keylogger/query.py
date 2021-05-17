# Copyright (c) 2021, see AUTHORS. Licensed under GPLv3+, see LICENSE.

import sqlite3


def _query(db_path, *a, **kwa):
    with sqlite3.connect(f'file:{db_path}?mode=ro', uri=True) as con:
        r = con.execute(*a, **kwa)
        return tuple(r.fetchall())


def keypresses_count(db_path):
    return _query(db_path, 'SELECT SUM(count) FROM keys;')[0][0]
