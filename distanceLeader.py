from discord.ext import commands, tasks
from datetime import datetime, timedelta

import botGlobals
import cmdImpl

@tasks.loop(minutes=60)
async def crownDistanceLeaders():
    if datetime.now().hour == botGlobals.resolveTime and datetime.now().weekday() == botGlobals.resolveDay:
        print('# ALS - crown leaders')


@crownDistanceLeaders.before_loop
async def before_my_task():
    if botGlobals.bot is not None:
        await botGlobals.bot.wait_until_ready()
