import traceback
from datetime import datetime

import config
import discord
from discord.ext import commands
from utils import views

# True means that we like the libs error message
errors = {
    commands.CheckFailure: True,
    commands.UserInputError: True,
    commands.EmojiNotFound: 'Emoji "{argument}" not found, is this a default emoji?',
    commands.RoleNotFound: True,
    commands.CommandOnCooldown: True,
    commands.MaxConcurrencyReached: 'You are already using a command, please wait for it to finish'
}


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.webhook = discord.Webhook.from_url(
            config.error_webhook, session=bot.session)
        self.commands_webhook = discord.Webhook.from_url(
            config.commands_webhook, session=bot.session)
        self.guilds_webhook = discord.Webhook.from_url(
            config.guilds_webhook, session=bot.session)

    async def bot_check(self, ctx):
        if not ctx.author.id in self.bot.owner_ids:
            bucket = self.bot._cd.get_bucket(ctx.message)
            retry_after = bucket.update_rate_limit()
            if retry_after:
                raise commands.CommandOnCooldown(
                    bucket, retry_after, type=commands.BucketType.user)
        return True

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return
        traceback_ = traceback.format_exception(
            type(error), error, error.__traceback__)
        invoke = ctx.message.content
        if len(invoke) > 800:
            invoke = invoke[:800] + '...'
        emb = discord.Embed()
        emb.add_field(name='Message',
                      value=f'`{invoke}` (`{ctx.message.id}`)', inline=False)
        emb.add_field(
            name='Author', value=f'`{str(ctx.author)}` (`{ctx.author.id}`)', inline=False)
        if ctx.guild:
            emb.add_field(
                name='Channel', value=f'`#{ctx.channel.name}` (`{ctx.channel.id}`)', inline=False)
            emb.add_field(
                name='Guild', value=f'`{ctx.guild.name}` (`{ctx.guild.id}`)', inline=False)
            if ctx.guild.icon:
                emb.set_thumbnail(url=str(ctx.guild.icon))
        else:
            emb.add_field(name='Channel', value=f'`DM Channel`', inline=False)
        time = round(datetime.timestamp(datetime.now()))
        emb.add_field(name='When', value=f'<t:{time}:f>', inline=False)
        emb.add_field(name='Error', value=f'```py\n{str(error)}\n```')
        emb.set_author(name=str(ctx.author),
                       icon_url=str(ctx.author.display_avatar))
        color = discord.Color.red()
        UNKNOWN_ERROR = f'An unhandled error occurred, please report this to the developers. Error code : `{self.bot.tid}`'
        self.bot.tracebacks[self.bot.tid] = traceback_
        self.bot.tid += 1
        base_error = errors.get(type(error))
        if base_error is True:
            description = str(error)
        elif base_error is None:
            parent_err = errors.get(type(error).__bases__[0])
            if parent_err is True:
                description = str(error)
            elif parent_err is None:
                description = UNKNOWN_ERROR
                color = discord.Color.dark_magenta()

            else:
                description = parent_err
        else:
            description = base_error
        description = description.format(**error.__dict__)
        ctx.embed = discord.Embed(
            title="Something went wrong.", color=color, description=description)
        ctx.embed.set_author(name=str(ctx.author),
                             icon_url=str(ctx.author.display_avatar))
        emb.color = color
        await self.webhook.send(f'Traceback ID : {self.bot.tid}', embed=emb)
        try:
            ctx.sent_message = await ctx.reply_embed(embed=ctx.embed, view=views.SupportView(ctx))
        except discord.errors.Forbidden:
            pass

    @commands.command(hidden=True)
    @commands.is_owner()
    async def vt(self, ctx, tid: int):
        paginator = commands.Paginator(suffix='```', prefix='```')
        tracebacks = self.bot.tracebacks[tid]
        for x in tracebacks:
            paginator.add_line(x)
        for x in paginator.pages:
            embed = discord.Embed(
                title='Traceback inspector', color=discord.Color.red(), description=x)
            await ctx.reply_embed(embed=embed)

    @commands.Cog.listener()
    async def on_command(self, ctx):
        time = round(datetime.timestamp(datetime.now()))
        emb = discord.Embed(color=discord.Color.green())
        emb.add_field(
            name='Message', value=f'`{ctx.message.content}` (`{ctx.message.id}`)', inline=False)
        emb.add_field(
            name='Author', value=f'`{str(ctx.author)}` (`{ctx.author.id}`)', inline=False)
        if ctx.guild:
            emb.add_field(
                name='Channel', value=f'`#{ctx.channel.name}` (`{ctx.channel.id}`)', inline=False)
            emb.add_field(
                name='Guild', value=f'`{ctx.guild.name}` (`{ctx.guild.id}`)', inline=False)
            if ctx.guild.icon:
                emb.set_thumbnail(url=str(ctx.guild.icon))
        else:
            emb.add_field(name='Channel', value=f'`DM Channel`', inline=False)
        emb.add_field(name='When', value=f'<t:{time}:f>', inline=False)
        emb.set_author(name=str(ctx.author),
                       icon_url=str(ctx.author.display_avatar))
        await self.commands_webhook.send(embed=emb)

    @commands.Cog.listener()
    async def on_guild_join(self, guild : discord.Guild):
        owner = await self.bot.fetch_user(guild.owner_id)
        emb = discord.Embed(title='New Server', color=config.color)
        emb.set_author(name=guild.name)
        if guild.icon:
            emb.set_thumbnail(url=str(guild.icon))
        emb.add_field(name='ID', value=f'`{guild.id}`')
        emb.add_field(name='Members', value=guild.member_count)
        emb.add_field(name='Owner', value=f'`{str(owner)}` (`{owner.id}`)', inline=False)
        if guild.banner:
            emb.set_image(url=str(guild.banner))
        await self.guilds_webhook.send(embed=emb)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        emb = discord.Embed(title="Left a server", colour=config.color_red)
        emb.set_author(name=guild.name)
        if guild.icon:
            emb.set_thumbnail(url=str(guild.icon))
        emb.add_field(name="ID", value=f"`{guild.id}`")
        emb.add_field(name="Members", value=guild.member_count)
        emb.add_field(name="Owner", value=f"`{guild.owner_id}`", inline=False)
        if guild.banner:
            emb.set_image(url=str(guild.banner))
        await self.guilds_webhook.send(embed=emb)


def setup(bot):
    bot.add_cog(Events(bot))
