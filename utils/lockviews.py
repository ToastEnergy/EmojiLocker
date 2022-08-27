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
from utils.views import OwnView
import asyncpg

class BaseView(OwnView):
    def __init__(self, ctx):
        super().__init__(ctx)
        self.successful = 0
        self.failed = 0
        self.overwrite_button = discord.ui.Button(label='Overwrite', style=discord.ButtonStyle.blurple)
        self.overwrite_button.callback = self.overwrite
        self.next_button = discord.ui.Button(emoji='▶️', style=discord.ButtonStyle.grey, row=0)
        self.next_button.callback = self.next_page
        self.previous_button = discord.ui.Button(emoji='◀️', style=discord.ButtonStyle.grey, row=0, disabled=True)
        self.previous_button.callback = self.previous_page
        self.remove_item(self.toggle_persistent)
        self.selects = []
        self.pages = []
        self._emojis = {}
        self._roles = {}
        self.selected_page = 0

    @discord.ui.button(label='Continue', style=discord.ButtonStyle.green)
    async def _continue(self, interaction: discord.Interaction, button):
        await interaction.response.defer()
        message = await interaction.original_message()
        await self.do_bulk(message, True)

    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button):
        await interaction.response.edit_message(content='Cancelled.', embed=None, view=None)
        self.stop()

    @discord.ui.button(label="Remove persistent", style=discord.ButtonStyle.red)
    async def toggle_persistent(self, interaction: discord.Interaction, button):
        if button.label == "Remove persistent":
            self.ctx._og_persistent = self.ctx.persistent
            self.ctx.persistent = set()
            button.label = "Add persistent"
            button.style = discord.ButtonStyle.green
        else:
            self.ctx.persistent = self.ctx._og_persistent
            button.label = "Remove persistent"
            button.style = discord.ButtonStyle.red
        await interaction.response.edit_message(view=self)


    async def do_bulk(self, message, overwrite=False):
        try:
            await message.edit(content='Working...', view=None, embed=None)
            i = 0
            for emoji in self.ctx.emojis:
                if not overwrite:
                    roles = set(emoji.roles).union(self.ctx.roles)
                else:
                    roles = self.ctx.roles
                try:
                    await emoji.edit(name=emoji.name, roles=roles)
                    self.successful += 1
                except:
                    self.failed += 1
                i += 1
                await message.edit(content=f'{i}/{len(self.ctx.emojis)}')
            await message.edit(content=None, embed=self.confirm_embed, view=UpvoteView())
        except Exception as e:
            raise e
        finally:
            self.stop()

    async def overwrite(self, interaction):
        if len(self.ctx.roles) == 0:
            return await interaction.response.send_message('Select at least one role', ephemeral=True)
        await interaction.response.defer()
        message = await interaction.original_message()
        await self.do_bulk(message, True)

    async def next_page(self, interaction: discord.Interaction):
        self.selected_page += 1
        self.update_paginator()
        await interaction.response.edit_message(view=self)

    async def previous_page(self, interaction: discord.Interaction):
        self.selected_page -= 1
        self.update_paginator()
        await interaction.response.edit_message(view=self)

    def update_buttons(self):
        self.previous_button.disabled = False
        self.next_button.disabled = False
        b1 = self.children.index(self.previous_button)
        b2 = self.children.index(self.next_button)
        if self.selected_page == 0:
            self.previous_button.disabled = True
        if self.selected_page == len(self.pages) - 1:
            self.next_button.disabled = True
        self.children[b1] = self.previous_button
        self.children[b2] = self.next_button

    def update_paginator(self):
        buttons = [i for i in self.children if type(i) == discord.ui.Button]
        self.clear_items()
        for b in buttons:
            self.add_item(b)
        self.update_buttons()
        for select in self.pages[self.selected_page]:
            self.add_item(select)

    def paginate_selects(self, kind, custom_list=None, handle_persistent=True):
        self.selects = []
        self.pages = []
        self.selected_page = 0
        if kind == "roles":
            roles = custom_list or self.ctx.guild.roles[1:]
            for i in range(0, len(roles), 25):
                s = RoleSelectMenu(self.ctx, roles[i:i + 25], handle_persistent)
                self.selects.append(s)
                self._roles[s] = set()
        elif kind == "emojis":
            emojis = custom_list or self.ctx.guild.emojis
            for i in range(0, len(emojis), 25):
                s = EmojiSelectMenu(self.ctx, emojis[i:i + 25])
                self.selects.append(s)
                self._emojis[s] = set()

        for select in self.selects[:4]:
            self.add_item(select)
        if len(self.selects) > 4:
            for x in range(0, len(self.selects), 4):
                self.pages.append([j for j in self.selects[x:x + 4]])
            self.add_item(self.previous_button)
            self.add_item(self.next_button)


