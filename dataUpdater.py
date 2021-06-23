from discord.ext import commands, tasks
from datetime import datetime, timedelta

import botGlobals
import cmdImpl
import userData
# Update the database around 11pm every day

@tasks.loop(minutes=60.0)
async def updateDB():
    if datetime.now().hour == botGlobals.updateDBTime:
        # Update nicknames, avatars, etc.
        await cmdImpl.updateImpl(bot=botGlobals.bot)
        # Clear out the any expired leaderboard caches
        await userData.clearLeaderBoardCache()

@updateDB.before_loop
async def before_my_task():

    if botGlobals.bot is not None:
        await botGlobals.bot.wait_until_ready()




