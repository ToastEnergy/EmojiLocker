import discord
import inspect
from discord.ext import commands


class LockallView(discord.ui.View):
    def __init__(self, ctx):
        self.ctx = ctx
        super().__init__(timeout=240)

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

    async def interaction_check(self, interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message('This is being used by someone else!', ephemeral=True)
            return False
        return True

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
                    await emoji.edit(name=emoji.name, roles=self.ctx.roles)
                except:
                    pass
                i += 1
                await message.edit(content=f'{i}/{len(self.ctx.guild.emojis)}')
            embed = discord.Embed(title='Emojis succesfully locked', color=discord.Color.green(),
                                  description=f'''🔒 I have succesfully all of your server emojis.\n
    ℹ️ Now only the people with at least one of the roles that you specified ({','.join([r.mention for r in self.ctx.roles])}) will be able to use the emojis''')
            embed.set_footer(
                text='If you can\'t use the emojis but you have at least one of these roles try to fully restart your Discord app')
            await message.edit(content=None, embed=embed)
        except Exception as e:
            raise(e)
        finally:
            self.stop()


class UnlockallView(discord.ui.View):
    def __init__(self, ctx):
        super().__init__(timeout=240)
        self.ctx = ctx

    @discord.ui.button(label='Continue', style=discord.ButtonStyle.green)
    async def _continue(self, button, interaction):
        await interaction.response.defer()
        message = await interaction.original_message()
        await self.do_unlockall(message)

    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.red)
    async def cancel(self, button, interaction):
        await interaction.response.edit_message(content='Cancelled.', embed=None, view=None)
        self.stop()

    async def do_unlockall(self, message):
        try:
            await message.edit(content='Working...', view=None, embed=None)
            i = 0
            for emoji in self.ctx.emojis:
                try:
                    await emoji.edit(name=emoji.name, roles=[])
                except:
                    pass
                i += 1
                await message.edit(content=f'{i}/{len(self.ctx.emojis)}')
            embed = discord.Embed(title='Emojis succesfully unlocked', color=discord.Color.green(),
                                  description=f'''🔓 I have succesfully unlocked all of your server emojis.\n
    ℹ️ Now everyone will be able to use all emojis in your server''')
            embed.set_footer(
                text='If you can\'t use the emojis try to fully restart your Discord app')
            await message.edit(content=None, embed=embed)
        except Exception as e:
            raise
        finally:
            self.stop()

    async def interaction_check(self, interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message('This is being used by someone else!', ephemeral=True)
            return False
        return True


class MultipleView(discord.ui.View):
    def __init__(self, ctx):
        super().__init__(timeout=240)
        self.ctx = ctx

    @discord.ui.button(label='Continue', style=discord.ButtonStyle.green)
    async def _continue(self, button, interaction):
        await interaction.response.defer()
        message = await interaction.original_message()
        await self.do_multiple(message)

    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.red)
    async def cancel(self, button, interaction):
        await interaction.response.edit_message(content='Cancelled.', embed=None, view=None)
        self.stop()

    async def do_multiple(self, message):
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
            embed = discord.Embed(title='Emojis succesfully locked', color=discord.Color.green(),
                                  description=f'''🔓 I have succesfully locked {len(self.ctx.emojis)} emojis\n
ℹ️ Now only the people with at least one of the roles that you specified ({','.join([r.mention for r in self.ctx.roles])}) will be able to use the emojis''')
            embed.set_footer(
                text='If you can\'t use the emojis try to fully restart your Discord app')
            await message.edit(content=None, embed=embed)
        except Exception as e:
            raise(e)
        finally:
            self.stop()

    async def interaction_check(self, interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message('This is being used by someone else!', ephemeral=True)
            return False
        return True


class Core(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.guild_only()
    @commands.has_guild_permissions(manage_emojis=True)
    @commands.bot_has_permissions(manage_emojis=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.max_concurrency(1, commands.BucketType.user)
    async def lock(self, ctx, emoji: discord.Emoji, *, roles):

        if emoji.guild != ctx.guild:
            return await ctx.reply('This emoji appears to be from another server')
        roles = roles.split(',')

        # Raises commands.BadArgument if any of the roles are invalid
        roles = set([await commands.RoleConverter().convert(ctx, role.strip()) for role in roles])

        await emoji.edit(name=emoji.name, roles=roles)

        description = f'''
🔒 I have succesfully locked the '{emoji.name}' emoji.\n
ℹ️ Now only the people with at least one of the roles that you specified ({', '.join([r.mention for r in roles])}) will be able to use the emoji'''
        if not ctx.channel.permissions_for(ctx.guild.me).embed_links:
            return await ctx.reply(description+'\n\nPlease consider giving me the embed links permissions to see nicer messages')

        embed = discord.Embed(title='Emoji succesfully locked',
                              description=description, color=0x2ecc71)
        embed.set_footer(
            text="If you can't use the emoji but you have at least one of these roles try to fully restart your Discord app")
        embed.set_thumbnail(url=emoji.url)
        await ctx.reply(embed=embed)

    @commands.command()
    @commands.guild_only()
    @commands.has_guild_permissions(manage_emojis=True)
    @commands.bot_has_permissions(manage_emojis=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.max_concurrency(1, commands.BucketType.user)
    async def unlock(self, ctx, emoji: discord.Emoji):

        if emoji.guild != ctx.guild:
            return await ctx.reply('This emoji appears to be from another server')

        await emoji.edit(name=emoji.name, roles=[])

        description = f'''
🔒 I have succesfully unlocked the '{emoji.name}' emoji.\n
ℹ️ Now everyone will be able to use the emoji'''
        if not ctx.channel.permissions_for(ctx.guild.me).embed_links:
            return await ctx.reply(description+'\n\nPlease consider giving me the embed links permissions to see nicer messages')

        embed = discord.Embed(title='Emoji succesfully locked',
                              description=description, color=0x2ecc71)
        embed.set_footer(
            text="If you can't use the emoji try to fully restart your Discord app")
        embed.set_thumbnail(url=emoji.url)
        await ctx.reply(embed=embed)

    @commands.command()
    @commands.guild_only()
    @commands.has_guild_permissions(manage_emojis=True)
    @commands.bot_has_permissions(manage_emojis=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.max_concurrency(1, commands.BucketType.user)
    async def unlockall(self, ctx):
        ctx.emojis = [
            emoji for emoji in ctx.guild.emojis if len(emoji.roles) > 0]
        if len(ctx.emojis) == 0:
            return await ctx.reply('There are no locked emojis.')
        embed = discord.Embed(title='Unlocking all emojis!',
                              description=f'You are about to unlock {len(ctx.emojis)} emojis, continue?', color=discord.Color.red())
        view = UnlockallView(ctx)
        await ctx.reply(embed=embed, view=view)
        await view.wait()

    @commands.command(usage='<role,role...>')
    @commands.guild_only()
    @commands.has_guild_permissions(manage_emojis=True)
    @commands.bot_has_permissions(manage_emojis=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.max_concurrency(1, commands.BucketType.user)
    async def lockall(self, ctx, *, roles):

        roles = roles.split(',')
        ctx.roles = set([await commands.RoleConverter().convert(ctx, role.strip()) for role in roles])
        embed = discord.Embed(title='Locking all emojis!', description='''Do you want to **keep** the roles in the existent setup or overwrite them?

If you select **keep** an emoji already locked to @role1  will be locked to @role1 + the roles that you specified in the command

if you select **overwrite** it will be locked only to the roles that you just specified.
''', color=discord.Color.red())
        view = LockallView(ctx)
        await ctx.reply(embed=embed, view=view)
        await view.wait()

    @commands.command(usage='<emoji,emoji...> | <role,role...>')
    @commands.guild_only()
    @commands.has_guild_permissions(manage_emojis=True)
    @commands.bot_has_permissions(manage_emojis=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.max_concurrency(1, commands.BucketType.user)
    # None because hardcoding :tm:
    async def multiple(self, ctx, *, args=None):

        # Not using commands.Greedy because the parsing ambiguities ruins the overall UX
        if not args:
            raise commands.MissingRequiredArgument(inspect.Parameter(
                name='emojis', kind=inspect.Parameter.POSITIONAL_ONLY))
        args = args.split("|")
        if len(args) == 1:
            raise commands.MissingRequiredArgument(inspect.Parameter(
                name='roles', kind=inspect.Parameter.POSITIONAL_ONLY))
        emojis = args[0].split(',')
        roles = args[1].split(',')
        ctx.emojis = set([await commands.EmojiConverter().convert(ctx, emoji.strip()) for emoji in emojis])
        ctx.roles = set([await commands.RoleConverter().convert(ctx, role.strip()) for role in roles])
        view = MultipleView(ctx)
        await ctx.send(f'You are about to lock {len(emojis)} emojis to these roles : {", ".join([r.mention for r in ctx.roles])}\nContinue?',
                       view=view)

        await view.wait()


def setup(bot):
    bot.add_cog(Core(bot))
