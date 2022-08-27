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
import traceback
from datetime import datetime
from typing import Union

import config
import discord
from discord import app_commands
from discord.ext import commands
from utils import views
from utils.checks import owner_only

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
        bot.tree.on_error = self.on_command_error
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

    async def on_command_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        if isinstance(error, commands.CommandNotFound):
            return
        if not interaction.command:
            return
        if not interaction.guild:
            return
        traceback_ = traceback.format_exception(
            type(error), error, error.__traceback__)
        invoke = f"/{interaction.command.name} {interaction.namespace}"
        if len(invoke) > 800:
            invoke = invoke[:800] + '...'
        emb = discord.Embed()
        emb.add_field(name='Message',
                      value=f'`{invoke}` (`{interaction.id}`)', inline=False)
        emb.add_field(
            name='Author', value=f'`{str(interaction.user)}` (`{interaction.user.id}`)', inline=False)
        emb.add_field(
            name='Channel', value=f'`#{interaction.channel.name}` (`{interaction.channel.id}`)', inline=False) # type: ignore
        emb.add_field(
            name='Guild', value=f'`{interaction.guild.name}` (`{interaction.guild.id}`)', inline=False)
        if interaction.guild.icon:
            emb.set_thumbnail(url=str(interaction.guild.icon))
        time = round(datetime.timestamp(datetime.now()))
        emb.add_field(name='When', value=f'<t:{time}:f>', inline=False)
        emb.add_field(name='Error', value=f'```py\n{str(error)}\n```')
        emb.set_author(name=str(interaction.user),
                       icon_url=str(interaction.user.display_avatar))
        color = discord.Color.red()
        UNKNOWN_ERROR = f'An unhandled error occurred, please report this to the developers. Error code : `{self.bot.tid}`'
        self.bot.tracebacks[self.bot.tid] = traceback_
        self.bot.tid += 1
        if isinstance(error, app_commands.TransformerError):
            error = error.__cause__ # type: ignore
        elif isinstance(error, app_commands.AppCommandError):
            error = error.original # type: ignore
        base_error = errors.get(type(error)) # type: ignore
        if base_error is True:
            description = str(error)
        elif base_error is None:
            parent_err = errors.get(type(error).__bases__[0]) # type: ignore
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
        embed = discord.Embed(
            title="Something went wrong.", color=color, description=description)
        embed.set_author(name=str(interaction.user),
                             icon_url=str(interaction.user.display_avatar))
        emb.color = color
        await self.webhook.send(f'Traceback ID : {self.bot.tid}', embed=emb)
        try:
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed, view=views.SupportView())
            else:
                await interaction.response.send_message(embed=embed, view=views.SupportView())
        except discord.errors.Forbidden:
            pass

    @app_commands.command()
    @app_commands.guilds(discord.Object(id=config.support_server_id))
    @app_commands.check(owner_only)
    async def vt(self, interaction: discord.Interaction, tid: int):
        paginator = commands.Paginator(suffix='```', prefix='```')
        tracebacks = self.bot.tracebacks[tid]
        for x in tracebacks:
            paginator.add_line(x)
        for x in paginator.pages:
            embed = discord.Embed(
                title='Traceback inspector', color=discord.Color.red(), description=x)
            await interaction.response.send_message(embed=embed)

    @commands.Cog.listener()
    async def on_app_command_completion(self, interaction: discord.Interaction, command: Union[discord.app_commands.Command, discord.app_commands.ContextMenu]):
        message = await interaction.original_response()
        if not interaction.guild:
            return
        emb = discord.Embed(description=f"**`/{command.name}`**\n\n**message id**: `{message.id}`\n**{str(interaction.user)}** (`{interaction.user.id}`)\n**#{interaction.channel.name}** (`{interaction.channel.id}`)\n**{interaction.guild.name}** (`{interaction.guild.id}`)\n\n<t:{int(datetime.now().timestamp())}:f>", color=config.color) # type: ignore
        emb.set_author(name=str(interaction.user), icon_url=interaction.user.avatar)
        emb.set_thumbnail(url=interaction.guild.icon) 
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


async def setup(bot):
    await bot.add_cog(Events(bot))
