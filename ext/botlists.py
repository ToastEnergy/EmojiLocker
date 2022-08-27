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
import asyncio
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
        await asyncio.sleep(30)  # bot hasn't finished initialization for some reasons
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


async def setup(bot):
    await bot.add_cog(BotLists(bot))
