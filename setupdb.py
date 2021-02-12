import asyncpg
import json
import asyncio
import sys

from bot import setup as regular_setup

async def setup(secrets : dict):
    conn = await asyncpg.connect(
        host = secrets["host"],
        user = secrets["user"],
        password = secrets["password"],
        database = secrets["database"]
    )

    async with conn.transaction():
        print("Creating DUsers table...", end = '')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS DUsers (
                id INT8 PRIMARY KEY,
                name TEXT NOT NULL,
                is_whitelist BOOL DEFAULT TRUE,
                money INT8 DEFAULT 0,
                last_daily TIMESTAMP,
                streak_daily INT4 DEFAULT 0
            );
        ''')
        print("Done!")
        
        print("Creating DGuilds table...", end = '')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS DGuilds (
                id INT8 PRIMARY KEY,
                name TEXT NOT NULL,
                is_whitelist BOOL DEFAULT TRUE,
                prefix TEXT DEFAULT '$',
                autorole_list INT8[],
                customcmd_list TEXT[]
            );
        ''')
        print("Done!")

        print("Creating DUsers_DGuilds table...", end = '')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS DUsers_DGuilds (
                user_id INT8 NOT NULL REFERENCES DUsers(id) ON UPDATE CASCADE ON DELETE CASCADE,
                guild_id INT8 NOT NULL REFERENCES DGuilds(id) ON UPDATE CASCADE ON DELETE CASCADE,
                tempmute_end TIMESTAMP,
                PRIMARY KEY (user_id, guild_id)
            );
        ''')
        print("Done!")

        print("Creating Items table...", end = '')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS Items (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                emoji TEXT NOT NULL
            );
        ''')
        print("Done!")

        print("Creating DUsers_Items table...", end = '')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS DUsers_Items (
                user_id INT8 NOT NULL REFERENCES DUsers(id) ON UPDATE CASCADE ON DELETE CASCADE,
                item_id SERIAL REFERENCES Items(id) ON UPDATE CASCADE ON DELETE CASCADE,
                quantity INT4 DEFAULT 0
            );
        ''')
        print("Done!")
    
    print("Finished setting up tables.")
    await conn.close()


bot_info, secrets = regular_setup(sys.argv[1])
asyncio.run(setup(secrets))