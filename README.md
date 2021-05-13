# ngram-keylogger

A tool to help me optimize my typing by measuring what do I type.

Requires Linux, works by reading input devices directly.


## Logs n-grams

I wanted to measure what how I type and optimize my layout,
but I didn't like the idea of installing keyloggers: they'd log passwords!

N-gram keylogger logs three things:

* key frequency
* bigram frequency
* trigram frequency

and only saves the db to disk once in a while,
so even comparing two consecutive states of the database
shouldn't help the attacker much in figuring out what exactly did you type.


## Logs actions, not keypresses

It aims to log not keypresses (who cares?), but rather semantic stuff like
`Control-Alt-a`, `%` and `workspace-switch 1`.
That aspect needs configuration and improvements though.


# Takes pauses into account

N-grams don't matter if you take breaks.
Resting, typing `hi`, resting again, typing `you` and resting again
will leave you with the following trigrams:

```
... ...  h
...  h   i
 h   i  ...
 i  ... ...
... ...  y
...  y   o
 y   o   u
 o   u  ...
 u  ... ...
```

This way your n-grams don't work across your lunch breaks
and you'll be able to identify your favourite opening and finishing sequences.
