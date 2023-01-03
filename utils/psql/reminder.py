import dataclasses
import datetime as dt
import typing as t

import asyncpg

from utils.psql._base import *


@dataclasses.dataclass(slots = True)
class Reminders:
    '''Represent an entry in the `Reminders` table along with possible operations related to the table.'''
    # As of now, this class seems structure differently from the rest, so I won't subclass it from __BaseSQLObject
    # I'll see about this later.

    remind_id: int
    user_id: int
    awake_time: dt.datetime
    message: str

    _tbl_name: t.ClassVar[str] = "Reminders"
    _PREVENT_UPDATE: t.ClassVar[tuple[str]] = ("remind_id", "user_id")

    @staticmethod
    async def get_user_reminders(conn: asyncpg.Connection, user_id: int, *, as_dict: bool = False) -> list[t.Self | dict | None]:
        '''Get a list of reminders a user have.'''
        
        query = """
            SELECT * FROM Reminders
            WHERE user_id = ($1);
        """

        result = await conn.fetch(query, user_id)
        return [record_to_type(record, result_type = Reminders if not as_dict else dict) for record in result]
    @staticmethod
    async def get_reminders(conn: asyncpg.Connection, lower_time: dt.datetime, upper_time: dt.datetime, *, as_dict: bool = False) -> list[t.Self | dict | None]:
        '''Get a list of reminders within `(lower_time, upper_time]`.'''

        query = """
            SELECT * FROM Reminders
            WHERE awake_time > ($1) AND awake_time <= ($2);
        """

        result = await conn.fetch(query, lower_time, upper_time)
        return [record_to_type(record, result_type = Reminders if not as_dict else dict) for record in result]
    @staticmethod
    async def get_past_reminders(conn: asyncpg.Connection, now: dt.datetime, *, as_dict: bool = False) -> list[t.Self | dict | None]:
        '''Get a list of reminders that are supposed to be cleared before the time provided.'''
        
        query = """
            SELECT * FROM Reminders
            WHERE awake_time < ($1);
        """

        result = await conn.fetch(query, now)
        return [record_to_type(record, result_type = Reminders if not as_dict else dict) for record in result]
    @staticmethod
    async def insert_reminder(conn: asyncpg.Connection, user_id: int, when: dt.datetime, message: str) -> int:
        '''Insert a reminder entry.'''
        
        query = """
            INSERT INTO Reminders (user_id, awake_time, message)
                VALUES ($1, $2, $3);
        """
        return await run_and_return_count(conn, query, user_id, when, message)
    @staticmethod
    async def delete_reminder(conn: asyncpg.Connection, remind_id: int, user_id: int) -> int:
        '''Delete a reminder entry.'''

        # Although remind_id is sufficient, user_id is to make sure a user can't remove another reminder.
        query = """
            DELETE FROM Reminders
            WHERE remind_id = ($1) AND user_id = ($2);
        """
        return await run_and_return_count(conn, query, remind_id, user_id)
