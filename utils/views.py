import asyncpg
import config
import discord


class UpvoteView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=0)
        button = discord.ui.Button(
            style=discord.ButtonStyle.url, url="https://top.gg/bot/609087387695316992/vote", label='Upvote the bot')
        self.add_item(button)
        self.stop()


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
    async def _continue(self, button, interaction):
        await interaction.response.defer()
        message = await interaction.original_message()
        await self.do_bulk(message, True)

    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.red)
    async def cancel(self, button, interaction):
        await interaction.response.edit_message(content='Cancelled.', embed=None, view=None)
        self.stop()

    @discord.ui.button(label="Remove persistent", style=discord.ButtonStyle.red)
    async def toggle_persistent(self, button, interaction):
        if button.label == "Remove persistent":
            print(f"ctx.roles : {self.ctx.roles}")
            print(f"ctx.persistent : {self.ctx.persistent}")
            self.ctx._og_persistent = self.ctx.persistent
            self.ctx.persistent = set()
            print(f"ctx.roles after : {self.ctx.roles}")
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


class SupportView(OwnView):
    def __init__(self, ctx):
        super().__init__(ctx)
        button = discord.ui.Button(
            style=discord.ButtonStyle.url, url=config.support_server, label='Support server')
        self.add_item(button)

    @discord.ui.button(style=discord.ButtonStyle.blurple, label='Show command help')
    async def show_help(self, button, interaction):
        self.remove_item(button)
        embed = self.ctx.embed
        command = self.ctx.command
        embed.add_field(name='Command help', value=f'''`{command.name}`
aliases : {", ".join(command.aliases) or "No aliases"}
usage : {command.usage}
> {command.help or 'No help provided'}
''')
        await interaction.response.edit_message(view=self, embed=embed, content=None)


class PacksView(OwnView):
    def __init__(self, ctx):
        super().__init__(ctx)
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

    @discord.ui.button(style=discord.ButtonStyle.blurple, emoji='◀️')
    async def back(self, button, interaction):
        self.page -= 1
        self.update()
        await interaction.response.edit_message(view=self, embed=self.ctx.embed)

    @discord.ui.button(style=discord.ButtonStyle.grey, emoji='⏹️')
    async def _stop(self, button, interaction):
        for x in self.children:
            x.disabled = True
        await interaction.response.edit_message(view=self)
        self.stop()

    @discord.ui.button(style=discord.ButtonStyle.blurple, emoji='▶️')
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
    async def add(self, button, interaction):
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
    async def remove(self, button, interaction):
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


