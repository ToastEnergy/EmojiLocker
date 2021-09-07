import asyncpg
import config


class Database:
    def __init__(self, bot):
        self.bot = bot
        self.conn = None

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
CREATE TABLE IF NOT EXISTS guilds (guild_id bigint NOT NULL, prefix character varying(12), PRIMARY KEY(guild_id));
CREATE TABLE IF NOT EXISTS roles (guild_id bigint, role_id bigint, PRIMARY KEY(role_id), FOREIGN KEY(guild_id) REFERENCES "guilds"("guild_id") ON DELETE CASCADE)
        ''')

    async def populate_cache(self, guilds_cache):
        data = await self.conn.fetch('SELECT * FROM guilds')
        guilds_cache.clear()
        for guild in data:
            guilds_cache[guild['guild_id']] = dict(guild)

    async def update_prefix(self, guild, prefix):
        query = '''
INSERT INTO guilds (guild_id, prefix) VALUES ($1,$2)
ON CONFLICT (guild_id) DO UPDATE SET prefix=$2
'''
        if not hasattr(self, 'update_prefix_stmnt'):
            self.update_prefix_stmnt = await self.conn.prepare(query)
        await self.update_prefix_stmnt.fetch(guild, prefix)

    async def add_roles(self, guild, roles):
        if guild not in self.bot.guilds_cache:
            await self.conn.execute("INSERT INTO GUILDS (guild_id) VALUES ($1)", guild)
            self.bot.guilds_cache[guild] = {'guild_id': guild}
        query = '''
INSERT INTO roles (guild_id, role_id) VALUES  ($1,$2)
'''
        if not hasattr(self, 'add_roles_stmnt'):
            self.add_roles_stmnt = await self.conn.prepare(query)
        await self.add_roles_stmnt.executemany([(guild, role) for role in roles])

    async def delete_roles(self, roles):
        query = '''
DELETE FROM roles WHERE role_id=$1'''
        await self.conn.executemany(query, [(role,) for role in roles])

    async def get_roles(self, guild):
        if not hasattr(self, 'get_role_stmnt'):
            self.get_role_stmnt = await self.conn.prepare('''
            SELECT role_id FROM roles WHERE guild_id=$1''')
        return await self.get_role_stmnt.fetch(guild)

    async def get_guild(self, guild):
        query = '''
SELECT guilds.guild_id, guilds.prefix, array(select role_id from roles where roles.guild_id=$1) as roles
FROM guilds WHERE guilds.guild_id=$1
'''
        if not hasattr(self, 'get_guild_stmnt'):
            self.get_guild_stmnt = await self.conn.prepare(query)
        return await self.get_guild_stmnt.fetchrow(guild)
