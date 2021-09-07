import discord
from discord.ext import commands

# this probably sucks but I tried

slash_commands = {}


def slashcommand(**kwargs):
    def decorator(func):
        return SlashCommand(func, **kwargs)
    return decorator


class SlashCommand:
    def __init__(self, func, **kwargs):
        self.name = kwargs.get('name') or func.__name__
        self.description = kwargs.get('description')
        self.guild_id = kwargs.get('guild_id')
        self.options = kwargs.get('options')
        self.callback = func

        self.json = {
            "name": self.name,
            "description": self.description,
            "type": 1,
            "options": []
        }
        if self.options:
            for option in self.options:
                self.json["options"].append(option)
        slash_commands[self.name] = self

    async def register(self, bot):
        if self.guild_id:
            await bot.http.upsert_guild_command(bot.user.id, self.guild_id, self.json)
        else:
            await bot.http.upsert_global_command(bot.user.id, self.json)


class SlashCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.already_registered = False

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.already_registered:
            for command in slash_commands.values():
                await command.register(self.bot)
            self.already_registered = True

    @slashcommand(description='gg')
    async def lock(self, interaction):
        await interaction.response.send_message('gg')

    @commands.Cog.listener()
    async def on_interaction(self, interaction):
        if interaction.type == discord.InteractionType.application_command:
            command = slash_commands.get(interaction.data['name'])
            if command:
                await command.callback(self, interaction)


def setup(bot):
    bot.add_cog(SlashCommands(bot))