class LockallView(BaseView):
    def __init__(self, ctx):
        super().__init__(ctx)
        self.children[0].label = 'Keep'
        self.clear_items()
        self.add_item(self._continue)
        self.add_item(self.overwrite_button)
        self.add_item(self.cancel)
        self.ctx.emojis = ctx.guild.emojis

    @property
    def confirm_embed(self):
        return discord.Embed(title='Emojis successfully locked', color=config.color,
                             description=f'''🔓 I have successfully locked all of your server emojis with {self.failed} failed edits.
        ℹ️ Now only the people with at least one of the roles that you specified ({','.join([r.mention for r in self.ctx.roles])}) will be able to use the emojis''').set_footer(
            text='If you can\'t use the emojis try to fully restart your Discord app')



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
        self.children[0].disabled = False
        self.children[2].disabled = False
        if self.page == 0:
            self.children[0].disabled = True
        if self.page == self.total_pages - 1:
            self.children[2].disabled = True

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
            x.disabled = True
        await interaction.response.edit_message(view=self)
        self.stop()

    @discord.ui.button(style=discord.ButtonStyle.blurple, emoji='▶️')
    async def _next(self, interaction: discord.Interaction, button):
        self.page += 1
        self.update()
        await interaction.response.edit_message(view=self, embed=self.embed)


class RoleSelectMenu(discord.ui.Select):
    def __init__(self, ctx, roles, handle_persistent=True):
        self.handle_persistent = handle_persistent
        self.ctx = ctx
        options = []
        for role in roles:
            options.append(discord.SelectOption(
                label=role.name, value=role.id))
        super().__init__(placeholder='Select the roles',
                         min_values=0, max_values=len(options), options=options)

    async def callback(self, interaction: discord.Interaction):
        selected = set(
            map(lambda r: self.ctx.guild.get_role(int(r)), self.values))
        self.view._roles[self] = selected
        self.ctx.roles.clear()
        for _set in self.view._roles.values():
            self.ctx.roles = self.ctx.roles.union(_set)
        if self.handle_persistent:
            self.ctx.roles = self.ctx.roles.union(self.ctx.persistent)


class EmojiSelectMenu(discord.ui.Select):
    def __init__(self, ctx, emojis):
        self.ctx = ctx
        self.emojis = set()
        options = []
        for emoji in emojis:
            options.append(discord.SelectOption(
                label=emoji.name, value=emoji.id, emoji=emoji))
        super().__init__(placeholder='Select the emojis',
                         min_values=0, max_values=len(options), options=options)

    async def callback(self, interaction: discord.Interaction):
        selected = set(
            map(lambda r: self.ctx.bot.get_emoji(int(r)), self.values))
        self.view._emojis[self] = selected
        self.ctx.emojis.clear()
        for _set in self.view._emojis.values():
            self.ctx.emojis = self.ctx.emojis.union(_set)


class LockAllSelectView(LockallView):
    def __init__(self, ctx):
        super().__init__(ctx)
        self._roles = {}
        self.paginate_selects("roles")


class MassUnlockSelectView(BaseView):
    def __init__(self, ctx):
        super().__init__(ctx)
        self._emojis = {}
        self.children[0].callback = self.__continue
        self.paginate_selects("emojis", ctx.locked)

    async def __continue(self, interaction: discord.Interaction):
        if len(self.ctx.emojis) == 0:
            return await interaction.response.send_message('Select at least one emoji', ephemeral=True)
        await interaction.response.defer()
        message = await interaction.original_message()
        await self.do_bulk(message, True)

    @property
    def confirm_embed(self):
        return discord.Embed(title='Emojis successfully unlocked', color=config.color,
                             description=f'''🔓 I have successfully unlocked {self.successful} emojis with {self.failed} failed edits.\n
ℹ️ Now everyone will be able to use these emojis in your server''').set_footer(
            text='If you can\'t use the emojis try to fully restart your Discord app')


