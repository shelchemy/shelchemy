# Persistent dict.
from shelchemy import sopen
from shelchemy.cache import Cache

d = Cache("sqlite+pysqlite:////tmp/sqla-test.db")
d["x"] = 5
d["b"] = None
print(d["x"], d["b"])
# ...

try:
    d["xxx"]
except KeyError as m:
    print(m)
# ...

for k, v in d.items():
    print(k, v)
print("x" in d)
# ...

del d["x"]
print("x" in d)
# ...

print(d)
# ...

# Using a context manager.
with sopen() as db:
    print("x" in db)
    print(db)

    db["x"] = b"asd"
    print(db)
    print(db["x"] == b"asd")
    print("x" in db)
    print(db.x == b"asd")

    del db["x"]
    print("x" in db)

    db["any string key longer than 40 characters will be hashed depending if the DBMS backend is used"] = None
    print(db)
# ...
