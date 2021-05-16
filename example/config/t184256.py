# Example config that t184256 uses

import re
import socket

import ngram_keylogger

REST_DURATION = 2   # seconds. Waiting longer than that breaks up n-grams.
PROCESS_RESCAN = 2  # seconds. Don't rescan processes more often than that.
HOSTNAME = socket.gethostname()
PASSWORD_PROMPTERS = ('swaylock', 'pinentry', 'nmtui')
PROMPTERS_RESCAN = 3

CUSTOM_REPLACEMENT_TABLE = {
    'alt-meta-q': 'workspace-1',
    'alt-meta-w': 'workspace-2',
    'alt-meta-f': 'workspace-3',
    'alt-meta-p': 'workspace-4',
    'alt-meta-g': 'workspace-5',
    'alt-meta-y': 'window-move-to',
    'shift-backspace': 'backspace',  # keyboard firmware bug
    'alt-meta-f11': None,  # used to light up a meta mode indicator
    'alt-meta-f12': None,  # used to light up a meta mode indicator
}


def detect_prompters(p):
    for s in PASSWORD_PROMPTERS:
        if s in p.name():
            return p.name()


def context_by_title(t):
    if re.match('.*Mozilla Firefox$', t):
        return 'browser'

    if re.match(r'^\[\d+\]@$' + HOSTNAME, t):  # gpg password prompt
        return ngram_keylogger.CONTEXT_IGNORE

    m = re.match(rf'.* > vi > \[(\w+)\].* > .* \[(INS|RPL|VIL|VIB)\]$', t)
    if m:
        return f'term:vi:{m.group(1)}:{m.group(2).lower()}'
    m = re.match(rf'.* > vi > \[(\w+)\].* > .*', t)
    if m:
        return f'term:vi:{m.group(1)}:nrm'
    if re.match(r'.* > vi.*', t):
        return 'term:vi'

    if re.match(r'.* > xonsh', t):
        return 'term:xonsh'
    if re.match(r'.* > weechat', t):
        return 'term:weechat'
    if re.match(r'.* > *', t):
        return 'term:other'
    return 'other'


async def action_generator_(event_and_extras_gen):
    """
    Converts evdev events to sequences of actions like
    'a', 'Y', '.', '&', 'control-shift-c', 'Left+' or 'close window'.
    """
    gen = event_and_extras_gen
    gen = ngram_keylogger.aspect.keys_only(gen)
    gen = ngram_keylogger.aspect.inactivity(gen, timeout=REST_DURATION)
    gen = ngram_keylogger.aspect.modifiers(gen)
    gen = ngram_keylogger.aspect.repeating(gen)

    current_window_titles = ngram_keylogger.util.i3ipc.current_window_titles()

    async for event, extras in gen:
        if extras['after_inactivity']:
            yield ngram_keylogger.NOTHING, None  # flushing works the same
        repeat = extras['repeat']
        active_modifiers_prefix = extras['active_modifiers_prefix']

        short = ngram_keylogger.util.short_key_name(event.code)
        short = active_modifiers_prefix + short
        key = short + ('+' if repeat else '')

        window_title = await current_window_titles.__anext__()
        context = context_by_title(window_title)

        yield key, context


action_generator = ngram_keylogger.filter.apply_filters(action_generator_, [
    ngram_keylogger.filter.t184256_russian,
    ngram_keylogger.filter.shift_printables,
    ngram_keylogger.filter.abbreviate_controls,
    ngram_keylogger.filter.make_replace(CUSTOM_REPLACEMENT_TABLE),
    ngram_keylogger.filter.make_process_scan(detect_prompters,
                                             PROMPTERS_RESCAN),
])
