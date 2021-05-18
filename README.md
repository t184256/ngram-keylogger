# ngram-keylogger

A tool to help me optimize my typing by measuring how do I type.

Requires Linux, works by reading input devices directly.


## Features

### Logs n-grams

I wanted to measure what how I type and optimize my layout,
but I didn't like the idea of installing keyloggers: they'd log passwords!
Thus, a keylogger isn't something I should run on my work laptop,
and without it I'd miss out on lots of data.

N-gram keylogger doesn't log everything you type sequentially.
Instead, it logs three things:

* key frequency
* bigram frequency
* trigram frequency

and only saves the db to disk once in a while,
so even comparing two consecutive states of the database
shouldn't help the attacker much in figuring out what exactly did you type.
Good passwords contain rare n-grams though, so it...


### Takes extra precautions to avoid logging passwords

One can configure it to stop logging into windows with certain window titles
(`i3` or `sway' only),
and/or suspend logging altogether when processes with certain names are running
(rescans are throttled though, so one must take a pause before typing
 in order not to outrun the process detection).


### Logs actions, not keypresses

It aims to log not keypresses (who cares?), but rather semantic stuff like
`Control-Alt-a`, `%` and `workspace-switch 1`.
That aspect needs configuration and improvements though.


### Takes pauses into account

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


### Logs context

Can be configured to attach a different 'context' string to every bit it logs.
Could be days of the week, could be applications you use or even editor modes,
it's up to you.
Contexts with too few actions will get their data discarded though
for security reasons, so the more different contexts you have,
the longer your collection periods should be.


## Usage example

```
# ngram-keylogger collect /dev/input/by-path/platform-i8042-serio-0-event-kbd --config example/config/t184256.py
... run it for a while
```

Now let's analyze how efficient my layout is.

A colon (`:`) is typed with `Shift+;` and is thus harder to type.
Does this make sense?

```
# ngram-keylogger query keypresses ':,;' --count
3735 | :
  52 | ;
```

Not at all, I should probably swap them around.

My underscore is nearly the same combo as my Enter (only the timing differs),
because I type a lot of underscores, right?

```
# ngram-keylogger query keypresses 'enter,literal-_'
4.639339% | enter
0.162412% | _
```

```
# ngram-keylogger query keypresses 'enter,literal-_' --renormalize
96.617647% | enter
 3.382353% | _
```

Wrong. I clearly don't.

Do I at least type the letters according to the English letter frequency
(ETAION...)?

```
# ngram-keylogger query --limit=5 keypresses '[a-z]'
4.095611% | t
4.042651% | e
3.964975% | i
3.424778% | o
3.216467% | n
```

OK, close enough.

What about capital letters?

```
# ngram-keylogger query --limit=5 keypresses '[A-Z]'
1.062741% | S
0.430745% | L
0.353070% | C
0.338947% | A
0.314232% | T
```

Huh? How come every 100th action I type is a capital 'S'?
What do I type it after?

```
# ngram-keylogger query --limit=5 bigrams '*' 'S' --renormalize
40.199336% | S     | S
18.272425% | L     | S
 7.641196% | space | S
 6.976744% | o     | S
 5.980066% | ...   | S
```

Wonderful, I spam it repeatedly, type `LS` or `oS`. Super natural.
`... S` and `space S` at least make some sense.

So, where do I spam `SS`?

```
# ngram-keylogger query --limit 3 --by-context bigrams 'S' 'S' --renormalize
90.082645% | term:vi:magit:nrm | S | S
 4.958678% | term:vi:magit:ins | S | S
 3.305785% | browser           | S | S
```

Whew, I'm not going crazy. `S` is a `stage hunk` shortcut in `vimagit`,
and I definitely do spam it when I review what I'm going to commit.

```
# ngram-keylogger query --limit 3 --by-context --contexts 'term:vi:magit*' keypresses --renormalize --cumulative
 7.714808% | 7.714808% | term:vi:magit:nrm | down
13.747715% | 6.032907% | term:vi:magit:nrm | S
19.049360% | 5.301645% | term:vi:magit:nrm | up
```

Yeah, checks out.
1/5 of my vimagit keypresses are moving up and down and staging hunks.

Case closed.
