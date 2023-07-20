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

from contextlib import contextmanager
from hashlib import md5
from pickle import dumps
from typing import TypeVar

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from shelchemy import memory
from shelchemy.sqla import Base, Content

VT = TypeVar("VT")


def check(key):
    if not isinstance(key, str):
        try:
            dump = dumps(key, protocol=5)
        except Exception as e:
            print(e)
            raise WrongKeyType(f"Key must be string or serializable (pickable), not {type(key)}.", key)
        key = dump
    else:
        key = key.encode()
    return md5(key).hexdigest() if len(key) not in [32, 40] else key


class Cache:
    r"""
    Dict-like persistence based on SQLAlchemy

    string or serializable (pickle) keys only

    When len(key) not in [32, 40], key is internally hashed to a MD5 hexdigest

    Usage:

    >>> from shelchemy import sopen
    >>> d = Cache("sqlite+pysqlite:////tmp/sqla-test.db")
    >>> d["x"] = 5
    >>> d["x"]
    5
    >>> for k, v in d.items():
    ...     print(k, v)
    9dd4e461268c8034f5c8564e155c67a6 5
    >>> "x" in d
    True
    >>> len(d)
    1
    >>> del d["x"]
    >>> "x" in d
    False
    >>> d
    {}
    >>> with sopen() as db:
    ...     "x" in db
    ...     db
    ...     db["x"] = b"asd"
    ...     db
    ...     db["9dd4e461268c8034f5c8564e155c67a6"] == b"asd"
    ...     "x" in db
    ...     db.x == b"asd"
    ...     del db["x"]
    ...     "x" in db
    False
    {}
    {'9dd4e461268c8034f5c8564e155c67a6': b'asd'}
    True
    True
    True
    False
    """

    def __init__(
        self, session=memory, ondup="overwrite", autopack=True, safepack=False, stablepack=False, debug=False, _engine=None
    ):
        if isinstance(session, str):

            @contextmanager
            def sessionctx():
                engine = create_engine(url=session, echo=debug)
                self._engine = engine
                session_ = Session(engine, autoflush=False)
                try:
                    yield session_
                except:
                    session_.rollback()
                    raise
                finally:
                    session_.close()

        else:
            if _engine is None:
                raise Exception(f"Missing `_engine` for external non string session.")
            self._engine = _engine

            @contextmanager
            def sessionctx():
                try:
                    yield session
                except:
                    session.rollback()
                    raise
                finally:
                    session.close()

        self.sessionctx = sessionctx
        self.ondup = ondup
        self.autopack = autopack
        self.safepack = safepack
        self.stablepack = stablepack

    def ensure_build(self, query__f):
        with self.sessionctx() as session:
            try:
                return query__f(session)
            except Exception as e:
                try:
                    Base.metadata.create_all(self._engine)
                except:
                    raise e from None
        return query__f(session)

    def __contains__(self, key):
        key = check(key)
        return self.ensure_build(lambda session: session.query(Content).filter_by(id=key).first() is not None)

    def __iter__(self):
        return self.ensure_build(lambda session: (c.id for c in session.query(Content).all()))

    def __setitem__(self, key: str, value, packing=True):
        key = check(key)
        if self.autopack and packing:
            try:
                from safeserializer.compression import pack
            except ModuleNotFoundError:
                raise Exception(
                    "You need to install optional packages `safeserializer` and `lz4` to be able to use compression inside shelchemy."
                )
            value = pack(value, ensure_determinism=self.stablepack, unsafe_fallback=not self.safepack)
        elif isinstance(value, str):
            value = value.encode()

        def f(session):
            if self.ondup == "overwrite":
                session.query(Content).filter_by(id=key).delete()
            if self.ondup == "stop" or session.query(Content).filter_by(id=key).first() is None:
                content = Content(id=key, blob=value)
                session.add(content)
            session.commit()

        self.ensure_build(f)

    def update(self, dic, packing=True):
        def f(session):
            for k, v in dic.items():
                k = check(k)
                if self.autopack and packing:
                    try:
                        from safeserializer.compression import pack
                    except ModuleNotFoundError:
                        raise Exception(
                            "You need to install optional packages `safeserializer` and `lz4` to be able to use compression inside shelchemy."
                        )
                    v = pack(v, ensure_determinism=self.stablepack, unsafe_fallback=not self.safepack)
                elif isinstance(v, str):
                    v = v.encode()

                if self.ondup == "overwrite":
                    session.query(Content).filter_by(id=k).delete()
                if self.ondup == "stop" or session.query(Content).filter_by(id=k).first() is None:
                    content = Content(id=k, blob=v)
                    session.add(content)
            session.commit()

        self.ensure_build(f)

    def __getitem__(self, key, packing=True):
        key = check(key)

        def f(session):
            if ret := session.query(Content).get(key):
                if ret is not None:
                    ret = ret.blob
                    if self.autopack and packing:
                        try:
                            from safeserializer.compression import unpack
                        except ModuleNotFoundError:
                            raise Exception(
                                "You need to install optional packages `safeserializer` and `lz4` to be able to use compression inside shelchemy."
                            )
                        ret = unpack(ret)
            return ret

        return self.ensure_build(f)

    def __delitem__(self, key):
        key = check(key)

        def f(session):
            session.query(Content).filter_by(id=key).delete()
            session.commit()

        self.ensure_build(f)

    def __getattr__(self, key):
        key_ = check(key)
        if key_ in self:
            return self[key_]
        return self.__getattribute__(key)

    def __len__(self):
        return self.ensure_build(lambda session: session.query(Content).count())

    def __repr__(self):
        return repr(self.asdict)

    def __str__(self):
        return repr(self)

    @property
    def asdict(self):
        return {k: self[k] for k in self}

    def copy(self):
        raise NotImplementedError

    def keys(self):
        return iter(self)

    def items(self):
        for k in self.keys():
            yield k, self[k]


"""
multiuser                   |   single user
----------------------------------------------
cache = SQLA(session)       |               ->  for already opened/permanent/global sessions
with sqla(url) as cache:    |   shelve      ->  a single session that open/close automatically
cache = SQLA(DBMS url)      |   Disk        ->
----------------------------------------------
Oka(web url); cache         |   dict        -> dict-like cache  
"""


class WrongKeyType(Exception):
    pass
