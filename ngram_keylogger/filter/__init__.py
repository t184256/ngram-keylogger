# Copyright (c) 2021, see AUTHORS. Licensed under GPLv3+, see LICENSE.

import functools

from ngram_keylogger.filter.replace import (
    make_replace,
    shift_printables,
    abbreviate_controls,
)
from ngram_keylogger.filter.skip import make_skip
from ngram_keylogger.filter.t184256_russian import t184256_russian


def apply_filters(action_generator, filter_):
    if not isinstance(filter_, list):
        return lambda q: filter_(action_generator(q))
    return functools.reduce(apply_filters, filter_, action_generator)
