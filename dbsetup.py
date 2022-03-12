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
        print("Creating default_commands table...", end = '')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS default_commands (
                name TEXT PRIMARY KEY
            );
        ''')
        print("Done!")

        print("Creating guilds table...")
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS guilds (
                id INT8 PRIMARY KEY,
                name TEXT NOT NULL,
                is_whitelist BOOL DEFAULT TRUE,
                prefix TEXT NOT NULL DEFAULT '$',
                enable_log BOOL DEFAULT FALSE
            );
        ''')
        print("Done!")

    await conn.close()

if __name__ == "__main__":
    argc = len(sys.argv)
    _, secrets = load_info(sys.argv[1])
    asyncio.run(setup_database(secrets["user"], secrets["password"], secrets["database"], secrets["host"], secrets["port"]))
