import discord
import traceback
from discord.embeds import E
from discord.ext import commands
from discord.ext.commands.errors import BadArgument, RoleNotFound
import config
from datetime import datetime


class SupportView(discord.ui.View):
    def __init__(self, ctx):
        super().__init__(timeout=240)
        self.ctx: commands.Context = ctx
        button = discord.ui.Button(
            style=discord.ButtonStyle.url, url=config.support_server, label='Support server')
        self.add_item(button)

    @discord.ui.button(style=discord.ButtonStyle.blurple, label='Show command help')
    async def show_help(self, button, interaction):
        self.remove_item(button)
        embed = self.ctx.sent_message.embeds[0]
        embed.add_field(name='Command help', value=self.ctx.command.signature)
        await interaction.response.edit_message(view=self, embed=embed)

    async def interaction_check(self, interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message('This is being used by someone else!', ephemeral=True)
            return False
        return True


# True means that we like the libs error message
errors = {
    commands.CheckFailure: True,
    commands.UserInputError: True,
    commands.EmojiNotFound : 'Emoji "{argument}" not found, is this a default emoji?',
    commands.RoleNotFound : True,
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
        print(type(error))
        print(type(error).__bases__)
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
        
        print(error.__dict__)
        description = description.format(**error.__dict__)
        embed = discord.Embed(title="Something went wrong.", colour=discord.Colour.red(
        ), description=description)
        embed.set_author(name=str(ctx.author),
                         icon_url=str(ctx.author.avatar))
        ctx.sent_message = await ctx.send(embed=embed, view=SupportView(ctx))

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
            await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(ErrorHandler(bot))
