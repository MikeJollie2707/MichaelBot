'''Run this script once if the database or a table is missing.'''

import asyncio
import sys
import asyncpg

from main import load_info

async def create_table(conn: asyncpg.Connection, table_name: str, query: str):
    print(f"Creating {table_name} table...", end = '')
    try:
        await conn.execute(query)
    except asyncpg.DuplicateTableError:
        print(f"Table {table_name} already existed, moving on!")
    else:
        print("Done!")

async def setup_database(user, password, database, host, port):
    conn: asyncpg.Connection = await asyncpg.connect(
        host = host,
        port = port,
        user = user,
        password = password,
        database = database
    )

    try:
        await create_table(conn, "Guilds", """
            CREATE TABLE Guilds (
                id INT8 PRIMARY KEY,
                name TEXT NOT NULL,
                is_whitelist BOOL NOT NULL DEFAULT TRUE,
                prefix TEXT NOT NULL DEFAULT '$'
            );
        """)
        
        await create_table(conn, "GuildsLogs", """
            CREATE TABLE GuildsLogs (
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
        """)
        
        await create_table(conn, "Users", """
            CREATE TABLE Users (
                id INT8 PRIMARY KEY,
                name TEXT NOT NULL,
                is_whitelist BOOL NOT NULL DEFAULT TRUE,
                balance INT NOT NULL DEFAULT 0 CHECK (balance >= 0),
                world TEXT NOT NULL DEFAULT 'overworld',
                last_travel TIMESTAMP WITH TIME ZONE,
                daily_streak INT NOT NULL DEFAULT 0 CHECK (daily_streak >= 0),
                last_daily TIMESTAMP WITH TIME ZONE,
                CONSTRAINT world_type
                    CHECK (world IN ('overworld', 'nether', 'end'))
            );
        """)

        await create_table(conn, "Reminders", """
            CREATE TABLE Reminders (
                remind_id SERIAL PRIMARY KEY,
                user_id INT8 NOT NULL,
                awake_time TIMESTAMP WITH TIME ZONE NOT NULL,
                message TEXT NOT NULL
            );
        """)

        await create_table(conn, "Items", """
            CREATE TABLE Items (
                id TEXT PRIMARY KEY,
                sort_id INT NOT NULL,
                name TEXT UNIQUE NOT NULL,
                aliases TEXT[] DEFAULT ARRAY[]::TEXT[],
                emoji TEXT UNIQUE NOT NULL,
                description TEXT NOT NULL,
                rarity TEXT NOT NULL,
                buy_price INT CHECK (buy_price >= 0),
                sell_price INT NOT NULL CHECK (sell_price >= 0),
                durability INT CHECK (durability > 0)
            );
        """)

        await create_table(conn, "UserInventory", """
            CREATE TABLE UserInventory (
                user_id INT8 NOT NULL REFERENCES Users(id) ON UPDATE CASCADE ON DELETE CASCADE,
                item_id TEXT NOT NULL REFERENCES Items(id) ON UPDATE CASCADE ON DELETE CASCADE,
                amount INT NOT NULL CHECK (amount >= 0),
                PRIMARY KEY (user_id, item_id)
            );
        """)

        await create_table(conn, "UserEquipment", """
            CREATE TABLE UserEquipment (
                user_id INT8 NOT NULL REFERENCES Users(id) ON UPDATE CASCADE ON DELETE CASCADE,
                item_id TEXT NOT NULL REFERENCES Items(id) ON UPDATE CASCADE ON DELETE CASCADE,
                eq_type TEXT NOT NULL,
                remain_durability INT NOT NULL CHECK (remain_durability >= 0),
                PRIMARY KEY (user_id, item_id),
                CONSTRAINT equipment_type
                    CHECK (eq_type IN ('_pickaxe', '_sword', '_axe', '_potion'))
            );
        """)

        await create_table(conn, "ActiveTrades", """
            CREATE TABLE ActiveTrades (
                id INT NOT NULL,
                type TEXT NOT NULL,
                item_src TEXT NOT NULL,
                amount_src INT NOT NULL,
                item_dest TEXT NOT NULL,
                amount_dest INT NOT NULL,
                next_reset TIMESTAMP WITH TIME ZONE NOT NULL,
                hard_limit INT NOT NULL DEFAULT 15,
                PRIMARY KEY (id, type),
                CONSTRAINT trade_type
                    CHECK (type IN ('trade', 'barter'))
            );
        """)

        await create_table(conn, "Users_ActiveTrades", """
            CREATE TABLE Users_ActiveTrades (
                user_id INT8 NOT NULL REFERENCES Users(id) ON UPDATE CASCADE ON DELETE CASCADE,
                trade_id INT NOT NULL,
                trade_type TEXT NOT NULL,
                hard_limit INT NOT NULL,
                count INT NOT NULL DEFAULT 1 CHECK (count > 0),
                FOREIGN KEY (trade_id, trade_type) REFERENCES ActiveTrades(id, type) ON UPDATE CASCADE ON DELETE CASCADE,
                PRIMARY KEY (user_id, trade_id, trade_type)
            );
        """)

        await create_table(conn, "Badges", """
            CREATE TABLE Badges (
                id TEXT PRIMARY KEY,
                sort_id INT NOT NULL,
                name TEXT UNIQUE NOT NULL,
                emoji TEXT NOT NULL,
                description TEXT NOT NULL,
                requirement INT NOT NULL DEFAULT 0
            );
        """)

        await create_table(conn, "Users_Badges", """
            CREATE TABLE Users_Badges (
                user_id INT8 NOT NULL REFERENCES Users(id) ON UPDATE CASCADE ON DELETE CASCADE,
                badge_id TEXT NOT NULL REFERENCES Badges(id) ON UPDATE CASCADE ON DELETE CASCADE,
                badge_progress INT NOT NULL DEFAULT 0,
                PRIMARY KEY (user_id, badge_id)
            );
        """)

    except Exception as e:
        raise e
    finally:
        await conn.close()

if __name__ == "__main__":
    argc = len(sys.argv)
    _, secrets = load_info(sys.argv[1])
    asyncio.run(setup_database(secrets["user"], secrets["password"], secrets["database"], secrets["host"], secrets["port"]))
