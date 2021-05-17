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


# collect

@cli.command()
@click.argument('device_path', nargs=-1, required=True,
                type=click.Path(readable=True))
@click.option('--config', default=ngram_keylogger.config.default_path(),
              type=click.Path(readable=True))
@click.pass_context
def collect(ctx, device_path, config):
    """ Collects keystrokes, saves them to disk. """
    ngram_keylogger.collect.collect(device_path, ctx.obj['db'], config)


# pretty-printing for query

def align(smth, width):
    s = ngram_keylogger.query.pformat(smth)
    if isinstance(smth, int) or isinstance(smth, float):
        return ' ' * (width - len(s)) + s
    return s + ' ' * (width - len(s))


def pprint(results, limit=None, renormalize=False, cumulative=False):
    if isinstance(results, int):
        print(results)
    elif not results:
        print('nothing')
    elif isinstance(results, tuple) and not isinstance(results[0], tuple):
        for r in results:
            print(results)
    elif (results and isinstance(results, tuple)
          and results[0] and isinstance(results[0], tuple)):
        # assume a rectangle with columns of same type
        if isinstance(results[0][0], (int, float)) and renormalize:
            total = sum(f for f, *_ in results)
            results = tuple((f / total, *o) for f, *o in results)
        if limit is not None and limit != -1:
            results = results[:limit]
        if isinstance(results[0][0], (int, float)) and cumulative:
            results = tuple((sum(f for f, *_ in results[:j+1]), *row)
                            for j, row in enumerate(results))
        max_widths = [max(len(ngram_keylogger.query.pformat(results[row][col]))
                          for row in range(len(results)))
                      for col in range(len(results[0]))]
        for row in results:
            print(' | '.join(align(x, max_widths[i])
                             for i, x in enumerate(row)))
    else:
        print('warning: unknown format')
        print(results)


# query

@cli.group()
@click.pass_context
@click.option('--contexts', default='*',
              help=('filter by contexts '
                    '(e.g., `term:*`, `term:,other` or `LITERAL-*`)'))
@click.option('--by-context/--combine-contexts', default=False)
@click.option('--limit', default=-1, type=int,
              help='show a maximum of this many results')
def query(ctx, contexts, by_context, limit):
    """
    Output various stats from the database.
    """
    ctx.ensure_object(dict)
    ctx.obj['qargs'] = {}
    ctx.obj['qargs']['db_path'] = (ctx.obj['db'] if 'db' in ctx.obj else
                                   ngram_keylogger.db.DEFAULT_PATH)
    ctx.obj['qargs']['contexts'] = contexts
    ctx.obj['qargs']['by_context'] = by_context
    ctx.obj['limit'] = limit


@query.command()
@click.option('--fraction/--count', default=False)
@click.option('--renormalize/--no-renormalize', default=False,
              help='Renormalize to the fraction of the sum of the output')
@click.option('--cumulative/--no-cumulative', default=False,
              help='Also output cumulative sum')
@click.pass_context
def keypresses_count(ctx, fraction, cumulative, renormalize):
    """
    Print how many keypresses are recorded, categorized by context.
    """
    pprint(ngram_keylogger.query.keypresses_count(**ctx.obj['qargs'],
                                                  fraction=fraction),
           limit=ctx.obj['limit'],
           renormalize=renormalize, cumulative=cumulative)


@query.command()
@click.option('--fraction/--count', default=True)
@click.option('--renormalize/--no-renormalize', default=False,
              help='Renormalize to the fraction of the sum of the output')
@click.option('--cumulative/--no-cumulative', default=False,
              help='Also output cumulative sum')
@click.argument('key_filter', default='*', required=False)
@click.pass_context
def keypresses(ctx, fraction, cumulative, renormalize, key_filter):
    """
    Print the most popular keypresses matching an optional filter argument.
    """
    pprint(ngram_keylogger.query.keypresses(key_filter,
                                            fraction=fraction,
                                            **ctx.obj['qargs']),
           limit=ctx.obj['limit'],
           renormalize=renormalize, cumulative=cumulative)


@query.command()
@click.option('--fraction/--count', default=True)
@click.option('--renormalize/--no-renormalize', default=False,
              help='Renormalize to the fraction of the sum of the output')
@click.option('--cumulative/--no-cumulative', default=False,
              help='Also output cumulative sum')
@click.argument('key_filters', default='*', nargs=2)
@click.pass_context
def bigrams(ctx, fraction, cumulative, renormalize, key_filters):
    """
    Print the most popular keypresses matching the filter arguments.
    Example: --by-context query bigrams 'S' '[A-Z]' --renormalize
    """
    pprint(ngram_keylogger.query.bigrams(*key_filters,
                                         fraction=fraction,
                                         **ctx.obj['qargs']),
           limit=ctx.obj['limit'],
           renormalize=renormalize, cumulative=cumulative)


@query.command()
@click.option('--fraction/--count', default=True)
@click.option('--renormalize/--no-renormalize', default=False,
              help='Renormalize to the fraction of the sum of the output')
@click.option('--cumulative/--no-cumulative', default=False,
              help='Also output cumulative sum')
@click.argument('key_filters', default='*', nargs=3)
@click.pass_context
def trigrams(ctx, fraction, cumulative, renormalize, key_filters):
    """
    Print the most popular trigrams matching the filter arguments.'
    Example: query trigrams --count --cumulative '*' '*' '*'
    """
    pprint(ngram_keylogger.query.trigrams(*key_filters,
                                          fraction=fraction,
                                          **ctx.obj['qargs']),
           limit=ctx.obj['limit'],
           renormalize=renormalize, cumulative=cumulative)
