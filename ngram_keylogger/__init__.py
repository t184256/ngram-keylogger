# Copyright (c) 2021, see AUTHORS. Licensed under GPLv3+, see LICENSE.

import ngram_keylogger.aspect as aspect
import ngram_keylogger.filter as filter
import ngram_keylogger.util as util
import ngram_keylogger.config as config
import ngram_keylogger.db as db
import ngram_keylogger.collect as collect
import ngram_keylogger.query as query
import ngram_keylogger.app as app

NOTHING = '...'  # indicates a pause
CONTEXT_IGNORE = object()
