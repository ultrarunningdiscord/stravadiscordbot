import discord

from discord.ext import commands, tasks
from datetime import datetime, timedelta

import botGlobals
activityIndex = 0
events = ['UTMB..',
          'Western States 100..see you in under 24',
          'Leadville 100',
          'Hardrock 100']

@tasks.loop(minutes=60)
async def runningEvent():
    global activityIndex, events

    if activityIndex == len(events):
        activityIndex = 0
    #currActivity = discord.CustomActivity(name=events[activityIndex])
    activity = discord.Activity(type=discord.ActivityType.competing, name=events[activityIndex])
    await botGlobals.bot.change_presence(activity=activity)
    activityIndex += 1

@runningEvent.before_loop
async def before_my_task():

    if botGlobals.bot is not None:
        await botGlobals.bot.wait_until_ready()
