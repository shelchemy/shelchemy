from dataclasses import dataclass

from shelchemy.locker import locker


@dataclass
class Scheduler:
    """
    Generator that skips already processed (or still being processed) items from any lshifted (<<) 'iterable'

    Item processing is restarted if 'timeout' expires.
    'url' is a sqlalchemy url (or a dict-like object) to use internally to store and query each item status
    'logstep' is the frequency of printed messages, 'None' means 'no logs'.
    'timeout'=None keeps the job status as 'started' forever if the job never finishes.

    # TODO: improve avoidance of race condition adopting a pre-started state

    >>> from time import sleep
    >>> names1 = ["a","b"]
    >>> names2 = ["c"]
    >>> names3 = ["d","e"]
    >>> storage = {}
    >>> for name in Scheduler(storage, timeout=10) << names1 << names2 << names3:
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
    >>> for name in Scheduler(storage, timeout=10) << names1 << names2 << names3:
    ...    print(f"Processing {name}")
    ...    sleep(0.1)
    ...    print(f"{name} processed!")
    'a' already done, skipping
    'b' already done, skipping
    'c' already done, skipping
    'd' already done, skipping
    'e' already done, skipping
    """

    url: str = None
    timeout: float = None
    logstep: int = 1

    def __post_init__(self):
        self.list_of_iterators = []

    def __lshift__(self, iterable):
        self.list_of_iterators.append(iterable)
        return self

    def __iter__(self):
        for items in self.list_of_iterators:
            yield from locker(items, self.url, self.timeout, self.logstep)
