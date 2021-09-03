import asyncpg
import config
import discord
from discord.ext import commands


class OwnView(discord.ui.View):
    def __init__(self, ctx):
        self.ctx = ctx
        super().__init__(timeout=240)

    async def interaction_check(self, interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message('This is being used by someone else!', ephemeral=True)
            return False
        return True


class BaseView(OwnView):
    def __init__(self, ctx):
        self.ctx = ctx
        super().__init__(ctx)

    @discord.ui.button(label='Continue', style=discord.ButtonStyle.green)
    async def _continue(self, button, interaction):
        await interaction.response.defer()
        message = await interaction.original_message()
        await self.do_bulk(message)

    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.red)
    async def cancel(self, button, interaction):
        await interaction.response.edit_message(content='Cancelled.', embed=None, view=None)
        self.stop()

    async def do_bulk(self, message):
        try:
            await message.edit(content='Working...', view=None, embed=None)
            i = 0
            for emoji in self.ctx.emojis:
                try:
                    await emoji.edit(name=emoji.name, roles=self.ctx.roles)
                except:
                    pass
                i += 1
                await message.edit(content=f'{i}/{len(self.ctx.emojis)}')
            await message.edit(content=None, embed=self.confirm_embed)
        except Exception as e:
            raise
        finally:
            self.stop()


class LockallView(OwnView):
    def __init__(self, ctx):
        self.ctx = ctx
        super().__init__(ctx)

    @discord.ui.button(label='Keep', style=discord.ButtonStyle.green)
    async def keep(self, button, interaction):
        if len(self.ctx.roles) == 0:
            return await interaction.response.send_message('Select at least one role',ephemeral=True)
        await interaction.response.defer()
        message = await interaction.original_message()
        await self.do_lockall(False, message)

    @discord.ui.button(label='Overwrite', style=discord.ButtonStyle.blurple)
    async def overwrite(self, button, interaction):
        if len(self.ctx.roles) == 0:
            return await interaction.response.send_message('Select at least one role',ephemeral=True)
        await interaction.response.defer()
        message = await interaction.original_message()
        await self.do_lockall(True, message)

    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.red)
    async def cancel(self, button, interaction):
        await interaction.response.edit_message(content='Cancelled.', embed=None, view=None)
        self.stop()

    async def do_lockall(self, overwrwite, message):
        try:
            await message.edit(content='Working...', view=None, embed=None)
            i = 0
            for emoji in self.ctx.guild.emojis:
                if not overwrwite:
                    roles = set(emoji.roles).union(self.ctx.roles)
                else:
                    roles = self.ctx.roles
                try:
                    await emoji.edit(name=emoji.name, roles=roles)
                except:
                    pass
                i += 1
                await message.edit(content=f'{i}/{len(self.ctx.guild.emojis)}')
            embed = discord.Embed(title='Emojis succesfully locked', color=discord.Color.green(),
                                  description=f'''🔒 I have succesfully locked all of your server emojis.\n
    ℹ️ Now only the people with at least one of the roles that you specified ({','.join([r.mention for r in self.ctx.roles])}) will be able to use the emojis''')
            embed.set_footer(
                text='If you can\'t use the emojis but you have at least one of these roles try to fully restart your Discord app')
            await message.edit(content=None, embed=embed)
        except Exception as e:
            raise(e)
        finally:
            self.stop()


class SupportView(OwnView):
    def __init__(self, ctx):
        super().__init__(ctx)
        self.ctx: commands.Context = ctx
        button = discord.ui.Button(
            style=discord.ButtonStyle.url, url=config.support_server, label='Support server')
        self.add_item(button)

    @discord.ui.button(style=discord.ButtonStyle.blurple, label='Show command help')
    async def show_help(self, button, interaction):
        self.remove_item(button)
        embed = self.ctx.embed
        embed.add_field(name='Command help', value=self.ctx.command.signature)
        await interaction.response.edit_message(view=self, embed=embed, content=None)


