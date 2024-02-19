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
            dic[item] = packb(datetime.utcnow())


def alive(val, timeout):  # pragma: no cover
    try:
        if timeout is None:
            return True
        return datetime.utcnow() < unpackb(val).datetime() + timedelta(seconds=timeout)
    except Exception as e:
        print(f"Problematic value: »»»{val}«««", flush=True)
        print(unpackb(val), flush=True)
        raise e from None


def locker(iterable, dict__url=None, timeout=None, logstep=1, mark_as_done=True, autopack_when_url=False, prefix="\r"):
    """
    Generator that skips already processed (or still being processed) items from 'iterable'

    Item processing is restarted if 'timeout' expires.
    'dict__url' is a dict-like object or a sqlalchemy url to store and query each item status
    'logstep' is the frequency of printed messages, 'None' means 'no logs'.
    'timeout'=None keeps the job status as 'started' forever if the job never finishes.
    'mark_as_done'=None  is intended to use the scheduler just to show if a task is being handled at the time.
                            useful when each task is incremental/resumable.

    >>> from time import sleep
    >>> names = ["a","b","c","d","e"]
    >>> storage = {}
    >>> for name in locker(names, dict__url=storage, timeout=10):  # doctest:+ELLIPSIS
    ...    print(f"Processing {name}")
    ...    sleep(0.1)
    ...    print(f"{name} processed!")
    20... 'a' is new, starting
    Processing a
    a processed!
    20... 'a' done
    20... 'b' is new, starting
    Processing b
    b processed!
    20... 'b' done
    20... 'c' is new, starting
    Processing c
    c processed!
    20... 'c' done
    20... 'd' is new, starting
    Processing d
    d processed!
    20... 'd' done
    20... 'e' is new, starting
    Processing e
    e processed!
    20... 'e' done
    >>> storage = {}
    >>> for name in locker(names, dict__url=storage, timeout=0, logstep=4):  # doctest:+ELLIPSIS
    ...    print(f"Processing {name}")
    ...    sleep(0.1)
    ...    print(f"{name} processed!")
    20... 'a' is new, starting
    Processing a
    a processed!
    20... 'a' done
    Processing b
    b processed!
    Processing c
    c processed!
    Processing d
    d processed!
    20... 'e' is new, starting
    Processing e
    e processed!
    20... 'e' done
    >>> storage = {}
    >>> for name in locker(names, dict__url=storage, timeout=None, logstep=4):  # doctest:+ELLIPSIS
    ...    print(f"Processing {name}")
    ...    sleep(0.1)
    ...    print(f"{name} processed!")
    20... 'a' is new, starting
    Processing a
    a processed!
    20... 'a' done
    Processing b
    b processed!
    Processing c
    c processed!
    Processing d
    d processed!
    20... 'e' is new, starting
    Processing e
    e processed!
    20... 'e' done
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
    >>> for name in locker(names):  # doctest:+ELLIPSIS
    ...    print(f"Processing {name}")
    ...    sleep(0.1)
    ...    print(f"{name} processed!")
    20... 'a' is new, starting
    Processing a
    a processed!
    20... 'a' done
    20... 'b' is new, starting
    Processing b
    b processed!
    20... 'b' done
    20... 'c' is new, starting
    Processing c
    c processed!
    20... 'c' done
    20... 'd' is new, starting
    Processing d
    d processed!
    20... 'd' done
    20... 'e' is new, starting
    Processing e
    e processed!
    20... 'e' done
    """
    from shelchemy.cache import Cache

    if dict__url is None:
        ctx = partial(shelve.open, "/tmp/locker.db")
    elif isinstance(dict__url, str):
        from shelchemy import sopen

        ctx = partial(sopen, dict__url, autopack=autopack_when_url)
    elif isinstance(dict__url, (dict, Cache)) and hasattr(dict__url, "__contains__"):

        @contextmanager
        def ctx():
            yield dict__url

    else:  # pragma: no cover
        ctx = dict__url

    print("Started scheduler", flush=True)
    for c, item in enumerate(iterable):
        # Try to avoid race condition between checking absence and marking as started.
        now = packb(datetime.utcnow())
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
            print(f"{prefix}{'                          ' if action == 'skipping' else datetime.now()} '{item}' {status}, {action}", flush=True)
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
                if mark_as_done:
                    dic[item] = b"d"
                else:
                    del dic[item]

            if logstep is not None and c % logstep == 0:
                print(f"{prefix}{datetime.now()} '{item}' done", flush=True)