class HelpSelect(discord.ui.Select):
    def __init__(self, _help, mapping):
        options = [
            discord.SelectOption(
                label='Main menu', description='Introduction', emoji='🏠', value='0', default=True
            ),
            discord.SelectOption(
                label='Basics', description='Start here!', emoji='🔒', value='1'),
            discord.SelectOption(label='Bulk actions', description='Learn about bulk commands like lockall', emoji='📚',
                                 value='2'),
            discord.SelectOption(
                label='Advanced Settings', description='Help about the bot\'s customizations', emoji='⚙️', value='3'),
            discord.SelectOption(
                label='All commands', description='Full commands reference', emoji='❓', value='4')
        ]

        self.embeds = [
            [
                _help.start_embed
            ],
            [
                discord.Embed(title='Basics', description=f'''
You can manage your emojis whitelists with 2 basic commands, `lock` and `unlock`

The **lock** command can add a role to the emoji's whitelist, so only who has at least one of the roles in the whitelist will be able to use emoji.

Just run `{_help.context.prefix}lock` and follow the steps in the gif below.
''', color=config.color).set_image(url='https://i.imgur.com/dFDkbjM.gif'),

                discord.Embed(title="Basics", description='''You can also use the **non-interactive** version of the **lock** command.
                
As you can see from this gif, the locked emojis completely disappear from the emoji picker if you don't have the required roles.
''', color=config.color).set_image(url='https://i.imgur.com/oUmEktv.gif'),

                discord.Embed(title="Basics", description=f'''
The **unlock** command disables the whitelist for an emoji, so everyone will be able to use it.

The command also has a **non-interactive** version, `{_help.context.prefix}unlock <emoji>` (don't actually type <>)

Its usage is very similar to the lock command, just run `{_help.context.prefix}unlock` and follow the steps in the gif below.
''', color=config.color).set_image(url='https://i.imgur.com/aNFtNcC.gif')
            ],
            [discord.Embed(title='Bulk commands', description=f'''
If you have to lock/unlock multiple emojis or even all of your server emojis you can do so with these commands:

- `lockall`
- `unlockall`
- `multiple`
- `massunlock`

Learn more about these commands in the next pages
''', color=config.color),
             discord.Embed(title='Bulk commands | lockall', description=f'''
The `lockall` command locks every emoji of the server for you. You can run it in **guided mode** or by specifying the roles (**manual mode**).

If you want to use it in **guided mode** just run `{_help.context.prefix}lockall` and follow the interactive setup.

If you don't want to follow the interactive setup use the **manual mode** by running `{_help.context.prefix}lockall @role1 "Role 2" @role3`, as you can see you can pass both the mention and the role name, if the name has spaces in it, put it in quotes.
The roles passed will be the roles to which every emoji of the server will be whitelisted.
''', color=config.color).set_image(url='https://i.imgur.com/l0rWqV5.gif'),
             discord.Embed(title='Bulk commands | unlockall', description=f'''
`unlockall` unlocks every emoji of the server, making them available to everyone

To run it, just type `{_help.context.prefix}unlockall` and click the confirm button
''', color=config.color).set_image(url='https://i.imgur.com/1aDH75A.gif'),
             discord.Embed(title='Bulk commands | multiple', description=f'''
`multiple` allows you to lock multiple emojis to multiple roles, as the **manual** syntax can be confusing, you can use the **guided mode** _(**recommended**)_.

To run `multiple` in **guided mode**, just type `{_help.context.prefix}multiple`

If you want to use the **manual mode** the syntax is the following:
`{_help.context.prefix}multiple emoji1 :emoji2: , @role1 Role2`

**Note that the comma is required and role names with spaces aren't supported (you can use role IDs)**
''', color=config.color).set_image(url='https://i.imgur.com/DTF92b3.gif')
             ],
            [
                discord.Embed(title='Settings help', description=f'''
There are two configurable settings, the bot's **prefix** and the **persistent roles**, read the next pages to learn more.
''', color=config.color),

                discord.Embed(title='Settings help', description=f'''
You can change the **prefix** of the bot with `{_help.context.prefix}settings prefix <prefix>` (don't type <>)

After changing the bot's prefix, you will no longer able to invoke commands using `e!` but with the prefix you just set.

If you forget the prefix, you will still be able to use the bot by @mentioning the bot.
''', color=config.color).set_image(url='https://i.imgur.com/PAoNK7Q.gif'),
                discord.Embed(title='Settings help', description=f'''
You may want to keep every emoji available to some roles, the **persistent roles** feature helps you setting this up. For instance you can use this feature to let admins use every emoji.
Adding a role to the persistent roles list will automatically lock the emojis you are locking with other commands to the persistent roles.

To set this up, run `{_help.context.prefix}settings roles` and follow the instructions in the gif below.
''', color=config.color).set_image(url='https://i.imgur.com/kavEM0f.gif'),
                discord.Embed(title='Settings help', description=f'''
If you edit your persistent roles setup you may notice that previously added emojis are not synced with the persistent roles, to fix this just run `{_help.context.prefix}settings roles sync`.
''', color=config.color).set_image(url='https://i.imgur.com/EwySUSi.gif'),
            ],
            [discord.Embed(title=f'Commands - {cog.qualified_name}', description=_help.get_cog_desc(cog),
                           colour=discord.Colour.red()) for cog in mapping]

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
        if self.selected_subpage == len(self.embeds[self.selected_page]) - 1:
            self.view.children[2].disabled = True

        self.embed = self.embeds[self.selected_page][self.selected_subpage]
        self.embed.set_footer(
            text=f'Page {self.visualized_page}/{len(self.embeds[self.selected_page])}')

    async def back(self, interaction: discord.Interaction):
        self.selected_subpage -= 1
        self.update()
        await interaction.response.edit_message(embed=self.embed, view=self.view)

    async def _next(self, interaction: discord.Interaction):
        self.selected_subpage += 1
        self.update()
        await interaction.response.edit_message(embed=self.embed, view=self.view)

    async def callback(self, interaction: discord.Interaction):
        option = int(interaction.data['values'][0])
        embeds = self.embeds[option]
        self.view.clear_items()
        self.view.add_item(self)

        if len(embeds) > 1:
            back = discord.ui.Button(
                style=discord.ButtonStyle.blurple, emoji='◀️')
            back.callback = self.back
            _next = discord.ui.Button(
                style=discord.ButtonStyle.blurple, emoji='▶️')
            _next.callback = self._next
            self.view.add_item(back)
            self.view.add_item(_next)
        self.selected_page = option
        self.selected_subpage = 0
        for o in self.options:
            if o.value == interaction.data['values'][0]:
                o.default = True
            else:
                o.default = False
        self.options[option].default = True
        if len(self.embeds[self.selected_page]) > 1:
            self.update()
        else:
            self.embed = self.embeds[self.selected_page][0]
        await interaction.response.edit_message(embed=self.embed, view=self.view)
