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
        self.successful = 0
        self.failed = 0
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
                    self.successful += 1
                except:
                    self.failed += 1
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
        self.succesfull = 0
        self.failed = 0
        super().__init__(ctx)

    @discord.ui.button(label='Keep', style=discord.ButtonStyle.green)
    async def keep(self, button, interaction):
        if len(self.ctx.roles) == 0:
            return await interaction.response.send_message('Select at least one role', ephemeral=True)
        await interaction.response.defer()
        message = await interaction.original_message()
        await self.do_lockall(False, message)

    @discord.ui.button(label='Overwrite', style=discord.ButtonStyle.blurple)
    async def overwrite(self, button, interaction):
        if len(self.ctx.roles) == 0:
            return await interaction.response.send_message('Select at least one role', ephemeral=True)
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
                    self.failed += 1
                i += 1
                await message.edit(content=f'{i}/{len(self.ctx.guild.emojis)}')
            embed = discord.Embed(title='Emojis succesfully locked', color=config.color,
                                  description=f'''🔒 I have succesfully locked all of your server emojis with {self.failed} failed edits..\n
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
        try:
            await self.ctx.sent_message.edit(view=self)
        except:
            pass

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
    async def _next(self, button, interaction):
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

    async def __continue(self, interaction: discord.Interaction):
        if len(self.ctx.emojis) == 0:
            return await interaction.response.send_message('Select at least one emoji', ephemeral=True)
        await interaction.response.defer()
        message = await interaction.original_message()
        await self.do_bulk(message)

    @property
    def confirm_embed(self):
        return discord.Embed(title='Emojis succesfully unlocked', color=config.color,
                             description=f'''🔓 I have succesfully unlocked {self.successful} emojis with {self.failed} failed edits.\n
ℹ️ Now everyone will be able to use these emojis in your server''').set_footer(
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

    async def __continue(self, interaction: discord.Interaction):
        if self.step == 0:
            if len(self.ctx.emojis) == 0:
                return await interaction.response.send_message('Select at least one emoji', ephemeral=True)
            self.clear_items()
            self.add_item(self._continue)
            self.add_item(self.cancel)
            for i in range(0, len(self.ctx.guild.roles[1:]), 25):
                s = RoleSelectMenu(
                    self.ctx, self.ctx.guild.roles[1:][i:i + 25])
                self.add_item(s)
                self._roles[s] = set()
            self.ctx.embed.description = "Select the roles which will be able to use the selected emojis with the menu below, then click continue"
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
        return discord.Embed(title='Emojis succesfully locked', color=config.color,
                             description=f'''🔓 I have succesfully locked {self.successful} emojis with {self.failed} failed edits.\n
ℹ️ Now only the people with at least one of the roles that you specified ({','.join([r.mention for r in self.ctx.roles])}) will be able to use the emojis''').set_footer(
            text='If you can\'t use the emojis try to fully restart your Discord app')


class RolesView(OwnView):
    def __init__(self, ctx):
        self._roles = {}
        super().__init__(ctx)

    def add_selects(self, roles):
        for i in range(0, len(roles), 25):
            s = RoleSelectMenu(self.ctx, roles[i:i + 25], False)
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
            alr_added = set(self.ctx.data)
        self.add_selects(list(set(self.ctx.guild.roles[1:])-alr_added))
        cont = discord.ui.Button(
            style=discord.ButtonStyle.green, label='Continue')
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
            self.ctx.embed.description = "There are no persistent roles for this server"
        else:
            self.ctx.embed.description = f"The persistent roles for this server are {', '.join(map(lambda r : r.mention ,self.ctx.data))}"
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
            self.ctx.embed.description = "There are no persistent roles for this server"
        else:
            self.ctx.embed.description = f"The persistent roles for this server are {', '.join(map(lambda r : r.mention ,self.ctx.data))}"
        await interaction.followup.edit_message(message_id=interaction.message.id, view=self, embed=self.ctx.embed)

    @discord.ui.button(label='Remove', style=discord.ButtonStyle.blurple)
    async def remove(self, button, interaction):
        self.ctx.embed.description = 'You are removing some persistent roles, select them with the menu below then click continue'
        self.ctx.roles = set()
        self.remove_item(button)
        self.remove_item(self.add)
        if not self.ctx.data:
            return await interaction.response.send_message('No roles to remove!', ephemeral=True)
        self.add_selects(self.ctx.data)
        cont = discord.ui.Button(
            style=discord.ButtonStyle.green, label='Continue')
        cont.callback = self.remove_roles
        self.add_item(cont)
        await interaction.response.edit_message(view=self, embed=self.ctx.embed)

    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.red)
    async def cancel(self, button, interaction):
        await interaction.response.edit_message(content='Cancelled.', embed=None, view=None)
        self.stop()


class HelpSelect(discord.ui.Select):
    def __init__(self, help, mapping):
        options = [
            discord.SelectOption(
                label='Basics', description='Learn about basic commands', emoji='🟥', value="0"),
            discord.SelectOption(
                label='Settings', description='Help about the bot\'s settings', emoji='🟩', value="1"),
            discord.SelectOption(
                label='All commands', description='Full commands reference', emoji='🟦', value="2")
        ]

        self.embeds = [

            [
                discord.Embed(title="Basics", description=f"""
                You can manage your emojis whitelists with 2 basic commands, `lock` and `unlock`

                The **lock** command can add a role to the emoji's whitelist, so only who has at least one of the roles in the whitelist will be able to use emoji.

                Just run `{help.context.prefix}lock` and follow the steps in the gif below.
                """,color=config.color)
                .set_image(url="https://i.imgur.com/C2itzck.gif"),

                discord.Embed(title="Basics", description="""You can also use the **non-interactive** version of the **lock** command.
                
                As you can see from this gif, the locked emojis completly disappear from the emoji picker if you don't have the required roles.
                """,color=config.color)
                .set_image(url="https://i.imgur.com/37zjqX7.gif"),
                
                discord.Embed(title="Basics", description=f"""
                The **unlock** command disables the whitelist for an emoji, so everyone will be able to use it.

                The command also have a **non-interactive** version, `{help.context.prefix}unlock <emoji>` (don't actually type <>)

                Its usage is very similare to the lock command, just run `{help.context.prefix}unlock` and follow the steps in the gif below.


                """,color=config.color).set_image(url="https://i.imgur.com/AKvKh8b.gif")
            ],
            [
                # TODO
                discord.Embed(title="Settings help", description="""
You can customize two settings to make it fit your ideal experience, these are:

- Prefix

""")
                .set_image(url="https://i.imgur.com/37zjqX7.gif"),

                discord.Embed(title="advanced", description="Non gg")
            ]

        ]
        super().__init__(placeholder='Select a tutorial', options=options)
        self.selected_page = 0
        self.selected_subpage = 0
        self.commands = mapping


    @property
    def visualized_page(self):
        return self.selected_subpage + 1

    def update(self):
        self.view.children[1].disabled = False
        self.view.children[2].disabled = False
        if self.selected_subpage == 0:
            self.view.children[1].disabled = True
        if self.selected_subpage == len(self.embeds[self.selected_page])-1:
            self.view.children[2].disabled = True

        self.embed = self.embeds[self.selected_page][self.selected_subpage]
        self.embed.set_footer(
            text=f'Page {self.visualized_page}/{len(self.embeds[self.selected_page])}')

    async def back(self, interaction: discord.Interaction):
        self.selected_subpage -= 1
        self.update()
        await interaction.response.edit_message(embed=self.embed,view=self.view)

    async def _next(self, interaction: discord.Interaction):
        self.selected_subpage += 1
        self.update()
        await interaction.response.edit_message(embed=self.embed,view=self.view)
        
    async def callback(self, interaction: discord.Interaction):
        option = int(interaction.data['values'][0])
        embeds = self.embeds[option]
        self.view.clear_items()
        self.view.add_item(self)

        if len(embeds) > 1:
            back = discord.ui.Button(
                style=discord.ButtonStyle.blurple, emoji="◀️")
            back.callback = self.back
            _next = discord.ui.Button(
                style=discord.ButtonStyle.blurple, emoji="▶️")
            _next.callback = self._next
            self.view.add_item(back)
            self.view.add_item(_next)
        self.selected_page = option
        self.selected_subpage = 0
        self.update()
        await interaction.response.edit_message(embed=self.embed, view=self.view)
