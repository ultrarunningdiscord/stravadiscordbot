#!/usr/bin/env python3
import asyncio

from threading import Event

from discord.ext.commands import Bot

import distanceLeader
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


m_loop = asyncio.get_event_loop()

def main():
    global m_loop
    try:
        # Start distanceLeader event
        stop_shots = Event()
        globals.leaderThread = distanceLeader.DistanceLeader(stop_shots)
        globals.leaderThread.start()
        stravaBot.run(globalData.botToken)

    finally:
        globals.leaderThread.cancel()
        #m_loop.run_until_complete(globals.session.close())
        pass

if __name__ == '__main__':
    main()