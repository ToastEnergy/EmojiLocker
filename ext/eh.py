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


class ErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.webhook = discord.Webhook.from_url(
            config.error_webhook, session=bot.session)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return
        traceback_ = traceback.format_exception(
            type(error), error, error.__traceback__)
        invoke = ctx.message.content
        if len(invoke) > 800:
            invoke = invoke[:800]+"..."
        emb = discord.Embed(colour=discord.Colour.red())
        emb.add_field(name="Message",
                      value=f"`{invoke}` (`{ctx.message.id}`)", inline=False)
        emb.add_field(
            name="Author", value=f"`{str(ctx.author)}` (`{ctx.author.id}`)", inline=False)
        if ctx.guild:
            emb.add_field(
                name="Channel", value=f"`#{ctx.channel.name}` (`{ctx.channel.id}`)", inline=False)
            emb.add_field(
                name="Guild", value=f"`{ctx.guild.name}` (`{ctx.guild.id}`)", inline=False)
            emb.set_thumbnail(url=str(ctx.guild.icon))
        else:
            emb.add_field(name="Channel", value=f"`DM Channel`", inline=False)
        time = round(datetime.timestamp(datetime.now()))
        emb.add_field(name="When", value=f"<t:{time}:f>", inline=False)
        emb.add_field(name="Error", value=f"```py\n{str(error)}\n```")
        emb.set_author(name=str(ctx.author), icon_url=str(ctx.author.avatar))
        await self.webhook.send(f'Traceback ID : {self.bot.tid}', embed=emb)
        UNKNOWN_ERROR = f'An unhandled error occured, please report this to the developers. Error code : `{self.bot.tid}`'
        self.bot.tracebacks[self.bot.tid] = traceback_
        self.bot.tid += 1
        base_error = errors.get(type(error))
        if base_error == True:
            description = str(error)
        elif base_error == None:
            parent_err = errors.get(type(error).__bases__[0])
            if parent_err == True:
                description = str(error)
            elif parent_err == None:
                description = UNKNOWN_ERROR
            else:
                description = parent_err
        else:
            description = base_error
        description = description.format(**error.__dict__)
        ctx.embed = discord.Embed(title="Something went wrong.", colour=discord.Colour.red(
        ), description=description)
        ctx.embed.set_author(name=str(ctx.author),
                             icon_url=str(ctx.author.avatar))
        if not ctx.channel.permissions_for(ctx.me).embed_links:
            ctx.sent_message = await ctx.reply_embed(description, view=views.SupportView(ctx))
        else:
            ctx.sent_message = await ctx.reply_embed(embed=ctx.embed, view=views.SupportView(ctx))

    @commands.command(hidden=True)
    @commands.is_owner()
    async def vt(self, ctx, tid: int):
        paginator = commands.Paginator(suffix="```", prefix="```")
        tracebacks = self.bot.tracebacks[tid]
        for x in tracebacks:
            paginator.add_line(x)
        for x in paginator.pages:
            embed = discord.Embed(
                title="Traceback inspector", colour=discord.Color.red(), description=x)
            await ctx.reply_embed(embed=embed)


def setup(bot):
    bot.add_cog(ErrorHandler(bot))
