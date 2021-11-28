import time

import discord.utils
from discord.ext import commands


class Meta(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=('info', 'aboutme', 'bot', 'stats', 'botstats'))
    async def about(self, ctx):
        """Info about the bot itself."""
        await ctx.send_help()

    @commands.command()
    async def ping(self, ctx):
        """Check the API/Websocket latency"""
        start = time.perf_counter()
        message = await ctx.send("Pinging...")
        end = time.perf_counter()
        duration = (end - start) * 1000
        await message.edit(
            content=f':ping_pong: **Pong!** : {round(duration)}ms\n:ping_pong: **Latency** : {round(self.bot.latency * 1000)}ms')

    @commands.command()
    async def invite(self, ctx):
        """Get a quick invite for the bot"""
        url = discord.utils.oauth_url(self.bot.user.id, permissions=discord.Permissions(1074023424), scopes=['bot',
                                                                                                             'applications.commands'])
        view = discord.ui.View()
        button = discord.ui.Button(style=discord.ButtonStyle.url,label="Invite",url=url)
        view.add_item(button)
        await ctx.send(embed=discord.Embed(title='Thanks for using Emoji Locker!'), view=view)


def setup(bot):
    bot.add_cog(Meta(bot))
