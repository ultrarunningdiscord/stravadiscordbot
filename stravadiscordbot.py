#!/usr/bin/env python3
import asyncio
import discord
import os
import humanfriendly
import json

import requests
import struct
import sys
import time


from conversions import metersToMiles, metersToFeet, getMinPerKm, getMinPerMile
from datetime import datetime, date, timedelta
from discord.ext.commands import Bot
from discord import Status

import globals
import botCommands
import help

globalData = globals.Globals()




BOT_PREFIX = ("!")
stravaBot = Bot(command_prefix=BOT_PREFIX)

# Help command isolated to its own file
stravaBot.help_command = help.MyHelpCommand()

# Add commands in the botCommands file and just update the commandList with the new function
for c in botCommands.commandList:
    stravaBot.add_command(c)

@stravaBot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(stravaBot))

# @stravaBot.command()
# async def leaderboard(ctx, *args):
#     failed = True
#     team = None
#
#     user = ctx.message.author
#     currChannel = ctx.message.channel
#
#
#     await currChannel.send('```Invalid sport, choices are nfl, nba or mlb. Type !help for full details```')


m_loop = asyncio.get_event_loop()

def main():
    global m_loop
    try:
        # Start resolve bets
        # stop_shots = Event()
        # globals.resolveThread = Resolve(stop_shots)
        # globals.resolveThread.start()
        stravaBot.run(globalData.botToken)

    finally:
        # globals.resolveThread.cancel()
        #m_loop.run_until_complete(globals.session.close())
        pass

if __name__ == '__main__':
    main()