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


def pprint(results, renormalize=False, cumulative=False):
    if isinstance(results, int):
        print(results)
    elif not results:
        print('nothing')
    elif isinstance(results, tuple) and not isinstance(results[0], tuple):
        for r in results:
            print(results)
    elif isinstance(results, tuple) and isinstance(results[0], tuple):
        # assume a rectangle with columns of same type
        if isinstance(results[0][0], float):
            if renormalize and isinstance(results[0][0], float):
                total = sum(f for f, *_ in results)
                results = tuple((f / total, *o) for f, *o in results)
            if cumulative:
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
    ctx.obj['qargs']['limit'] = limit


@query.command()
@click.option('--renormalize/--no-renormalize', default=False,
              help='Renormalize to the fraction of the sum of the output')
@click.option('--cumulative/--no-cumulative', default=False,
              help='Also output cumulative sum')
@click.pass_context
def keypresses_count(ctx, cumulative, renormalize):
    """
    Print how many keypresses are recorded, categorized by context.
    """
    d = ngram_keylogger.query.keypresses_count(**ctx.obj['qargs'])
    pprint(d, renormalize=renormalize, cumulative=cumulative)


@query.command()
@click.option('--renormalize/--no-renormalize', default=False,
              help='Renormalize to the fraction of the sum of the output')
@click.option('--cumulative/--no-cumulative', default=False,
              help='Also output cumulative sum')
@click.argument('key_filter', default='*', required=False)
@click.pass_context
def keypresses(ctx, cumulative, renormalize, key_filter):
    """
    Print the most popular keypresses matching an optional filter argument.
    """
    pprint(ngram_keylogger.query.keypresses(**ctx.obj['qargs'],
                                            key_filter=key_filter),
           renormalize=renormalize, cumulative=cumulative)


@query.command()
@click.option('--renormalize/--no-renormalize', default=False,
              help='Renormalize to the fraction of the sum of the output')
@click.option('--cumulative/--no-cumulative', default=False,
              help='Also output cumulative sum')
@click.argument('key_filters', default='*', nargs=2)
@click.pass_context
def bigrams(ctx, cumulative, renormalize, key_filters):
    """
    Print the most popular keypresses matching the filter arguments.
    Example: --by-context query bigrams 'S' '[A-Z]' --renormalize
    """
    pprint(ngram_keylogger.query.bigrams(*key_filters, **ctx.obj['qargs']),
           renormalize=renormalize, cumulative=cumulative)


@query.command()
@click.option('--renormalize/--no-renormalize', default=False,
              help='Renormalize to the fraction of the sum of the output')
@click.option('--cumulative/--no-cumulative', default=False,
              help='Also output cumulative sum')
@click.argument('key_filters', default='*', nargs=3)
@click.pass_context
def trigrams(ctx, cumulative, renormalize, key_filters):
    """
    Print the most popular trigrams matching the filter arguments.'
    Example: --by-context query trigrams --cumulative '*' '*' '*'
    """
    pprint(ngram_keylogger.query.trigrams(*key_filters, **ctx.obj['qargs']),
           renormalize=renormalize, cumulative=cumulative)
