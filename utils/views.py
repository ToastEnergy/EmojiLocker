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
import asyncpg
import config
import discord
from discord.ext import commands


class UpvoteView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=0)
        button = discord.ui.Button(
            style=discord.ButtonStyle.url, url="https://top.gg/bot/609087387695316992/vote", label='Upvote the bot')
        self.add_item(button)
        self.stop()


class OwnView(discord.ui.View):
    def __init__(self, author_id: int):
        self.author_id = author_id
        self.latest_interaction : discord.Interaction
        super().__init__(timeout=240)

    async def interaction_check(self, interaction):
        self.latest_interaction = interaction
        if interaction.user.id != self.author_id:
            await interaction.response.send_message('This is being used by someone else!', ephemeral=True)
            return False
        return True
     
    async def on_timeout(self):
        for x in self.children:
            x.disabled = True # type: ignore
        try:
            await self.latest_interaction.edit_original_response(view=self)
        except:
            pass

class ConfirmView(OwnView):
    def __init__(self, author_id: int):
        super().__init__(author_id)
        self.result = None
    
    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button):
        await interaction.response.defer()
        self.result = True
        self.stop()
    
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button):
        await interaction.response.defer()
        self.result = False
        self.stop()

class SupportView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        button = discord.ui.Button(
            style=discord.ButtonStyle.url, url=config.support_server, label='Support server')
        self.add_item(button)

class PacksView(OwnView):
    def __init__(self, author_id:int, paginator: commands.Paginator, embed: discord.Embed):
        super().__init__(author_id)
        self.paginator = paginator
        self.embed = embed
        self.page = 0
        self.total_pages = len(paginator.pages)
        self.timeout = 60
        self.update()

    @property
    def visualized_page(self):
        return self.page + 1

    def update(self):
        self.children[0].disabled = False # type: ignore
        self.children[2].disabled = False # type: ignore
        if self.page == 0:
            self.children[0].disabled = True # type: ignore
        if self.page == self.total_pages - 1:
            self.children[2].disabled = True # type: ignore

        page = self.paginator.pages[self.page]
        self.embed.description = page
        self.embed.set_footer(
            text=f'Page {self.visualized_page}/{self.total_pages}')

    @discord.ui.button(style=discord.ButtonStyle.blurple, emoji='◀️')
    async def back(self, interaction: discord.Interaction, button):
        self.page -= 1
        self.update()
        await interaction.response.edit_message(view=self, embed=self.embed)

    @discord.ui.button(style=discord.ButtonStyle.grey, emoji='⏹️')
    async def _stop(self, interaction: discord.Interaction, button):
        for x in self.children:
            x.disabled = True # type: ignore
        await interaction.response.edit_message(view=self)
        self.stop()

    @discord.ui.button(style=discord.ButtonStyle.blurple, emoji='▶️')
    async def _next(self, interaction: discord.Interaction, button):
        self.page += 1
        self.update()
        await interaction.response.edit_message(view=self, embed=self.embed)