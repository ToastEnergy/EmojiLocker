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
            await message.edit(content=None, embed=self.ctx.confirm_embed)
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
        await interaction.response.defer()
        message = await interaction.original_message()
        await self.do_lockall(False, message)

    @discord.ui.button(label='Overwrite', style=discord.ButtonStyle.blurple)
    async def overwrite(self, button, interaction):
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
