# Persistent dict.

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
