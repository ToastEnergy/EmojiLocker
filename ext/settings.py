import discord
from discord.ext import commands
import config
import inspect


class Settings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def update_cache_key(self, guild, key, value):
        cache = self.bot.guilds_cache

        if not cache.get(guild):
            cache[guild] = {key: value}
        cache[guild].update({key: value})

    @commands.group(invoke_without_command=True)
    async def settings(self, ctx):
        data = (await self.bot.db.get_guild(ctx.guild.id)) or {}
        prefix = data.get('prefix')
        if not data:
            roles = 'No roles'
            prefix = config.prefix
        else:
            prefix = data.get('prefix') or 'No roles'
            roles = ', '.join(
            map(lambda r: f'<@&{r}>', data.get('roles'))) or 'No roles'
        embed = discord.Embed(title='Emoji Locker\'s settings',
                              colour=discord.Colour.green(),
                              description=f'''**Available settings**
- `Prefix` (the bot's prefix)
- `Roles` (the default role that will be always included when you lock an emoji, useful for server admins)

Use `{ctx.prefix}settings <setting>` to change a setting

**Current settings**
- Prefix : `{prefix}`
- Persistent roles : {roles}

''')
        await ctx.reply_embed(embed=embed)

    @settings.command()
    async def prefix(self, ctx, *, prefix=None):
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

    @settings.group(invoke_without_command=True)
    async def roles(self, ctx):
        data = await self.bot.db.get_guild(ctx.guild.id)
        if not data:
            roles = "There are no persistent roles for this server"
        else:
            if not data.get('roles'):
                roles = "There are no persistent roles for this server"
            else:
                roles = f"The persistent roles for this server are {', '.join(map(lambda r : f'<@&{r}>' ,data.get('roles')))}"
        embed = discord.Embed(title=f'{ctx.guild.name}\'s persistent roles')
        embed.description = roles
        await ctx.reply_embed(embed=embed)

    @roles.command()
    async def add(self, ctx, roles: commands.Greedy[discord.Role]):
        if len(roles) == 0:
            raise commands.MissingRequiredArgument(inspect.Parameter(
                name='roles', kind=inspect.Parameter.POSITIONAL_ONLY))
        roles = map(lambda r: r.id, roles)
        await self.bot.db.add_roles(ctx.guild.id, roles)
        roles = await self.bot.db.get_roles(ctx.guild.id)
        self.update_cache_key(ctx.guild.id, 'roles',
                              map(lambda r: r['role_id'], roles))
        await ctx.reply('☑')

    @roles.command()
    async def delete(self, ctx, roles: commands.Greedy[discord.Role]):
        if len(roles) == 0:
            raise commands.MissingRequiredArgument(inspect.Parameter(
                name='roles', kind=inspect.Parameter.POSITIONAL_ONLY))
        roles = map(lambda r: r.id, roles)
        await self.bot.db.delete_roles(roles)
        await ctx.reply('☑')


def setup(bot):
    bot.add_cog(Settings(bot))
