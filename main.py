import discord
import config
import os
from utils import database
from discord.ext import commands

os.environ["JISHAKU_NO_UNDERSCORE"] = "True"
os.environ["JISHAKU_NO_DM_TRACEBACK"] = "True"
os.environ["JISHAKU_HIDE"] = "True"


class EmojiLocker(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=self.get_custom_prefix)
        self.load_extension('jishaku')
        self.guilds_cache = {}
        self.first_ready = True
        self.default_prefix = commands.when_mentioned_or(
            config.prefix+' ', config.prefix)

    async def login(self, *args, **kwargs):
        self.db = database.Database()
        await self.db.connect()
        await self.db.populate_cache(self.guilds_cache)
        await super().login(*args, **kwargs)

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
        elif not data.get('prefix'):
            return self.default_prefix(bot, message)
        else:
            return commands.when_mentioned_or(data.get('prefix')+' ', data.get('prefix'))(bot, message)


bot = EmojiLocker()
bot.run(config.discord_token)