class PacksView(OwnView):
    def __init__(self, ctx):
        super().__init__(ctx)
        self.ctx: commands.Context = ctx
        self.page = 0
        self.total_pages = len(ctx.paginator.pages)
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

        page = self.ctx.paginator.pages[self.page]
        self.ctx.embed.description = page
        self.ctx.embed.set_footer(
            text=f'Page {self.visualized_page}/{self.total_pages}')

    async def on_timeout(self):
        for x in self.children:
            x.disabled = True
        await self.ctx.sent_message.edit(view=self)

    @discord.ui.button(style=discord.ButtonStyle.blurple, emoji="◀️")
    async def back(self, button, interaction):
        self.page -= 1
        self.update()
        await interaction.response.edit_message(view=self, embed=self.ctx.embed)

    @discord.ui.button(style=discord.ButtonStyle.grey, emoji="⏹️")
    async def _stop(self, button, interaction):
        for x in self.children:
            x.disabled = True
        await interaction.response.edit_message(view=self)
        self.stop()

    @discord.ui.button(style=discord.ButtonStyle.blurple, emoji="▶️")
    async def next(self, button, interaction):
        self.page += 1
        self.update()
        await interaction.response.edit_message(view=self, embed=self.ctx.embed)


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
        self._roles = {}
        super().__init__(ctx)
        for i in range(0, len(ctx.guild.roles[1:]), 25):
            s = RoleSelectMenu(ctx, ctx.guild.roles[1:][i:i + 25])
            self.add_item(s)
            self._roles[s] = set()



class MassUnlockSelectView(BaseView):
    def __init__(self, ctx):
        self._emojis = {}
        super().__init__(ctx)
        self.children[0].callback = self.__continue
        for i in range(0, len(ctx.locked), 25):
            s = EmojiSelectMenu(ctx, ctx.locked[i:i + 25])
            self.add_item(s)
            self._emojis[s] = set()

    async def __continue(self, interaction : discord.Interaction):
        if len(self.ctx.emojis) == 0:
            return await interaction.response.send_message('Select at least one emoji',ephemeral=True)
        await interaction.response.defer()
        message = await interaction.original_message()
        await self.do_bulk(message)  

    @property
    def confirm_embed(self):
        return discord.Embed(title='Emojis succesfully unlocked', color=discord.Color.green(),
                                          description=f'''🔓 I have succesfully unlocked {len(self.ctx.emojis)} emojis.\n
ℹ️ Now everyone will be able to use all emojis in your server''').set_footer(
            text='If you can\'t use the emojis try to fully restart your Discord app')

class MultipleSelectView(BaseView):
    def __init__(self, ctx):
        self.step = 0
        self._emojis = {}
        self._roles = {}
        super().__init__(ctx)
        self.children[0].callback = self.__continue
        for i in range(0, len(ctx.guild.emojis), 25):
            s = EmojiSelectMenu(ctx, ctx.guild.emojis[i:i + 25])
            self.add_item(s)
            self._emojis[s] = set()




    async def __continue(self, interaction : discord.Interaction):
        if self.step == 0:
            if len(self.ctx.emojis) == 0:
                return await interaction.response.send_message('Select at least one emoji',ephemeral=True)
            self.clear_items()
            self.add_item(self._continue)
            self.add_item(self.cancel)
            for i in range(0, len(self.ctx.guild.roles[1:]), 25):
                s = RoleSelectMenu(self.ctx, self.ctx.guild.roles[1:][i:i + 25])
                self.add_item(s)
                self._roles[s] = set()
            self.ctx.embed.description = "Select the roles which will be able to use the selected emojis with the menu below, then click continue"
            await interaction.response.edit_message(view=self,embed=self.ctx.embed)
        elif self.step == 1:
            if len(self.ctx.roles) == 0:
                return await interaction.response.send_message('Select at least one role',ephemeral=True)
            await interaction.response.defer()
            message = await interaction.original_message()
            await self.do_bulk(message)
        self.step += 1
    @property
    def confirm_embed(self):
        return discord.Embed(title='Emojis succesfully locked', color=discord.Color.green(),
                                          description=f'''🔓 I have succesfully locked {len(self.ctx.emojis)} emojis.\n
ℹ️ Now only the people with at least one of the roles that you specified ({','.join([r.mention for r in self.ctx.roles])}) will be able to use the emojis''').set_footer(
            text='If you can\'t use the emojis try to fully restart your Discord app')



