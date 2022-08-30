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
import discord
from discord.ext import commands
from utils.views import OwnView, UpvoteView
import asyncpg
import config


# class EmojiSelectMenu(discord.ui.Select):
#     def __init__(self, bot: commands.Bot, emojis):
#         self.bot = bot
#         self.emojis = emojis
#         options = []
#         for emoji in emojis:
#             options.append(discord.SelectOption(
#                 label=emoji.name, value=emoji.id, emoji=emoji))
#         super().__init__(placeholder='Select the emojis',
#                          min_values=0, max_values=len(options), options=options)

#     async def callback(self, interaction: discord.Interaction):
#         selected = set(
#             map(lambda r: self.bot.get_emoji(int(r)), self.values))
#         self.view.emojis[self] = selected
#         self.ctx.emojis.clear()
#         for _set in self.view._emojis.values():
#             self.ctx.emojis = self.ctx.emojis.union(_set)

# class LockView(OwnView):
#     def __init__(self, author_id: int, roles: list[discord.Role], emojis: list[discord.Emoji], guild: discord.Guild, confirm_embed: discord.Embed):
#         super().__init__(author_id)
#         self.roles = roles
#         self.emojis = emojis
#         self.guild = guild
#         self.confirm_embed = confirm_embed
    
#     async def do_lock(self, interaction: discord.Interaction, overwrite=False):
#         succesful = 0
#         failed = 0
#         try:
#             await interaction.edit_original_response(content='Working...', view=None, embed=None)
#             i = 0
#             for emoji in self.emojis:
#                 if not overwrite:
#                     roles = set(emoji.roles).union(self.roles)
#                 else:
#                     roles = self.roles
#                 try:
#                     await emoji.edit(name=emoji.name, roles=roles)
#                     succesful += 1
#                 except:
#                     failed += 1
#                 i += 1
#                 await interaction.edit_original_response(content=f'{i}/{len(self.emojis)}')
#             await interaction.edit_original_response(content=None, embed=self.confirm_embed, view=UpvoteView())
#         except Exception as e:
#             raise e
#         finally:
#             self.stop()


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



# class RolesView(BaseView):
#     def __init__(self, ctx):
#         super().__init__(ctx)
#         self.remove_item(self._continue)

#     @discord.ui.button(label='Add', style=discord.ButtonStyle.green,row=0)
#     async def add(self, interaction: discord.Interaction, button):
#         self.ctx.embed.description = 'You are adding some persistent roles, select them with the menu below then click continue'
#         self.ctx.roles = set()
#         self.remove_item(button)
#         self.remove_item(self.remove)
#         if not self.ctx.data:
#             alr_added = set()
#         else:
#             alr_added = set(self.ctx.data)
#         self.paginate_selects("roles", list(set(self.ctx.guild.roles[1:]) - alr_added), False)
#         cont = discord.ui.Button(
#             style=discord.ButtonStyle.green, label='Continue', row=0)
#         cont.callback = self.add_roles
#         self.add_item(cont)
#         await interaction.response.edit_message(view=self, embed=self.ctx.embed)

#     async def add_roles(self, interaction: discord.Interaction):
#         await interaction.response.defer()
#         roles = map(lambda r: r.id, self.ctx.roles)
#         try:
#             await self.ctx.bot.db.add_roles(self.ctx.guild.id, roles)
#         except asyncpg.exceptions.UniqueViolationError:
#             await interaction.followup.send('One of the roles was already added.', ephemeral=True)

#         self.clear_items()
#         self.add_item(self.add)
#         self.add_item(self.remove)
#         self.add_item(self.cancel)
#         self.ctx.data = await self.ctx.bot.get_persistent_roles(self.ctx)
#         if not self.ctx.data:
#             self.ctx.embed.description = 'There are no persistent roles for this server'
#         else:
#             self.ctx.embed.description = f'The persistent roles for this server are {", ".join(map(lambda r: r.mention, self.ctx.data))}'
#         await interaction.followup.edit_message(message_id=interaction.message.id, view=self, embed=self.ctx.embed)

#     async def remove_roles(self, interaction: discord.Interaction):
#         await interaction.response.defer()
#         roles = list(map(lambda r: r.id, self.ctx.roles))
#         await self.ctx.bot.db.delete_roles(roles)
#         self.clear_items()
#         self.add_item(self.add)
#         self.add_item(self.remove)
#         self.add_item(self.cancel)
#         self.ctx.data = await self.ctx.bot.get_persistent_roles(self.ctx)
#         if not self.ctx.data:
#             self.ctx.embed.description = 'There are no persistent roles for this server'
#         else:
#             self.ctx.embed.description = f'The persistent roles for this server are {", ".join(map(lambda r: r.mention, self.ctx.data))}'
#         await interaction.followup.edit_message(message_id=interaction.message.id, view=self, embed=self.ctx.embed)

#     @discord.ui.button(label='Remove', style=discord.ButtonStyle.blurple,row=0)
#     async def remove(self, interaction: discord.Interaction, button):
#         self.ctx.embed.description = 'You are removing some persistent roles, select them with the menu below then click continue'
#         self.ctx.roles = set()
#         self.remove_item(button)
#         self.remove_item(self.add)
#         if not self.ctx.data:
#             return await interaction.response.send_message('No roles to remove!', ephemeral=True)
#         cont = discord.ui.Button(
#             style=discord.ButtonStyle.green, label='Continue', row=0)
#         cont.callback = self.remove_roles
#         self.add_item(cont)
#         self.paginate_selects("roles", self.ctx.data, False)
#         await interaction.response.edit_message(view=self, embed=self.ctx.embed)

