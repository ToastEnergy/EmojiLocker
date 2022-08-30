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
        self.view.children[1].disabled = False # type: ignore
        self.view.children[2].disabled = False # type: ignore
        if self.selected_subpage == 0:
            self.view.children[1].disabled = True # type: ignore
        if self.selected_subpage == len(self.embeds[self.selected_page]) - 1:
            self.view.children[2].disabled = True # type: ignore

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

class SupportView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        button = discord.ui.Button(
            style=discord.ButtonStyle.url, url=config.support_server, label='Support server')
        self.add_item(button)