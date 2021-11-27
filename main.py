import os

import aiohttp
import discord
from discord.ext import commands

import config
from utils import database, views

os.environ["JISHAKU_NO_UNDERSCORE"] = "True"
os.environ["JISHAKU_NO_DM_TRACEBACK"] = "True"
os.environ["JISHAKU_HIDE"] = "True"

DESCRIPTION = '''
This bot can whitelist the usage of **custom emojis** to server roles, making them **disappear** from the emoji picker!
This can be really useful in **server economy**, rewards etc...

To learn more, use the **dropdown** below

If you need any help join the **[support server](https://discord.gg/TaJubW7)**

**[Privacy Policy](https://bit.ly/2ZLoLG1)**
**[FAQ](https://godo)**
'''


class LockHelp(commands.HelpCommand):
    def __init__(self):
        super().__init__(verify_checks=False)

    def get_command_desc(self, command):
        r = f"""`{command.name}`
aliases : {",".join(command.aliases) or "No aliases"}
usage : {command.usage}
> {command.help or "No help provided"}
"""
        if isinstance(command, commands.Group):
            for x in command.commands:
                r += f"""
`{x.parent.name} {x.name}`
aliases : {",".join(x.aliases) or "No aliases"}
usage : {x.usage}
> {x.help}
"""

        return r

    def get_cog_desc(self, cog):
        r = ""
        for command in cog.get_commands():
            r += self.get_command_desc(command) + "\n"
        return r

    async def send_bot_help(self, mapping):
        embed = discord.Embed(title='Emoji Locker',
                              description=self.context.bot.description, color=config.color)
        embed.set_thumbnail(url=str(self.context.bot.user.display_avatar))
        embed.set_footer(text="Made with ♥ by Toast Energy")
        self.start_embed = embed
        view = views.OwnView(self.context)
        entries = [self.context.bot.get_cog(cog) for cog in self.context.bot.cogs if cog not in ["Jishaku","Events"]]
        view.add_item(views.HelpSelect(self, entries))
        await self.context.reply_embed(embed=embed, view=view)


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
            content = f'{og_content}{kwargs.pop("embed").description}\n\n{config.no_embeds_message}'
            return await self.send(content, **kwargs)
        else:
            return await self.send(*args, **kwargs)


class EmojiLocker(commands.AutoShardedBot):
    def __init__(self):
        super().__init__(command_prefix=self.get_custom_prefix, case_insensitive=True)
        self.load_extension('jishaku')
        self.allowed_mentions = discord.AllowedMentions(
            everyone=False, replied_user=True, roles=False, users=False
        )
        self.description = DESCRIPTION
        self.help_command = LockHelp()
        self.guilds_cache = {}
        self.tid = 0
        self._cd = commands.CooldownMapping.from_cooldown(
            1, 1.5, commands.BucketType.user)
        self.tracebacks = {}
        self.default_prefix = commands.when_mentioned_or(
            config.prefix+' ', config.prefix)

    async def login(self, *args, **kwargs):
        self.db = database.Database(self)
        await self.db.connect()
        await self.db.populate_cache(self.guilds_cache)
        self.session = aiohttp.ClientSession()
        for filename in os.listdir("./ext"):
            if filename.endswith(".py") and not filename.startswith("_"):
                self.load_extension(f"ext.{filename[:-3]}")
                print(f'Loaded {filename}')
        await super().login(*args, **kwargs)

    async def close(self, *args, **kwargs):
        await self.session.close()
        await super().close(*args, **kwargs)

    async def get_context(self, message, *, cls=EmojiContext):
        return await super().get_context(message, cls=cls)

    async def on_ready(self):
        print(f'logged in as {self.user}')

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

    async def get_persistent_roles(self, ctx):
        data = await self.db.get_roles(ctx.guild.id)
        res = list()
        to_remove = list()
        for role in data:
            resolved_role = ctx.guild.get_role(role['role_id'])
            if resolved_role:
                res.append(resolved_role)
            else:
                to_remove.append(role['role_id'])
        if to_remove:
            await self.db.delete_roles(to_remove)
        return res


bot = EmojiLocker()
bot.run(config.discord_token)
