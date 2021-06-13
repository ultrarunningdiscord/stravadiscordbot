import discord
import os
import sys

from discord.ext import commands

import botGlobals

async def helpMsg():
    embed = discord.Embed()
    embed = discord.Embed(color=0x00ff00)
    embed.title = f"**{botGlobals.STRAVACLUB_PRETTYNAME} Strava Club:**\n"

    stravaMsg = 'Join our Strava club: https://www.strava.com/clubs/' + botGlobals.STRAVACLUB + '\n'

    stravaMsg += 'Show weekly distance leaderboard: `!leaderboard` or `!lb`. Use `!fullboard` to see all athletes.\n'
    stravaMsg += 'Show weekly vert leaderboard: `!vertleaderboard` or just `!vertlb` Use `!fullvert to see all athletes.`\n'
    stravaMsg += 'Show 7-day statistics: `!stats`\n'
    stravaMsg += 'Show this message: `!strava or !help`\n'
    #stravaMsg += 'Register Discord ID w/ Strava ID for leaderboards and distance kings: Type `!register` for more details'
    embed.description = stravaMsg

    return embed

class MyHelpCommand(commands.DefaultHelpCommand):
    def get_command_signature(self, command):
        return "{0.clean_prefix}{1.qualified_name} {1.signature}".format(self, command)

    async def send_bot_help(self, mapping):
        ctx = self.context

        await self.helpImpl(ctx)

    async def helpImpl(self, ctx=None):
        embed = await helpMsg()
        if ctx is not None:
            currChannel = ctx.message.channel


            await currChannel.send(embed=embed)
