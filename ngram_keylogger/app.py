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
    pass


@cli.command()
@click.argument('device_path', nargs=-1, required=True,
                type=click.Path(readable=True))
@click.option('--config', default=ngram_keylogger.config.default_path(),
              type=click.Path(readable=True))
@click.pass_context
def collect(ctx, device_path, config):
    """ Collects keystrokes, saves them to disk. """
    ngram_keylogger.collect.collect(device_path, ctx.obj['db'], config)


@cli.group()
@click.pass_context
def query(ctx):
    """
    Output various stats from the database.
    """
    pass


@query.command()
@click.pass_context
def keypresses_count(ctx):
    """
    Print how many keypresses are recorded in the db.
    """
    print(ngram_keylogger.query.keypresses_count(ctx.obj['db']))
