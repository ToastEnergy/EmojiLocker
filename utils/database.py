import asyncpg
import config


class Database:
    def __init__(self, conn=None):
        self.conn = conn

    async def connect(self):
        self.conn = await asyncpg.connect(
            host=config.host,
            port=config.port,
            user=config.user,
            database=config.database,
            password=config.password
        )
        await self.create_tables()

    async def create_tables(self):
        await self.conn.execute('''
CREATE TABLE IF NOT EXISTS guilds (id bigint NOT NULL, prefix character varying(12), PRIMARY KEY(id))
        ''')

    async def populate_cache(self, guilds_cache):
        data = await self.conn.fetch('SELECT * FROM guilds')

        guilds_cache.clear()
        for guild in data:
            guilds_cache[guild['id']] = data

    async def update_prefix(self, guild, prefix):
        query = '''
INSERT INTO guilds (id, prefix) VALUES ($1,$2)
ON CONFLICT (id) DO UPDATE SET prefix=$2
'''
        await self.conn.execute(query, guild, prefix)
