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
import itertools

import config
import discord
from discord.ext import commands
from discord import app_commands
from utils.autocompletes import emoji_autocomplete
from utils.views import PacksView
from utils.checks import guild_with_emoji_only
from utils.transformers import EmojiTransformer

class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="emojiinfo")
    @app_commands.guild_only()
    @app_commands.describe(emoji="The emoji to get info on")
    @app_commands.autocomplete(emoji=emoji_autocomplete)
    @app_commands.check(guild_with_emoji_only)
    @commands.guild_only()
    async def emojiinfo(self, interaction:discord.Interaction, emoji: app_commands.Transform[discord.Emoji, EmojiTransformer]):
        """Get info about an emoji"""
        embed = discord.Embed(title=emoji.name)
        embed.color = config.color
        embed.set_thumbnail(url=str(emoji.url))
        embed.description = f'''
**Animated?** : {emoji.animated}
**Roles** : {", ".join([x.mention for x in emoji.roles]) or '@everyone'}
**Guild** : {emoji.guild.name} [{emoji.guild.id}]
**ID** : {emoji.id}
**Available** : {emoji.available}
**Managed by an integration?** : {emoji.managed}
**Created at** : {emoji.created_at.strftime("%m/%d/%Y, %H:%M:%S")}
**Download link** : [Click here]({str(emoji.url)})
        '''
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="emojis")
    @app_commands.guild_only()
    @app_commands.check(guild_with_emoji_only)
    async def emojis(self, interaction: discord.Interaction):
        """List all the server emojis grouped by roles"""
        packs = []
        keys = []
        def func(x): return x.roles
        for k, g in itertools.groupby(sorted(interaction.guild.emojis, key=func), func): # type: ignore
            packs.append(list(g))
            keys.append(k)

        embed = discord.Embed(
            title='Packs', color=config.color)
        paginator = commands.Paginator(prefix='', suffix='', linesep='')
        c = 0
        for x in packs:
            paginator.add_line('\n\n')
            paginator.add_line(
                f"> **{(', '.join([role.name for role in keys[c]])) or '@everyone'}**")
            c += 1
            paginator.add_line('\n')
            for em in x:
                paginator.add_line(f"{em} ")
        embed.description = paginator.pages[0]
        embed.set_footer(text=f'Page 1/{len(paginator.pages)}')
        if len(paginator.pages) > 1:
            view = PacksView(author_id=interaction.user.id, paginator=paginator, embed=embed)
            await interaction.response.send_message(embed=embed, view=view)
            return await view.wait()
        else:
            await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Misc(bot))
