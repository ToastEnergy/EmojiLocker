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
import time
import discord
from discord.ext import commands
from discord import app_commands


class Meta(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command()
    async def ping(self, interaction: discord.Interaction):
        """Check the API/Websocket latency"""
        start = time.perf_counter()
        message = await interaction.response.send_message("Pinging...")
        end = time.perf_counter()
        duration = (end - start) * 1000
        await interaction.edit_original_response(
            content=f':ping_pong: **Pong!** : {round(duration)}ms\n:ping_pong: **Latency** : {round(self.bot.latency * 1000)}ms')

    @app_commands.command()
    async def vote(self, interaction: discord.Interaction):
        """Upvote the bot"""
        await interaction.response.send_message("Do you like the bot? Upvote it at https://top.gg/bot/609087387695316992")

    @app_commands.command(name="invite")
    async def invite(self, interaction: discord.Interaction):
        """Get a quick invite for the bot"""
        url = discord.utils.oauth_url(self.bot.user.id, permissions=discord.Permissions(1074023424), scopes=['bot',
                                                                                                             'applications.commands'])
        view = discord.ui.View()
        button = discord.ui.Button(style=discord.ButtonStyle.url,label="Invite",url=url)
        view.add_item(button)
        await interaction.response.send_message(embed=discord.Embed(title='Thanks for using Emoji Locker!'), view=view)


async def setup(bot):
    await bot.add_cog(Meta(bot))
