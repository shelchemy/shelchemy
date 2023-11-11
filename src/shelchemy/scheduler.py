from dataclasses import dataclass

from shelchemy.locker import locker


# todo: fixed? is there a problem with different timezones? use UTC? use database server time?
# todo: fixed? add flag to not mark task as done
# todo: flag `join` to wait for entire loop to finish before proceeding


@dataclass
class Scheduler:
    """
    Generator that skips already processed (or still being processed) items from any lshifted (<<) 'iterable'

    Item processing is restarted if 'timeout' expires.
    'url' is a sqlalchemy url (or a dict-like object) to use internally to store and query each item status
    'logstep' is the frequency of printed messages, 'None' means 'no logs'.
    'timeout'=None keeps the job status as 'started' forever if the job never finishes.

    # TODO: improve avoidance of race condition adopting a 'pre-started' state

    >>> from time import sleep
    >>> names1 = ["a","b"]
    >>> names2 = ["c"]
    >>> names3 = ["d","e"]
    >>> storage = {}
    >>> for name in Scheduler(storage, timeout=10) << names1 << names2 << names3:  # doctest:+ELLIPSIS
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
    >>> print(storage.keys())
    dict_keys(['a', 'b', 'c', 'd', 'e'])
    >>> storage = {}
    >>> for name in Scheduler(storage, timeout=10, mark_as_done=False) << names1 << names2 << names3:  # doctest:+ELLIPSIS
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
    >>> print(storage.keys())
    dict_keys([])
    """

    url: str = None
    timeout: float = None
    logstep: int = 1
    mark_as_done: bool = True

    def __post_init__(self):
        self.list_of_iterators = []

    def __lshift__(self, iterable):
        self.list_of_iterators.append(iterable)
        return self

    def __iter__(self):
        for items in self.list_of_iterators:
            yield from locker(items, self.url, self.timeout, self.logstep, self.mark_as_done)