class RolesView(OwnView):
    def __init__(self, ctx):
        self._roles = {}
        super().__init__(ctx)

    def add_selects(self, roles):
        for i in range(0, len(roles), 25):
            s = RoleSelectMenu(self.ctx, roles[i:i + 25],False)
            self.add_item(s)
            self._roles[s] = set()

    @discord.ui.button(label='Add', style=discord.ButtonStyle.green)
    async def add(self, button, interaction):
        self.ctx.embed.description = 'You are adding some persistent roles, select them with the menu below then click continue'
        self.ctx.roles = set()
        self.remove_item(button)
        self.remove_item(self.remove)
        if not self.ctx.data:
            alr_added = set()
        else:
            alr_added = set(map(lambda r : self.ctx.guild.get_role(r), self.ctx.data.get('roles')))
        self.add_selects(list(set(self.ctx.guild.roles[1:])-alr_added))
        cont = discord.ui.Button(style=discord.ButtonStyle.green, label='Continue')
        cont.callback = self.add_roles
        self.add_item(cont)
        await interaction.response.edit_message(view=self,embed=self.ctx.embed)


    async def add_roles(self, interaction : discord.Interaction):
        await interaction.response.defer()
        roles = map(lambda r: r.id, self.ctx.roles)
        try:
            await self.ctx.bot.db.add_roles(self.ctx.guild.id,roles)
        except asyncpg.exceptions.UniqueViolationError:
            await interaction.followup.send('One of the roles was already added.',ephemeral=True)

        self.clear_items()
        self.add_item(self.add)
        self.add_item(self.remove)
        self.add_item(self.cancel)
        self.ctx.data = await self.ctx.bot.db.get_guild(self.ctx.guild.id)
        if len(self.ctx.data.get('roles')) == 0:
            self.ctx.embed.description = "There are no persistent roles for this server"
        else:
            self.ctx.embed.description = f"The persistent roles for this server are {', '.join(map(lambda r : f'<@&{r}>' ,self.ctx.data.get('roles')))}"
        await interaction.followup.edit_message(message_id=interaction.message.id, view=self, embed=self.ctx.embed)

    async def remove_roles(self, interaction : discord.Interaction):
        await interaction.response.defer()
        roles = list(map(lambda r: r.id, self.ctx.roles))
        await self.ctx.bot.db.delete_roles(roles)
        self.clear_items()
        self.add_item(self.add)
        self.add_item(self.remove)
        self.add_item(self.cancel)
        self.ctx.data = await self.ctx.bot.db.get_guild(self.ctx.guild.id)
        if len(self.ctx.data.get('roles')) == 0:
            self.ctx.embed.description = "There are no persistent roles for this server"
        else:
            self.ctx.embed.description = f"The persistent roles for this server are {', '.join(map(lambda r : f'<@&{r}>' ,self.ctx.data.get('roles')))}"
        await interaction.followup.edit_message(message_id=interaction.message.id, view=self, embed=self.ctx.embed)


    @discord.ui.button(label='Remove', style=discord.ButtonStyle.blurple)
    async def remove(self, button, interaction):
        self.ctx.embed.description = 'You are removing some persistent roles, select them with the menu below then click continue'
        self.ctx.roles = set()
        self.remove_item(button)
        self.remove_item(self.add)
        if not self.ctx.data or len(self.ctx.data.get('roles'))==0:
            return await interaction.response.send_message('No roles to remove!',ephemeral=True)
        self.add_selects(list((map(lambda r : self.ctx.guild.get_role(r), self.ctx.data.get('roles')))))
        cont = discord.ui.Button(style=discord.ButtonStyle.green, label='Continue')
        cont.callback = self.remove_roles
        self.add_item(cont)
        await interaction.response.edit_message(view=self,embed=self.ctx.embed)

    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.red)
    async def cancel(self, button, interaction):
        await interaction.response.edit_message(content='Cancelled.', embed=None, view=None)
        self.stop()    