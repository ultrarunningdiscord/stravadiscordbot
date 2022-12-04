#!/usr/bin/env python3
import asyncio

from threading import Event

import discord
from discord.ext.commands import Bot

import botActivity
import botGlobals
import botCommands
import botMonthly
import dataUpdater
import distanceLeader
import help

BOT_PREFIX = ("!")
intents = discord.Intents.default()
intents.members = True
stravaBot = Bot(command_prefix=BOT_PREFIX, intents=intents)

# Help command isolated to its own file
stravaBot.help_command = help.MyHelpCommand()

# Add commands in the botCommands file and just update the commandList with the new function
for c in botCommands.commandList:
    stravaBot.add_command(c)

@stravaBot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(stravaBot))
    dataUpdater.updateDB.start()
    distanceLeader.crownDistanceLeaders.start()
    botActivity.runningEvent.start()
    botMonthly.updateMonthlyData.start()


m_loop = asyncio.get_event_loop()

def main():
    botGlobals.init(stravaBot=stravaBot) # Initialize all the environment variables, etc.
    global m_loop
    try:
        stravaBot.run(botGlobals.botToken)

    finally:
        #m_loop.run_until_complete(globals.session.close())
        dataUpdater.updateDB.cancel()
        distanceLeader.crownDistanceLeaders.cancel()
        botActivity.runningEvent.cancel()
        botMonthly.updateMonthlyData.cancel()
        pass

if __name__ == '__main__':
    main()
