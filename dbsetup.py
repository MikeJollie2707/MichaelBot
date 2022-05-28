'''Run this script once if the database or a table is missing.'''

import asyncio
import sys
import asyncpg

from main import load_info

async def setup_database(user, password, database, host, port):
    conn = await asyncpg.connect(
        host = host,
        port = port,
        user = user,
        password = password,
        database = database
    )

    async with conn.transaction():
        print("Creating Guilds table...", end = '')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS Guilds (
                id INT8 PRIMARY KEY,
                name TEXT NOT NULL,
                is_whitelist BOOL NOT NULL DEFAULT TRUE,
                prefix TEXT NOT NULL DEFAULT '$'
            );
        ''')
        print("Done!")

        print("Creating GuildsLogs table...", end = '')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS GuildsLogs (
                guild_id INT8 UNIQUE NOT NULL,
                log_channel INT8 DEFAULT NULL,
                guild_channel_create BOOL NOT NULL DEFAULT TRUE,
                guild_channel_delete BOOL NOT NULL DEFAULT TRUE,
                guild_channel_update BOOL NOT NULL DEFAULT TRUE,
                guild_ban BOOL NOT NULL DEFAULT TRUE,
                guild_unban BOOL NOT NULL DEFAULT TRUE,
                guild_update BOOL NOT NULL DEFAULT TRUE,
                member_join BOOL NOT NULL DEFAULT TRUE,
                member_leave BOOL NOT NULL DEFAULT TRUE,
                member_update BOOL NOT NULL DEFAULT TRUE,
                guild_bulk_message_delete BOOL NOT NULL DEFAULT TRUE,
                guild_message_delete BOOL NOT NULL DEFAULT TRUE,
                guild_message_update BOOL NOT NULL DEFAULT TRUE,
                role_create BOOL NOT NULL DEFAULT TRUE,
                role_delete BOOL NOT NULL DEFAULT TRUE,
                role_update BOOL NOT NULL DEFAULT TRUE,
                command_complete BOOL NOT NULL DEFAULT FALSE,
                command_error BOOL NOT NULL DEFAULT TRUE,
                CONSTRAINT fk_guildslogs_guilds
                    FOREIGN KEY (guild_id) REFERENCES Guilds(id) ON UPDATE CASCADE ON DELETE CASCADE
            );
        ''')
        print("Done!")

        await conn.execute('''
            CREATE TYPE LogConfig AS (
                guild_channel_create BOOL,
                guild_channel_delete BOOL,
                guild_channel_update BOOL,
                guild_ban BOOL,
                guild_unban BOOL,
                guild_update BOOL,
                member_join BOOL,
                member_leave BOOL,
                member_update BOOL,
                guild_bulk_message_delete BOOL,
                guild_message_delete BOOL,
                guild_message_update BOOL,
                role_create BOOL,
                role_update BOOL,
                command_complete BOOL,
                command_error BOOL
            );
        ''')

        await conn.execute('''
            CREATE TABLE GuildsLogsTest (
                guild_id INT8 UNIQUE NOT NULL,
                log_channel INT8 DEFAULT NULL,
                config LogConfig,
                CONSTRAINT fk_guildslogstest_guilds
                    FOREIGN KEY (guild_id) REFERENCES Guilds(id) ON UPDATE CASCADE ON DELETE CASCADE
            );
        ''')

        print("Creating Users table...", end = '')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS Users (
                id INT8 PRIMARY KEY,
                name TEXT NOT NULL,
                is_whitelist BOOL NOT NULL DEFAULT TRUE
            );
        ''')
        print("Done!")

        print("Creating Reminders table...", end = '')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS Reminders (
                remind_id SERIAL PRIMARY KEY,
                user_id INT8 NOT NULL,
                awake_time TIMESTAMP WITH TIME ZONE NOT NULL,
                message TEXT NOT NULL
            );
        ''')
        print("Done!")

    await conn.close()

if __name__ == "__main__":
    argc = len(sys.argv)
    _, secrets = load_info(sys.argv[1])
    asyncio.run(setup_database(secrets["user"], secrets["password"], secrets["database"], secrets["host"], secrets["port"]))
