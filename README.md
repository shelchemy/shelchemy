![test](https://github.com/shelchemy/shelchemy/workflows/test/badge.svg)
[![codecov](https://codecov.io/gh/shelchemy/shelchemy/branch/main/graph/badge.svg)](https://codecov.io/gh/shelchemy/shelchemy)
<a href="https://pypi.org/project/shelchemy">
<img src="https://img.shields.io/github/v/release/shelchemy/shelchemy?display_name=tag&sort=semver&color=blue" alt="github">
</a>
![Python version](https://img.shields.io/badge/python-3.8%20%7C%203.9-blue.svg)
[![license: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

[![API documentation](https://img.shields.io/badge/doc-API%20%28auto%29-a0a0a0.svg)](https://shelchemy.github.io/shelchemy)
[![Downloads](https://static.pepy.tech/badge/shelchemy)](https://pepy.tech/project/shelchemy)
![PyPI - Downloads](https://img.shields.io/pypi/dm/shelchemy)

# shelchemy - Dict-like (shelve-like) storage wrapper for any DBMS (SQLAlchemy)
 


## Python installation
### from package
```bash
# Set up a virtualenv. 
python3 -m venv venv
source venv/bin/activate

# Install from PyPI
pip install shelchemy
```

### from source
```bash
git clone https://github.com/shelchemy/shelchemy
cd shelchemy
poetry install
```

### Examples
This library is more usefull when used along with `hdict`.
Here are some possible usages by itself.

**Scheduling jobs.**
<details>
<p>

```python3
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
"""
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
```


</p>
</details>

**Persistent dict.**
<details>
<p>

```python3

from shelchemy.cache import Cache

d = Cache("sqlite+pysqlite:////tmp/sqla-test.db")
d["x"] = 5
d["b"] = None
print(d["x"], d["b"])
"""
5 None
"""
```

```python3

try:
    d["xxx"]
except KeyError as m:
    print(m)
"""
'f561aaf6ef0bf14d4208bb46a4ccb3ad'
"""
```

```python3

for k, v in d.items():
    print(k, v)
print("x" in d)
"""
aed0339093d97301965a4e23dac3424a b'only bytes when autopack=False'
0cc175b9c0f1b6a831c399e269772661 b'by'
9dd4e461268c8034f5c8564e155c67a6 5
92eb5ffee6ae2fec3ad71c777531578f None
True
"""
```

```python3

del d["x"]
print("x" in d)
"""
False
"""
```

```python3

print(d)
"""
{'aed0339093d97301965a4e23dac3424a': b'only bytes when autopack=False', '0cc175b9c0f1b6a831c399e269772661': b'by', '92eb5ffee6ae2fec3ad71c777531578f': None}
"""
```


</p>
</details>


## Grants
This work was partially supported by Fapesp under supervision of
Prof. André C. P. L. F. de Carvalho at CEPID-CeMEAI (Grants 2013/07375-0 – 2019/01735-0).
