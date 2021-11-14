import inspect

import asyncpg
import config
import discord
from discord.ext import commands
from utils import views


class Settings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def update_cache_key(self, guild, key, value):
        cache = self.bot.guilds_cache

        if not cache.get(guild):
            cache[guild] = {key: value}
        cache[guild].update({key: value})

    async def cog_check(self, ctx):
        if not ctx.guild:
            raise commands.NoPrivateMessage()
        if not ctx.author.guild_permissions.manage_guild:
            raise commands.MissingPermissions(['Manage server'])
        return True

    @commands.group(invoke_without_command=True,aliases=['setting'])
    async def settings(self, ctx):
        """View the server settings"""
        data = (await self.bot.db.get_guild(ctx.guild.id)) or {}
        if not data:
            roles = 'No roles'
            prefix = config.prefix
        else:
            prefix = data.get('prefix') or config.prefix
            roles = ', '.join(
                map(lambda r: f'<@&{r}>', data.get('roles'))) or 'No roles'
        embed = discord.Embed(title='Emoji Locker\'s settings',
                              color=config.color,
                              description=f'''**Available settings**
- `prefix` (the bot's prefix)
- `roles` (the default roles that will be always included when you lock an emoji, useful for allowing emoji access to server admins)

Use `{ctx.prefix}settings <setting>` to change a setting

**Current settings**
- Prefix : `{prefix}`
- Persistent roles : {roles}

''')
        await ctx.reply_embed(embed=embed)

    @settings.command()
    async def prefix(self, ctx, *, prefix=None):
        """Change the bot's prefix"""
        if not prefix:
            data = await self.bot.db.get_guild(ctx.guild.id)
            if not data:
                prefix = config.prefix
            else:
                prefix = data.get('prefix') or config.prefix
            embed = discord.Embed(title=f'{ctx.guild.name}\'s prefix')
            embed.description = f'The prefix for this server is `{prefix}`\nUse `{ctx.prefix}settings prefix newprefix` to change it'
            return await ctx.reply_embed(embed=embed)
        if len(prefix) > 12:
            return await ctx.reply(f'The prefix is too long! {len(prefix)}/12')
        await self.bot.db.update_prefix(ctx.guild.id, prefix)
        self.update_cache_key(ctx.guild.id, 'prefix', prefix)
        await ctx.reply('☑')

    @settings.group(invoke_without_command=True,aliases=['role','persistent'])
    async def roles(self, ctx):
        """Change the server's persistent roles. Persistent roles are roles applied in every emoji lock operation
        Useful to keep roles like admin always able to use emojis"""
        ctx.data = await self.bot.get_persistent_roles(ctx)
        if not ctx.data:
            roles = "There are no persistent roles for this server"
        else:
            roles = f"The persistent roles for this server are {', '.join(map(lambda r : r.mention ,ctx.data))}"
        ctx.embed = discord.Embed(
            title=f'{ctx.guild.name}\'s persistent roles')
        ctx.embed.description = roles
        view = views.RolesView(ctx)
        await ctx.reply_embed(embed=ctx.embed, view=view)
        await view.wait()

    @roles.command()
    async def add(self, ctx, roles: commands.Greedy[discord.Role]):
        """Add a persistent role to the server's settings"""
        if len(roles) == 0:
            raise commands.MissingRequiredArgument(inspect.Parameter(
                name='roles', kind=inspect.Parameter.POSITIONAL_ONLY))
        roles = map(lambda r: r.id, roles)
        try:
            await self.bot.db.add_roles(ctx.guild.id, roles)
        except asyncpg.exceptions.UniqueViolationError:
            raise commands.BadArgument('One of the roles was already added.')
        await ctx.reply('☑')

    @roles.command()
    async def delete(self, ctx, roles: commands.Greedy[discord.Role]):
        """Remove a persistent role to the server's settings"""
        if len(roles) == 0:
            raise commands.MissingRequiredArgument(inspect.Parameter(
                name='roles', kind=inspect.Parameter.POSITIONAL_ONLY))
        roles = map(lambda r: r.id, roles)
        await self.bot.db.delete_roles(roles)
        await ctx.reply('☑')

    @roles.command(aliases=['refresh'])
    async def sync(self, ctx):
        """Lock emojis to newly added persistent roles"""
        roles = await self.bot.get_persistent_roles(ctx)
        emojis = [emoji for emoji in ctx.guild.emojis if not set(roles).issubset(emoji.roles)]
        if not emojis:
            return await ctx.reply('Nothing to sync.')
        message = await ctx.reply(f'Updating {len(emojis)} emojis...')
        for i, emoji in enumerate(emojis):
            await emoji.edit(roles=set(emoji.roles).union(roles))
            try:
                await message.edit(f'{i}/{len(emojis)}')
            except:
                pass
        await message.edit(f'Updated {len(emojis)} emojis.')
def setup(bot):
    bot.add_cog(Settings(bot))
