import inspect
import itertools
import random

import discord
from discord.ext import commands
from utils import views


class Core(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.guild_only()
    @commands.has_guild_permissions(manage_emojis=True)
    @commands.bot_has_permissions(manage_emojis=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.max_concurrency(1, commands.BucketType.user)
    async def lock(self, ctx, emoji: discord.Emoji, *, roles):

        if emoji.guild != ctx.guild:
            return await ctx.reply('This emoji appears to be from another server')
        roles = roles.split(',')

        # Raises commands.BadArgument if any of the roles are invalid
        roles = set([await commands.RoleConverter().convert(ctx, role.strip()) for role in roles])

        await emoji.edit(name=emoji.name, roles=roles)

        description = f'''
🔒 I have succesfully locked the '{emoji.name}' emoji.\n
ℹ️ Now only the people with at least one of the roles that you specified ({', '.join([r.mention for r in roles])}) will be able to use the emoji'''

        embed = discord.Embed(title='Emoji succesfully locked',
                              description=description, color=0x2ecc71)
        embed.set_footer(
            text="If you can't use the emoji but you have at least one of these roles try to fully restart your Discord app")
        embed.set_thumbnail(url=emoji.url)
        await ctx.reply_embed(embed=embed)

    @commands.command()
    @commands.guild_only()
    @commands.has_guild_permissions(manage_emojis=True)
    @commands.bot_has_permissions(manage_emojis=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.max_concurrency(1, commands.BucketType.user)
    async def unlock(self, ctx, emoji: discord.Emoji):

        if emoji.guild != ctx.guild:
            return await ctx.reply('This emoji appears to be from another server')

        await emoji.edit(name=emoji.name, roles=[])

        description = f'''
🔒 I have succesfully unlocked the '{emoji.name}' emoji.\n
ℹ️ Now everyone will be able to use the emoji'''
        if not ctx.channel.permissions_for(ctx.guild.me).embed_links:
            return await ctx.reply(description+'\n\nPlease consider giving me the embed links permissions to see nicer messages')

        embed = discord.Embed(title='Emoji succesfully locked',
                              description=description, color=0x2ecc71)
        embed.set_footer(
            text="If you can't use the emoji try to fully restart your Discord app")
        embed.set_thumbnail(url=emoji.url)
        await ctx.reply_embed(embed=embed)

    @commands.command()
    @commands.guild_only()
    @commands.has_guild_permissions(manage_emojis=True)
    @commands.bot_has_permissions(manage_emojis=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.max_concurrency(1, commands.BucketType.user)
    async def unlockall(self, ctx):
        ctx.emojis = [
            emoji for emoji in ctx.guild.emojis if len(emoji.roles) > 0]
        ctx.roles = []
        if len(ctx.emojis) == 0:
            return await ctx.reply('There are no locked emojis.')
        embed = discord.Embed(title='Unlocking all emojis!',
                              description=f'You are about to unlock {len(ctx.emojis)} emojis, continue?', color=discord.Color.red())
        ctx.confirm_embed = discord.Embed(title='Emojis succesfully unlocked', color=discord.Color.green(),
                                          description=f'''🔓 I have succesfully unlocked all of your server emojis.\n
ℹ️ Now everyone will be able to use all emojis in your server''').set_footer(
            text='If you can\'t use the emojis try to fully restart your Discord app')
        view = views.BaseView(ctx)
        await ctx.reply_embed(embed=embed, view=view)
        await view.wait()

    @commands.command(usage='<role,role...>')
    @commands.guild_only()
    @commands.has_guild_permissions(manage_emojis=True)
    @commands.bot_has_permissions(manage_emojis=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.max_concurrency(1, commands.BucketType.user)
    async def lockall(self, ctx, *, roles):

        roles = roles.split(',')
        ctx.roles = set([await commands.RoleConverter().convert(ctx, role.strip()) for role in roles])
        embed = discord.Embed(title='Locking all emojis!', description='''Do you want to **keep** the roles in the existent setup or overwrite them?

If you select **keep** an emoji already locked to @role1  will be locked to @role1 + the roles that you specified in the command

if you select **overwrite** it will be locked only to the roles that you just specified.
''', color=discord.Color.red())
        view = views.LockallView(ctx)
        await ctx.reply_embed(embed=embed, view=view)
        await view.wait()

    @commands.command(usage='<emoji,emoji...> | <role,role...>')
    @commands.guild_only()
    @commands.has_guild_permissions(manage_emojis=True)
    @commands.bot_has_permissions(manage_emojis=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.max_concurrency(1, commands.BucketType.user)
    # None because hardcoding :tm:
    async def multiple(self, ctx, *, args=None):

        # Not using commands.Greedy because the parsing ambiguities ruins the overall UX
        if not args:
            raise commands.MissingRequiredArgument(inspect.Parameter(
                name='emojis', kind=inspect.Parameter.POSITIONAL_ONLY))
        args = args.split("|")
        if len(args) == 1:
            raise commands.MissingRequiredArgument(inspect.Parameter(
                name='roles', kind=inspect.Parameter.POSITIONAL_ONLY))
        emojis = args[0].split(',')
        roles = args[1].split(',')
        ctx.emojis = set([await commands.EmojiConverter().convert(ctx, emoji.strip()) for emoji in emojis])
        ctx.roles = set([await commands.RoleConverter().convert(ctx, role.strip()) for role in roles])
        view = views.BaseView(ctx)
        ctx.confirm_embed = discord.Embed(title='Emojis succesfully locked', color=discord.Color.green(),
                                          description=f'''🔓 I have succesfully locked {len(ctx.emojis)} emojis\n
ℹ️ Now only the people with at least one of the roles that you specified ({','.join([r.mention for r in ctx.roles])}) will be able to use the emojis''')
        ctx.confirm_embed.set_footer(
            text='If you can\'t use the emojis try to fully restart your Discord app')
        await ctx.reply_embed(f'You are about to lock {len(ctx.emojis)} emojis to these roles : {", ".join([r.mention for r in ctx.roles])}\nContinue?',
                              view=view)

        await view.wait()

    @commands.command(usage='<emoji,emoji...>')
    @commands.guild_only()
    @commands.has_guild_permissions(manage_emojis=True)
    @commands.bot_has_permissions(manage_emojis=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.max_concurrency(1, commands.BucketType.user)
    async def massunlock(self, ctx, *, emojis):

        emojis = emojis.split(",")
        ctx.emojis = list(filter(lambda e: (len(e.roles) > 0),
                                 set([await commands.EmojiConverter().convert(ctx, emoji.strip()) for emoji in emojis])))
        ctx.roles = []
        view = views.BaseView(ctx)
        ctx.confirm_embed = discord.Embed(title='Emojis succesfully unlocked', color=discord.Color.green(),
                                          description=f'''🔓 I have succesfully unlocked {len(ctx.emojis)} emojis\n
ℹ️ Now everyone will be able to use the emojis''')
        ctx.confirm_embed.set_footer(
            text='If you can\'t use the emojis try to fully restart your Discord app')
        await ctx.reply_embed(f'You are about to unlock {len(ctx.emojis)} emojis\nContinue?',
                              view=view)

        await view.wait()

    @commands.command()
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def emojiinfo(self, ctx, *, emoji: discord.Emoji):
        embed = discord.Embed(title=emoji.name)
        embed.colour = discord.Colour.from_hsv(random.random(), 1, 1)
        embed.set_thumbnail(url=str(emoji.url))
        embed.description = f"""
**Animated?** : {emoji.animated}
**Roles** : {", ".join([x.mention for x in emoji.roles]) or '@everyone'}
**Guild** : {emoji.guild.name} [{emoji.guild.id}]
**ID** : {emoji.id}
**Available** : {emoji.available}
**Managed by an integration?** : {emoji.managed}
**Created at** : {emoji.created_at.strftime("%m/%d/%Y, %H:%M:%S")}
**Download link** : [Click here]({str(emoji.url)})
        """
        await ctx.reply_embed(embed=embed)

    @commands.command()
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.max_concurrency(1, commands.BucketType.user)
    async def packs(self, ctx):
        ctx.packs = []
        ctx.keys = []
        def func(x): return x.roles
        for k, g in itertools.groupby(sorted(ctx.guild.emojis, key=func), func):
            ctx.packs.append(list(g))
            ctx.keys.append(k)

        ctx.embed = discord.Embed(
            title='Packs', colour=discord.Colour.from_hsv(random.random(), 1, 1))
        ctx.paginator = commands.Paginator(prefix='', suffix='', linesep='')
        c = 0
        for x in ctx.packs:
            ctx.paginator.add_line('\n\n')
            ctx.paginator.add_line(
                f"> **{(', '.join([role.name for role in ctx.keys[c]])) or '@everyone'}**")
            c += 1
            ctx.paginator.add_line('\n')
            for em in x:
                ctx.paginator.add_line(f"{em} ")
        ctx.embed.description = ctx.paginator.pages[0]
        ctx.embed.set_footer(text=f'Page 1/{len(ctx.paginator.pages)}')
        view = views.PacksView(ctx) if len(ctx.paginator.pages) > 1 else None
        ctx.sent_message = await ctx.reply_embed(embed=ctx.embed, view=view)
        if view:
            await view.wait()


def setup(bot):
    bot.add_cog(Core(bot))
