# This script should only run once, and only when:
# - You have an empty database
# - One or more tables are missing somehow
# - There's a change in table's structure (prefer ALTER TABLE instead)

import asyncpg
import asyncio
import sys

from bot import load_info

async def setup(secrets : dict):
    conn = await asyncpg.connect(
        dsn = secrets["dsn"],
        host = secrets["host"],
        port = secrets["port"],
        user = secrets["user"],
        password = secrets["password"],
        database = secrets["database"]
    )

    async with conn.transaction():
        print("Creating BotCommands table...", end = '')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS BotCommands (
                name TEXT PRIMARY KEY,
                aliases TEXT[]
            );
        ''')
        print("Done!")

        print("Creating DUsers table...", end = '')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS DUsers (
                id INT8 PRIMARY KEY,
                name TEXT NOT NULL,
                is_whitelist BOOL DEFAULT TRUE,
                money INT8 DEFAULT 0,
                last_daily TIMESTAMP,
                streak_daily INT4 DEFAULT 0,
                world INT4 DEFAULT 0,
                last_move TIMESTAMP
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
                enable_log BOOL DEFAULT FALSE,
                log_channel INT8 NOT NULL DEFAULT 0,
                enable_welcome BOOL DEFAULT FALSE,
                welcome_channel INT8 NOT NULL DEFAULT 0,
                welcome_text TEXT NOT NULL DEFAULT ''
            );
        ''')
        print("Done!")

        print("Creating DUsers_DGuilds table...", end = '')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS DUsers_DGuilds (
                user_id INT8 NOT NULL REFERENCES DUsers(id) ON UPDATE CASCADE ON DELETE CASCADE,
                guild_id INT8 NOT NULL REFERENCES DGuilds(id) ON UPDATE CASCADE ON DELETE CASCADE,
                PRIMARY KEY (user_id, guild_id)
            );
        ''')
        print("Done!")

        print("Creating DGuilds_ARoles table...", end = '')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS DGuilds_ARoles (
                guild_id INT8 NOT NULL REFERENCES DGuilds(id) ON UPDATE CASCADE ON DELETE CASCADE,
                role_id INT8 NOT NULL,
                description TEXT,
                PRIMARY KEY(guild_id, role_id)
            );
        ''')
        print("Done!")

        print("Creating Items table...", end = '')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS Items (
                id TEXT PRIMARY KEY,
                emoji TEXT NOT NULL UNIQUE,
                inner_sort INT4,
                name TEXT NOT NULL,
                rarity TEXT NOT NULL,
                buy_price INT,
                sell_price INT,
                durability INT,
                description TEXT NOT NULL
            );
        ''')
        print("Done!")

        print("Creating DUsers_Items table...", end = '')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS DUsers_Items (
                user_id INT8 NOT NULL REFERENCES DUsers(id) ON UPDATE CASCADE ON DELETE CASCADE,
                item_id TEXT NOT NULL REFERENCES Items(id) ON UPDATE CASCADE ON DELETE CASCADE,
                quantity INT4 NOT NULL DEFAULT 0,
                PRIMARY KEY (user_id, item_id)
            );
        ''')
        print("Done!")

        print("Creating DUsers_ActiveTools table...", end = '')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS DUsers_ActiveTools (
                user_id INT8 NOT NULL REFERENCES DUsers (id) ON UPDATE CASCADE ON DELETE CASCADE,
                item_id TEXT NOT NULL REFERENCES Items (id) ON UPDATE CASCADE ON DELETE CASCADE,
                durability_left INT4 NOT NULL,
                PRIMARY KEY (user_id, item_id)
            )
        ''')
        print("Done!")

        print("Creating DUsers_ActivePortals...", end = '')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS DUsers_ActivePortals (
                user_id INT8 NOT NULL REFERENCES DUsers (id) ON UPDATE CASCADE ON DELETE CASCADE,
                item_id TEXT NOT NULL REFERENCES Items (id) ON UPDATE CASCADE ON DELETE CASCADE,
                remain_uses INT4 NOT NULL DEFAULT 0,
                PRIMARY KEY (user_id, item_id)
            )
        ''')
        print("Done!")

        print("Creating DUsers_ActivePotions...", end = '')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS DUsers_ActivePotions (
                user_id INT8 NOT NULL REFERENCES DUsers (id) ON UPDATE CASCADE ON DELETE CASCADE,
                item_id TEXT NOT NULL REFERENCES Items (id) ON UPDATE CASCADE ON DELETE CASCADE,
                remain_uses INT4 NOT NULL DEFAULT 0,
                PRIMARY KEY (user_id, item_id)
            )
        ''')
        print("Done!")

        print("Creating Badges table...", end = '')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS Badges (
                id TEXT PRIMARY KEY,
                emoji TEXT NOT NULL,
                inner_sort INT4,
                name TEXT NOT NULL,
                description TEXT NOT NULL
            )
        ''')
        print("Done!")

        print("Creating DUsers_Badges table...", end = '')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS DUsers_Badges (
                user_id INT8 NOT NULL REFERENCES DUsers (id) ON UPDATE CASCADE ON DELETE CASCADE,
                badge_id TEXT NOT NULL REFERENCES Badges (id) ON UPDATE CASCADE ON DELETE CASCADE
            )
        ''')
        print("Done!")

        print("Creating DNotify table...", end = '')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS DNotify (
                id SERIAL PRIMARY KEY,
                user_id INT8 NOT NULL REFERENCES DUsers (id) ON UPDATE CASCADE,
                awake_time TIMESTAMP NOT NULL,
                message TEXT NOT NULL
            );
        ''')
        print("Done!")

        print("Creating DMembers_Tempmute...", end = '')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS DMembers_Tempmute (
                user_id INT8 NOT NULL REFERENCES DUsers (id) ON UPDATE CASCADE ON DELETE CASCADE,
                guild_id INT8 NOT NULL REFERENCES DGuilds (id) ON UPDATE CASCADE ON DELETE CASCADE,
                expire TIMESTAMP NOT NULL,
                PRIMARY KEY(user_id, guild_id)
            );
        ''')
        print("Done!")

        print("Creating DGuilds_CCommand...", end = '')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS DGuilds_CCommand (
                guild_id INT8 NOT NULL REFERENCES DGuilds (id) ON UPDATE CASCADE ON DELETE CASCADE,
                name TEXT NOT NULL,
                description TEXT,
                message TEXT,
                channel INT8,
                is_reply BOOL DEFAULT FALSE,
                addroles INT8[],
                rmvroles INT8[],
                PRIMARY KEY(guild_id, name)
            );
        ''')
        print("Done!")
    
    print("Finished setting up tables.")
    await conn.close()


bot_info, secrets = load_info(sys.argv[1])
asyncio.run(setup(secrets))
