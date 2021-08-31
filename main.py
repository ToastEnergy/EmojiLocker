import os

import aiohttp
import discord
from discord.ext import commands

import config
from utils import database

os.environ["JISHAKU_NO_UNDERSCORE"] = "True"
os.environ["JISHAKU_NO_DM_TRACEBACK"] = "True"
os.environ["JISHAKU_HIDE"] = "True"

DESCRIPTION = '''
What's Emoji Locker?
Emoji Locker can block emojis to only some roles, you can use it like to give exclusive emojis to the most ranked person or maybe in server's economy!
If you need any help join the support server https://discord.gg/TaJubW7
Privacy Policy : https://bit.ly/2ZLoLG1
'''


class LockHelp(commands.MinimalHelpCommand):
    async def send_bot_help(self, mapping):
        embed = discord.Embed(title="Emoji Locker", colour=discord.Colour.green(
        ), description=self.context.bot.description)
        embed.set_thumbnail(url=str(self.context.bot.user.avatar))
        commands = str()
        for x in [x for x in [self.context.bot.get_cog(c) for c in self.context.bot.cogs]]:
            commands_obj = [c for c in x.get_commands() if not c.hidden]
            if not (x.qualified_name == "Jishaku") and len(commands_obj) > 0:
                commands += f"\n__Category: **{x.qualified_name}**__\n"
                cog_c = str()
                for command in commands_obj:
                    if command.hidden:
                        continue
                    cog_c += f"`{self.context.prefix}{command.name}`, "
                commands += cog_c[:-2]
        embed.add_field(name="Commands", value=commands)
        embed.set_footer(
            text=f"Use {self.context.prefix}help <command> to learn about commands")
        await self.context.send(embed=embed)

    async def send_cog_help(self, cog):
        return await self.context.send("Command not found.")

    async def send_command_help(self, command):
        if command.hidden or command.cog_name == "Jishaku":
            return await self.context.send("Command not found.")
        embed = discord.Embed(title=f"Command help",
                              colour=discord.Colour.green())
        embed.set_thumbnail(url=str(self.context.bot.user.avatar))
        embed.add_field(name=command.name, value=f"""
        Usage: {self.get_command_signature(command)}
        Aliases: {", ".join([a for a in command.aliases]) or "None"}
        Category: {command.cog_name}
        ```{command.help}```
        """)
        await self.context.send(embed=embed)

    async def send_group_help(self, group):
        if group.hidden:
            return await self.context.send("Command not found.")
        embed = discord.Embed(title=f"Command group help",
                              colour=discord.Colour.green(), description=group.help)
        embed.set_thumbnail(url=str(self.context.bot.user.avatar))
        for command in group.commands:
            embed.add_field(name=command.name, value=f"""
            Usage: {self.get_command_signature(command)}
            Aliases: {", ".join([a for a in command.aliases]) or "None"}
            Category: {command.cog_name}
            ```{command.help}```
            """)
        await self.context.send(embed=embed)


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


class EmojiLocker(commands.AutoShardedBot):
    def __init__(self):
        super().__init__(command_prefix=self.get_custom_prefix)
        self.load_extension('jishaku')
        self.allowed_mentions = discord.AllowedMentions(
            everyone=False, replied_user=True, roles=False, users=False
        )
        self.description = DESCRIPTION
        self.help_command = LockHelp()
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
                if filename.endswith(".py") and not filename.startswith("_"):
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
