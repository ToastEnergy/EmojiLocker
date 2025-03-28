"""
MIT License

Copyright (c) 2022 chickenmatty

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import os

import aiohttp
import discord
from discord.ext import commands

import config
from utils import database, views

os.environ['JISHAKU_NO_UNDERSCORE'] = 'True'
os.environ['JISHAKU_NO_DM_TRACEBACK'] = 'True'
os.environ['JISHAKU_HIDE'] = 'True'

DESCRIPTION = '''
This bot can whitelist the usage of **custom emojis** to server roles, making them **disappear** from the emoji picker!
This can be really useful in **server economy**, rewards etc...

To learn more, use the **dropdown** below

If you need any help join the **[support server](https://discord.gg/TaJubW7)**

**[Privacy Policy](https://bit.ly/2ZLoLG1)**
**[Top.gg](https://top.gg/bot/609087387695316992/)**
'''

INTENTS = discord.Intents.default()


class EmojiLocker(commands.AutoShardedBot):
    def __init__(self):
        super().__init__(command_prefix=commands.when_mentioned, case_insensitive=True,
                         activity=discord.Game(name=config.status), intents=INTENTS)
        self.allowed_mentions = discord.AllowedMentions(
            everyone=False, replied_user=True, roles=False, users=False
        )
        self.description = DESCRIPTION
        self.first_ready = True
        self.guilds_cache = {}
        self.tid = 0
        self._cd = commands.CooldownMapping.from_cooldown(
            1, 1.5, commands.BucketType.user)
        self.tracebacks = {}

    async def login(self, *args, **kwargs):
        self.db = database.Database(self)
        await self.db.connect()
        await self.db.populate_cache(self.guilds_cache)
        self.session = aiohttp.ClientSession()
        await super().login(*args, **kwargs)

    async def close(self, *args, **kwargs):
        await self.session.close()
        await super().close(*args, **kwargs)

    async def setup_hook(self):
        await self.load_extension('jishaku')


    async def on_ready(self):
        print(f'logged in as {self.user}')
        if self.first_ready:
            for filename in os.listdir('./ext'):
                if filename.endswith('.py') and not filename.startswith('_'):
                    await self.load_extension(f'ext.{filename[:-3]}')
                    print(f'Loaded {filename}')
            self.first_ready = False
            
    async def get_persistent_roles(self, guild: discord.Guild):
        data = await self.db.get_roles(guild.id)
        res = list()
        to_remove = list()
        for role in data:
            resolved_role = guild.get_role(role['role_id'])
            if resolved_role:
                res.append(resolved_role)
            else:
                to_remove.append(role['role_id'])
        if to_remove:
            await self.db.delete_roles(to_remove)
        return res


bot = EmojiLocker()
bot.run(config.discord_token)
