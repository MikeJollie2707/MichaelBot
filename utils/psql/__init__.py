'''Contains many functions and classes that hide all "naked" SQL to use.

Classes
-------
This module has a dataclass for every table currently exist in `dbsetup.py`. These are used to nicely store a row of data in designated table.
However, most of them don't have any member functions. All SQL functions are static. If you don't use any SQL functions due to performance, you can use
these classes to organize your data a bit better than naked dictionary.

SQL Functions
-------------
The SQL functions are meant to make the bot's code looks nice without SQL strings everywhere. They also can be slightly customized to deal with common operations.
Therefore, these functions will contain some overheads. If performance is your main concern, do not use any of these static functions.

Generally, all these functions are self-contained, meaning if something screw up, they'll rollback on their own.
However, using multiple functions at a time in the bot's code can be dangerous without wrapping them around a transaction.

Each class has a `_PREVENT_UPDATE` tuple that will contains columns that can't be updated via SQL functions for safety. These are usually primary keys or read-only attributes
(attributes that doesn't exist on the table, but only for the sake of convenience, like from JOIN table).

Other Functions
---------------
Some public functions can be convenient to use if you decide to not use the SQL functions and instead deal with SQL on your own.

Example
-------
Without transaction:
```py
# This is just an example. In reality, you should use `models.UserCache` instead of directly working on `psql.User`.
async with pool.acquire() as conn:
    user: psql.User | None = await psql.User.fetch_one(conn, id = user_id)
    assert user is not None

    user.is_whitelist = ...
    user.balance = ...
    await psql.User.update(conn, user)
```

With transaction:
```py
async with pool.acquire() as conn:
    users: list[psql.User] = await psql.User.fetch_all(conn)
    async with conn.transaction():
        for user in users:
            user.is_whitelist = ...
            user.balance = ...
            await psql.User.update(conn, user)
```

Query with constraint:
```py
def e_in_name(user: psql.User) -> bool:
    # Apply any filtering here.
    return 'e' in user.name

async with pool.acquire() as conn:
    users: list[psql.User] = await psql.User.fetch_all_where(conn, where = e_in_name)
    # Do stuffs.
```
'''

from dataclasses import asdict

from utils.psql.active_trade import ActiveTrade
from utils.psql.badge import Badge
from utils.psql.equipment import Equipment
from utils.psql.exception import *
from utils.psql.extra_inventory import ExtraInventory
from utils.psql.guild import Guild
from utils.psql.guildlog import GuildLog
from utils.psql.inventory import Inventory
from utils.psql.item import Item
from utils.psql.reminder import Reminders
from utils.psql.user import User
from utils.psql.user_badge import UserBadge
from utils.psql.user_trade import UserTrade
