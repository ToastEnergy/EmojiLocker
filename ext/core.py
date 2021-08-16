import discord
from discord.ext import commands


class Core(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.guild_only()
    @commands.has_guild_permissions(manage_emojis=True)
    @commands.bot_has_guild_permissions(manage_emojis=True)
    async def lock(self, ctx, emoji: discord.Emoji, *, roles):

        if emoji.guild != ctx.guild:
            return await ctx.send('This emoji appears to be from another server')
        roles = roles.split(',')

        # Raises commands.BadArgument if any of the roles are invalid
        roles = set([await commands.RoleConverter().convert(ctx, role.strip()) for role in roles])

        await emoji.edit(name=emoji.name, roles=roles)

        description = f'''
🔒 I have succesfully locked the '{emoji.name}' emoji.\n
ℹ️ Now only the people with at least one of the roles that you specified ({', '.join([r.mention for r in roles])}) will be able to use the emoji'''
        if not ctx.channel.permissions_for(ctx.guild.me).embed_links:
            return await ctx.send(description+'\n\nPlease consider giving me the embed links permissions to see nicer messages')

        embed = discord.Embed(title='Emoji succesfully locked',
                              description=description, color=0x2ecc71)
        embed.set_footer(
            text="If you can't use the emoji but you have at least one of these roles try to fully restart your Discord app")
        embed.set_thumbnail(url=emoji.url)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    @commands.has_guild_permissions(manage_emojis=True)
    @commands.bot_has_guild_permissions(manage_emojis=True)
    async def unlock(self, ctx, emoji: discord.Emoji):

        if emoji.guild != ctx.guild:
            return await ctx.send('This emoji appears to be from another server')

        await emoji.edit(name=emoji.name, roles=[])

        description = f'''
🔒 I have succesfully unlocked the '{emoji.name}' emoji.\n
ℹ️ Now everyone will be able to use the emoji'''
        if not ctx.channel.permissions_for(ctx.guild.me).embed_links:
            return await ctx.send(description+'\n\nPlease consider giving me the embed links permissions to see nicer messages')

        embed = discord.Embed(title='Emoji succesfully locked',
                              description=description, color=0x2ecc71)
        embed.set_footer(
            text="If you can't use the emoji try to fully restart your Discord app")
        embed.set_thumbnail(url=emoji.url)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Core(bot))
