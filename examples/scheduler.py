# Scheduling jobs.
from time import sleep

from shelchemy.scheduler import Scheduler

# Jobs can be distributed across multiple computers/networks.
names1 = ["a", "b"]
names2 = ["c"]
names3 = ["d", "e"]
storage = {}
# `storage` can be: shelve; URI pointing to a database; or, any dict-like object.
#   Example of a local database: storage="sqlite+pysqlite:////tmp/sqla-test.db"
#   Example of a remote database: storage="mysql+pymysql://user1:password1@hosh.page/db1"
for name in Scheduler(storage, timeout=10) << names1 << names2 << names3:
    print(f"Processing {name}")
    sleep(0.1)
    print(f"{name} processed!")
# ...
