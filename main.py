import os

import aiohttp
import discord
from discord.ext import commands

import config
from utils import database

os.environ["JISHAKU_NO_UNDERSCORE"] = "True"
os.environ["JISHAKU_NO_DM_TRACEBACK"] = "True"
os.environ["JISHAKU_HIDE"] = "True"


class EmojiContext(commands.Context):
    def __init__(self, **attrs):
        super().__init__(**attrs)

    async def reply_embed(self, *args, **kwargs):
        return await self.send_embed(*args, **kwargs, reference=self.message)

    async def send_embed(self, *args, **kwargs):
        if not self.channel.permissions_for(self.me).embed_links:
            try:
                og_content = kwargs.pop('content', args[0])
                og_content += '\n\n'
            except:
                og_content = ''

            content = f'{og_content}{kwargs.pop("embed").description}{config.no_embeds_message}'
            return await self.send(content, **kwargs)
        else:
            return await self.send(*args, **kwargs)


class EmojiLocker(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=self.get_custom_prefix)
        self.load_extension('jishaku')
        self.allowed_mentions = discord.AllowedMentions(
            everyone=False, replied_user=True, roles=False, users=False
        )
        self.guilds_cache = {}
        self.tid = 0
        self.tracebacks = {}
        self.first_ready = True
        self.default_prefix = commands.when_mentioned_or(
            config.prefix+' ', config.prefix)

    async def login(self, *args, **kwargs):
        self.db = database.Database()
        await self.db.connect()
        await self.db.populate_cache(self.guilds_cache)
        self.session = aiohttp.ClientSession()
        await super().login(*args, **kwargs)

    async def close(self, *args, **kwargs):
        await self.session.close()
        await super().close(*args, **kwargs)

    async def get_context(self, message, *, cls=EmojiContext):
        return await super().get_context(message, cls=cls)

    async def on_ready(self):
        print(f'logged in as {self.user}')
        if self.first_ready:
            self.first_ready = False
            for filename in os.listdir("./ext"):
                if filename.endswith(".py"):
                    self.load_extension(f"ext.{filename[:-3]}")
                    print(f'Loaded {filename}')

    async def get_custom_prefix(self, bot, message):
        if not message.guild:
            return self.default_prefix(bot, message)

        data = self.guilds_cache.get(message.guild.id)
        if not data:
            return self.default_prefix(bot, message)
        if not data.get('prefix'):
            return self.default_prefix(bot, message)
        else:
            return commands.when_mentioned_or(data.get('prefix')+' ', data.get('prefix'))(bot, message)


bot = EmojiLocker()
bot.run(config.discord_token)