class MultipleSelectView(BaseView):
    def __init__(self, ctx):
        super().__init__(ctx)
        self.step = 0
        self.children[0].callback = self.__continue
        self.add_item(self.toggle_persistent)
        self.paginate_selects("emojis")

    async def __continue(self, interaction: discord.Interaction):
        if self.step == 0:
            if len(self.ctx.emojis) == 0:
                return await interaction.response.send_message('Select at least one emoji', ephemeral=True)
            self.clear_items()
            self._continue.label = 'Keep'
            self.add_item(self._continue)
            self.add_item(self.overwrite_button)
            self.add_item(self.cancel)
            self.paginate_selects("roles")
            self.ctx.embed.description = '''
Select the roles that will be able to use the selected emojis with the menu below, then click Keep or Overwrite

If you select **keep** an emoji already locked to @role1 will be locked to @role1 + the roles that you specified in the command

if you select **overwrite** it will be locked only to the roles that you just specified.
'''
            await interaction.response.edit_message(view=self, embed=self.ctx.embed)
        elif self.step == 1:
            if len(self.ctx.roles) == 0:
                return await interaction.response.send_message('Select at least one role', ephemeral=True)
            await interaction.response.defer()
            message = await interaction.original_message()
            await self.do_bulk(message)
        self.step += 1

    @property
    def confirm_embed(self):
        return discord.Embed(title='Emojis successfully locked', color=config.color,
                             description=f'''🔓 I have successfully locked {self.successful} emojis with {self.failed} failed edits.\n
ℹ️ Now only the people with at least one of the roles that you specified ({','.join([r.mention for r in self.ctx.roles])}) will be able to use the emojis''').set_footer(
            text='If you can\'t use the emojis try to fully restart your Discord app')

class RolesView(BaseView):
    def __init__(self, ctx):
        super().__init__(ctx)
        self.remove_item(self._continue)

    @discord.ui.button(label='Add', style=discord.ButtonStyle.green,row=0)
    async def add(self, interaction: discord.Interaction, button):
        self.ctx.embed.description = 'You are adding some persistent roles, select them with the menu below then click continue'
        self.ctx.roles = set()
        self.remove_item(button)
        self.remove_item(self.remove)
        if not self.ctx.data:
            alr_added = set()
        else:
            alr_added = set(self.ctx.data)
        self.paginate_selects("roles", list(set(self.ctx.guild.roles[1:]) - alr_added), False)
        cont = discord.ui.Button(
            style=discord.ButtonStyle.green, label='Continue', row=0)
        cont.callback = self.add_roles
        self.add_item(cont)
        await interaction.response.edit_message(view=self, embed=self.ctx.embed)

    async def add_roles(self, interaction: discord.Interaction):
        await interaction.response.defer()
        roles = map(lambda r: r.id, self.ctx.roles)
        try:
            await self.ctx.bot.db.add_roles(self.ctx.guild.id, roles)
        except asyncpg.exceptions.UniqueViolationError:
            await interaction.followup.send('One of the roles was already added.', ephemeral=True)

        self.clear_items()
        self.add_item(self.add)
        self.add_item(self.remove)
        self.add_item(self.cancel)
        self.ctx.data = await self.ctx.bot.get_persistent_roles(self.ctx)
        if not self.ctx.data:
            self.ctx.embed.description = 'There are no persistent roles for this server'
        else:
            self.ctx.embed.description = f'The persistent roles for this server are {", ".join(map(lambda r: r.mention, self.ctx.data))}'
        await interaction.followup.edit_message(message_id=interaction.message.id, view=self, embed=self.ctx.embed)

    async def remove_roles(self, interaction: discord.Interaction):
        await interaction.response.defer()
        roles = list(map(lambda r: r.id, self.ctx.roles))
        await self.ctx.bot.db.delete_roles(roles)
        self.clear_items()
        self.add_item(self.add)
        self.add_item(self.remove)
        self.add_item(self.cancel)
        self.ctx.data = await self.ctx.bot.get_persistent_roles(self.ctx)
        if not self.ctx.data:
            self.ctx.embed.description = 'There are no persistent roles for this server'
        else:
            self.ctx.embed.description = f'The persistent roles for this server are {", ".join(map(lambda r: r.mention, self.ctx.data))}'
        await interaction.followup.edit_message(message_id=interaction.message.id, view=self, embed=self.ctx.embed)

    @discord.ui.button(label='Remove', style=discord.ButtonStyle.blurple,row=0)
    async def remove(self, interaction: discord.Interaction, button):
        self.ctx.embed.description = 'You are removing some persistent roles, select them with the menu below then click continue'
        self.ctx.roles = set()
        self.remove_item(button)
        self.remove_item(self.add)
        if not self.ctx.data:
            return await interaction.response.send_message('No roles to remove!', ephemeral=True)
        cont = discord.ui.Button(
            style=discord.ButtonStyle.green, label='Continue', row=0)
        cont.callback = self.remove_roles
        self.add_item(cont)
        self.paginate_selects("roles", self.ctx.data, False)
        await interaction.response.edit_message(view=self, embed=self.ctx.embed)

