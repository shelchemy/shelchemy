from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

memory = "sqlite+pysqlite:///:memory:"


@contextmanager
def sopen(url=memory, ondup="overwrite", autopack=True, safepack=False, stablepack=False, debug=False):
    from .cache import Cache as Cache

    engine = create_engine(url, echo=debug)
    with Session(engine, autoflush=False) as session:
        yield Cache(session, ondup, autopack, safepack, stablepack, debug, _engine=engine)
