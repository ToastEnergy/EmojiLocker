import discord
from discord.ext import commands
from utils import views

# this probably sucks but I tried

slash_commands = {}


class FakeMessage(discord.Message):
    def __init__(self, channel):
        self.id = 0
        self.content = 'Slash command'
        self.channel = channel


class InteractionContext:
    def __init__(self, command, interaction):
        self.command = command
        self.interaction = interaction
        self.author = interaction.user
        self.guild = interaction.guild
        self.channel = self.guild.get_channel(interaction.channel_id)
        self.bot = command.bot
        self.reply_embed = self.send_message
        self.message = FakeMessage(self.channel)

    async def send_message(self, *args, **kwargs):
        await self.interaction.followup.send(*args, **kwargs)


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
                command.bot = self.bot
                await command.register(self.bot)
            self.already_registered = True

    @commands.Cog.listener()
    async def on_interaction(self, interaction):
        if interaction.type == discord.InteractionType.application_command:
            command = slash_commands.get(interaction.data['name'])
            if command:
                try:
                    ctx = InteractionContext(command, interaction)
                    self.bot.dispatch('command', ctx)
                    await interaction.response.defer()
                    if hasattr(command, '__commands_checks__'):
                        await discord.utils.async_all(check(ctx) for check in command.__commands_checks__)
                    await command.callback(self, ctx)
                except Exception as error:
                    self.bot.dispatch('command_error', ctx, error)
                else:
                    self.bot.dispatch('command_completion', ctx)

    @commands.has_guild_permissions(manage_emojis=True)
    @slashcommand(name='lock', guild_id=609363464170897437, description='Locks an emoji')
    async def lock_slash(self, ctx):
        await self.bot.get_command('wizard').__call__(ctx)

    @slashcommand(name='packs', guild_id=609363464170897437, description='View the server\'s emoji packs')
    async def packs_slash(self, ctx):
        await self.bot.get_command('packs').__call__(ctx)

    @commands.has_guild_permissions(manage_emojis=True)
    @slashcommand(name='unlock', guild_id=609363464170897437, description='Unlocks an emoji')
    async def unlock_slash(self, ctx):
        await self.bot.get_command('wizard unlock').__call__(ctx)


def setup(bot):
    bot.add_cog(SlashCommands(bot))
