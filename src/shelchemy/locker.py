#  Copyright (c) 2021. Davi Pereira dos Santos
#  This file is part of the shelchemy project.
#  Please respect the license - more about this in the section (*) below.
#
#  shelchemy is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  shelchemy is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with shelchemy.  If not, see <http://www.gnu.org/licenses/>.
#
#  (*) Removing authorship by any means, e.g. by distribution of derived
#  works or verbatim, obfuscated, compiled or rewritten versions of any
#  part of this work is illegal and unethical regarding the effort and
#  time spent here.

import shelve
from contextlib import contextmanager
from datetime import datetime, timedelta
from functools import partial
from random import random
from threading import Thread

from temporenc import packb, unpackb
from time import sleep


def ping(ctx, item, timeout, stop):
    with ctx() as dic:
        while not stop[0]:
            t = timeout / 2
            if t == 0:
                break
            while not stop[0] and t > 0:
                sleep(min(0.2, t))
                t -= 0.2
            dic[item] = packb(datetime.now())


def alive(val, timeout):  # pragma: no cover
    try:
        if timeout is None:
            return True
        return datetime.now() < unpackb(val).datetime() + timedelta(seconds=timeout)
    except Exception as e:
        print(f"Problematic value: »»»{val}«««")
        print(unpackb(val))
        raise e from None


def locker(iterable, dict__url=None, timeout=None, logstep=1):
    """
    Generator that skips already processed (or still being processed) items from 'iterable'

    Item processing is restarted if 'timeout' expires.
    'dict__url' is a dict-like object or a sqlalchemy url to store and query each item status
    'logstep' is the frequency of printed messages, 'None' means 'no logs'.
    'timeout'=None keeps the job status as 'started' forever if the job never finishes.

    >>> from time import sleep
    >>> names = ["a","b","c","d","e"]
    >>> storage = {}
    >>> for name in locker(names, dict__url=storage, timeout=10):
    ...    print(f"Processing {name}")
    ...    sleep(0.1)
    ...    print(f"{name} processed!")
    'a' is new, starting
    Processing a
    a processed!
    'a' done
    'b' is new, starting
    Processing b
    b processed!
    'b' done
    'c' is new, starting
    Processing c
    c processed!
    'c' done
    'd' is new, starting
    Processing d
    d processed!
    'd' done
    'e' is new, starting
    Processing e
    e processed!
    'e' done
    >>> storage = {}
    >>> for name in locker(names, dict__url=storage, timeout=0):
    ...    print(f"Processing {name}")
    ...    sleep(0.1)
    ...    print(f"{name} processed!")
    'a' is new, starting
    Processing a
    a processed!
    'a' done
    'b' is new, starting
    Processing b
    b processed!
    'b' done
    'c' is new, starting
    Processing c
    c processed!
    'c' done
    'd' is new, starting
    Processing d
    d processed!
    'd' done
    'e' is new, starting
    Processing e
    e processed!
    'e' done
    >>> storage = {}
    >>> for name in locker(names, dict__url=storage, timeout=None):
    ...    print(f"Processing {name}")
    ...    sleep(0.1)
    ...    print(f"{name} processed!")
    'a' is new, starting
    Processing a
    a processed!
    'a' done
    'b' is new, starting
    Processing b
    b processed!
    'b' done
    'c' is new, starting
    Processing c
    c processed!
    'c' done
    'd' is new, starting
    Processing d
    d processed!
    'd' done
    'e' is new, starting
    Processing e
    e processed!
    'e' done
    >>> storage
    {'a': b'd', 'b': b'd', 'c': b'd', 'd': b'd', 'e': b'd'}
    >>> for name in locker(names, dict__url=storage, timeout=1):
    ...    print(f"Processing {name}")
    ...    sleep(0.1)
    ...    print(f"{name} processed!")
    'a' already done, skipping
    'b' already done, skipping
    'c' already done, skipping
    'd' already done, skipping
    'e' already done, skipping
    >>> for name in locker(names):
    ...    print(f"Processing {name}")
    ...    sleep(0.1)
    ...    print(f"{name} processed!")
    'a' is new, starting
    Processing a
    a processed!
    'a' done
    'b' is new, starting
    Processing b
    b processed!
    'b' done
    'c' is new, starting
    Processing c
    c processed!
    'c' done
    'd' is new, starting
    Processing d
    d processed!
    'd' done
    'e' is new, starting
    Processing e
    e processed!
    'e' done
    """
    from shelchemy.cache import Cache

    if dict__url is None:
        ctx = partial(shelve.open, "/tmp/locker.db")
    elif isinstance(dict__url, str):
        from shelchemy import sopen

        ctx = partial(sopen, dict__url, autopack=False)
    elif isinstance(dict__url, (dict, Cache)) and hasattr(dict__url, "__contains__"):

        @contextmanager
        def ctx():
            yield dict__url

    else:  # pragma: no cover
        ctx = dict__url

    for c, item in enumerate(iterable):
        # Try to avoid race condition between checking absence and marking as started.
        now = packb(datetime.now())
        sleep((random() + 1) / 1000)  # ~1.5ms
        with ctx() as dic:
            try:
                ret = dic[item]
                val = ret
                if val == b"d":
                    status, action = "already done", "skipping"
                elif not alive(val, timeout):
                    dic[item] = now  # Mark as started, as early as possible.
                    status, action = "expired", "restarting"
                else:
                    status, action = "already started", "skipping"
            except KeyError:
                dic[item] = now  # Mark as started, as early as possible.
                # Wait to see if someone else has taken the job.
                sleep(5 * (random() + 1) / 1000)  # ~7.5ms
                status, action = ("just started by other", "skipping") if dic[item] != now else ("is new", "starting")

        if logstep is not None and c % logstep == 0:
            print(f"'{item}' {status}, {action}")
        if action != "skipping":
            if timeout is None:
                yield item
            else:
                stop = [False]
                t = Thread(target=ping, args=(ctx, item, timeout, stop), daemon=True)
                t.start()
                yield item
                stop[0] = True
                t.join()

            with ctx() as dic:
                dic[item] = b"d"
            if logstep is not None and c % logstep == 0:
                print(f"'{item}' done")
