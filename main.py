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


class LockHelp(commands.HelpCommand):
    def __init__(self):
        super().__init__(verify_checks=False)

    def get_command_desc(self, command):
        r = f'''`{command.name}`
aliases : {", ".join(command.aliases) or "No aliases"}
usage : {command.usage}
> {command.help or "No help provided"}
'''
        if isinstance(command, commands.Group):
            for x in command.commands:
                r += f'''
`{x.parent.name} {x.name}`
aliases : {",".join(x.aliases) or "No aliases"}
usage : {x.usage}
> {x.help}
'''

        return r

    def get_cog_desc(self, cog):
        r = ""
        for command in cog.get_commands():
            r += self.get_command_desc(command) + '\n'
        return r

    async def send_bot_help(self, mapping):
        embed = discord.Embed(title='Emoji Locker',
                              description=self.context.bot.description, color=config.color)
        embed.set_thumbnail(url=str(self.context.bot.user.display_avatar))
        embed.set_footer(text='Made with ??? by Toast Energy')
        self.start_embed = embed
        view = views.OwnView(self.context)
        entries = [self.context.bot.get_cog(cog) for cog in self.context.bot.cogs if cog not in ['Jishaku', 'Events', 'BotLists']]
        view.add_item(views.HelpSelect(self, entries))
        button = discord.ui.Button(
            style=discord.ButtonStyle.url, url="https://top.gg/bot/609087387695316992/vote", label='Upvote the bot')
        view.add_item(button)
        await self.context.reply_embed(embed=embed, view=view)

    async def send_command_help(self, command):
        embed = discord.Embed(description=self.get_command_desc(command), color=config.color)
        await self.context.reply_embed(embed=embed)

    async def send_group_help(self, group):
        return await self.send_command_help(group)


class EmojiContext(commands.Context):
    def __init__(self, **attrs):
        super().__init__(**attrs)

    async def reply_embed(self, *args, **kwargs):
        if self.channel.permissions_for(self.me).read_message_history:
            try:
                return await self.send_embed(*args, **kwargs, reference=self.message)
            except discord.errors.HTTPException:
                return await self.send_embed(*args, **kwargs)
        else:
            return await self.send_embed(*args, **kwargs)

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
        super().__init__(command_prefix=self.get_custom_prefix, case_insensitive=True, activity=discord.Game(name=config.status))
        self.load_extension('jishaku')
        self.allowed_mentions = discord.AllowedMentions(
            everyone=False, replied_user=True, roles=False, users=False
        )
        self.description = DESCRIPTION
        self.first_ready = True
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
            for filename in os.listdir('./ext'):
                if filename.endswith('.py') and not filename.startswith('_'):
                    self.load_extension(f'ext.{filename[:-3]}')
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
