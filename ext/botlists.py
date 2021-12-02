import aiohttp
import discord
from discord.ext import commands, tasks
import config


class BotLists(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.topgg = f"https://top.gg/api/bots/{self.bot.user.id}/stats"
        self.dbots = f"https://discord.bots.gg/api/v1/bots/{self.bot.user.id}/stats"
        self.autopost.start()

    @tasks.loop(minutes=30)
    async def autopost(self):
        try:
            payload = {"server_count": len(self.bot.guilds), "shard_count": len(self.bot.shards)}
            headers = {"Authorization": config.DBL_TOKEN}
            r = await self.bot.session.post(self.topgg, data=payload, headers=headers)
            t = await r.text()
            print(f"Server count posted to top.gg with status code {r.status} {t}")
        except:
            print("Failed to post server count to top.gg")

        try:
            payload = {"guildCount": len(self.bot.guilds), "shardCount": len(self.bot.shards)}
            headers = {"Authorization": config.DBOTS_TOKEN}
            r = await self.bot.session.post(self.dbots, data=payload, headers=headers)
            t = await r.text()
            print(f"Server count posted to discord.bots.gg with status code {r.status} {t}")
        except:
            print("Failed to post server count to discord.bots.gg")

    def cog_unload(self):
        self.autopost.cancel()


def setup(bot):
    bot.add_cog(BotLists(bot))
