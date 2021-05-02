#!/usr/bin/env python3
import os
import sys
import discord
import requests
import json
import humanfriendly
from conversions import metersToMiles, metersToFeet, getMinPerKm, getMinPerMile

# Grab the Discord bot token from DISCORDTOKEN environment variable
DISCORDTOKEN = os.environ.get('DISCORDTOKEN')
if DISCORDTOKEN is None:
    print("DISCORDTOKEN variable not set. Unable to launch bot.")
    sys.exit()
else:
    print("Discord token is", DISCORDTOKEN)

# Grab the Strava auth token from STRAVATOKEN environment variable
# This is used for Bearer authentication against Strava's API
STRAVATOKEN = os.environ.get('STRAVATOKEN')
if STRAVATOKEN is None:
    print("STRAVATOKEN variable not set. Unable to launch bot.")
    sys.exit()
else:
    print("Strava token is", STRAVATOKEN)

# Grab the Strava Club ID from STRAVACLUB environment variable
STRAVACLUB = os.environ.get('STRAVACLUB')
if STRAVACLUB is None:
    print("STRAVACLUB variable not set. Unable to launch bot.")
    sys.exit()
else:
    print("Strava club is", STRAVACLUB)

# Building Strava authentication header
stravaAuthHeader = {'Content-Type': 'application/json',
                    'Authorization': 'Bearer {}'.format(STRAVATOKEN)}

# Header used for requests to Strava's open/public APIs
stravaPublicHeader = {'Host': 'www.strava.com ',
                      'Accept': 'text/javascript,application/javascript ',
                      'Referer': 'https://www.strava.com/clubs/' + STRAVACLUB,
                      'X-Requested-With': 'XMLHttpRequest'}

stravaClubDetails = requests.get('https://www.strava.com/api/v3/clubs/' +
                                            STRAVACLUB,
                                            headers=stravaAuthHeader)
clubDetails = stravaClubDetails.json()

class StravaIntegration(discord.Client):

    async def on_ready(self):
        ''' Function fires when bot connects '''
        print('Logged on as', self.user)

    async def on_message(self, message):
        ''' Primary inbound message parsing function '''
        # print('Message:', message.content)

        if message.author == self.user:
            return

        if message.content == '!statistics':
            embed = discord.Embed()
            embed = discord.Embed(color=0x00ff00)
            embed.title = f"**{clubDetails['name']} Weekly Statistics:**\n"
            # Fetching overall statistics via authenticated API
            stravaResult = requests.get('https://www.strava.com/api/v3/clubs/' +
                                        STRAVACLUB+'/activities',
                                        headers=stravaAuthHeader)
            totalDistance = 0
            totalElevationGain = 0
            totalMovingTime = 0
            totalActivitiesRecorded = len(stravaResult.json())

            print("Results in dataset: ", totalActivitiesRecorded)
            print(stravaResult.json())

            for activity in stravaResult.json():
                totalDistance += activity['distance']
                totalElevationGain += activity['total_elevation_gain']
                totalMovingTime += activity['moving_time']

            humanMovingTime = humanfriendly.format_timespan(totalMovingTime)
            statisticsMsg = 'Together we have run: ' + \
                             str(round(totalDistance/1000, 2)) + \
                             ' km (' + \
                             metersToMiles(totalDistance) + ')' +\
                             ' over ' + str(totalActivitiesRecorded) + ' activities. \n'
            statisticsMsg += 'Our total elevation gain is ' + \
                              str(round(totalElevationGain,2)) + ' m (' + \
                                 metersToFeet(totalElevationGain) +'). \n'
            statisticsMsg += 'Our total time spent moving is ' + \
                              humanMovingTime + '. \n'

            embed.description = statisticsMsg
            await message.channel.send(embed=embed)

        if message.content == '!leaderboard':
            embed = discord.Embed()
            embed = discord.Embed(color=0x00ff00)
            embed.title = f"**{clubDetails['name']} Weekly Leaderboard:**\n"

            publicLeaderboard = requests.get('https://www.strava.com/clubs/' +
                                             STRAVACLUB + '/leaderboard',
                                             headers=stravaPublicHeader)

            leaderboardJSON = json.loads(publicLeaderboard.content)
            leaderboardMsg = ""
            for rankedUser in leaderboardJSON['data']:
                leaderboardMsg +=   str(rankedUser['rank']) + '. ' + \
                                    rankedUser['athlete_firstname'] + ' ' + \
                                    rankedUser['athlete_lastname'] + ' - ' + \
                                    str(round(rankedUser['distance']/1000, 2)) + \
                                    ' km (' + \
                                    metersToMiles(rankedUser['distance']) + ')\n'
            embed.description = leaderboardMsg
            await message.channel.send(embed=embed)

        if message.content == '!strava':
            embed = discord.Embed()
            embed = discord.Embed(color=0x00ff00)
            embed.title = f"**{clubDetails['name']} Strava Club:**\n"

            stravaMsg = 'Join our Strava club: https://www.strava.com/clubs/' + STRAVACLUB + '\n'
            stravaMsg += 'Show leaderboard: `!leaderboard`\n'
            stravaMsg += 'Show weekly statistics: `!statistics`\n'
            stravaMsg += 'Show this message: `!strava`'
            embed.description = stravaMsg
            await message.channel.send(embed=embed)


client = StravaIntegration()
client.run(DISCORDTOKEN)
