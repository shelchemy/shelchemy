#  Copyright (c) 2022. Davi Pereira dos Santos
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
#  part of this work is illegal and it is unethical regarding the effort and
#  time spent here.
#


def ichunks(items, binsize, asgenerators=True):
    """
    >>> for ch in ichunks([1,2,3,4,5], 2):
    ...     print(list(ch))
    [1, 2]
    [3, 4]
    [5]
    >>> for ch in ichunks([1,2,3,4,5], 2, asgenerators=False):
    ...     print(ch)
    [1, 2]
    [3, 4]
    [5]

    Parameters
    ----------
    items
    binsize
    asgenerators

    Returns
    -------

    """
    consumed = [0]
    sent = [0]
    it = iter(items)

    def g():
        c = 0
        while c < binsize:
            try:
                val = next(it)
            except StopIteration:
                # noinspection PyTypeChecker
                consumed[0] = None
                return
            consumed[0] += 1
            yield val
            c += 1

    while True:
        yield g() if asgenerators else list(g())
        if consumed[0] is None:
            return
        sent[0] += binsize
        if consumed[0] < sent[0]:  # pragma: no cover
            raise Exception("Cannot traverse a chunk before the previous one is consumed.", consumed[0], sent[0])
