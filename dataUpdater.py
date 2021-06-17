from discord.ext import commands, tasks
from datetime import datetime, timedelta

import botGlobals
import cmdImpl
# Update the database around 11pm every day

@tasks.loop(minutes=60.0)
async def updateDB():
    if datetime.now().hour == botGlobals.updateDBTime:
        print('# ALS - *** UPDATING DATA ***')
        await cmdImpl.updateImpl(bot=botGlobals.bot)

@updateDB.before_loop
async def before_my_task():

    if botGlobals.bot is not None:
        await botGlobals.bot.wait_until_ready()




