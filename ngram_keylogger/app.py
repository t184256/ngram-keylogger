# Copyright (c) 2021, see AUTHORS. Licensed under GPLv3+, see LICENSE.

"""
n-gram keylogger: typing stats that don't leak passwords

Uses evdev to read the device files directly,
and thus requires appropriate permissions.
"""

import click

import ngram_keylogger


@click.group(help=__doc__)
@click.option('--db', default=ngram_keylogger.db.DEFAULT_PATH,
              type=click.Path(readable=True))
@click.pass_context
def cli(ctx, db):
    ctx.ensure_object(dict)
    ctx.obj['db'] = db


@cli.command()
@click.argument('device_path', nargs=-1, required=True,
                type=click.Path(readable=True))
@click.option('--config', default=ngram_keylogger.config.default_path(),
              type=click.Path(readable=True))
@click.pass_context
def collect(ctx, device_path, config):
    """ Collects keystrokes, saves them to disk. """
    ngram_keylogger.collect.collect(device_path, ctx.obj['db'], config)


def align(smth, width):
    s = str(smth)
    if isinstance(smth, int):
        return ' ' * (width - len(s)) + s
    return s + ' ' * (width - len(s))


def pprint(results):
    if isinstance(results, int):
        print(results)
    elif not results:
        print('nothing')
    elif isinstance(results, tuple) and not isinstance(results[0], tuple):
        for r in results:
            print(results)
    elif isinstance(results, tuple) and isinstance(results[0], tuple):
        # assume a rectangle
        max_widths = [max(len(str(results[row][col]))
                          for row in range(len(results)))
                      for col in range(len(results[0]))]
        for row in results:
            print('|'.join(align(x, max_widths[i]) for i, x in enumerate(row)))
    else:
        print('warning: unknown format')
        print(results)


@cli.group()
@click.pass_context
@click.option('--contexts', default='*',
              help='filter by contexts (e.g., `term:vi:*` or_`browser,other`)')
@click.option('--limit', default=-1, type=int,
              help='show a maximum of this many results')
def query(ctx, contexts, limit):
    """
    Output various stats from the database.
    """
    ctx.ensure_object(dict)
    ctx.obj['contexts'] = contexts
    ctx.obj['limit'] = limit
    ctx.obj['qargs'] = (ctx.obj['db'], ctx.obj['contexts'], ctx.obj['limit'])


@query.command()
@click.pass_context
def keypresses_count(ctx):
    """
    Print how many keypresses are recorded.
    """
    pprint(ngram_keylogger.query.keypresses_count(*ctx.obj['qargs']))


@query.command()
@click.pass_context
def keypresses_by_context(ctx):
    """
    Print how many keypresses are recorded, categorized by context.
    """
    pprint(ngram_keylogger.query.keypresses_by_context(*ctx.obj['qargs']))
