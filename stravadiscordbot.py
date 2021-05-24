#!/usr/bin/env python3
import os
import struct
import sys
import discord
import redis
import requests
import json
import humanfriendly
from datetime import datetime, date, timedelta
import time
from conversions import metersToMiles, metersToFeet, getMinPerKm, getMinPerMile

try:
    redis_conn = redis.Redis(host='localhost', port=6379, db=0)
except (redis.exceptions.ConnectionError, ConnectionRefusedError) as e:
    print('Redis connection error: ', e)

# Grab the Discord bot token from DISCORDTOKEN environment variable
DISCORDTOKEN = os.environ.get('DISCORDTOKEN')
if DISCORDTOKEN is None:
    print("DISCORDTOKEN variable not set. Unable to launch bot.")
    sys.exit()
else:
    pass

# Grab the Strava auth token from STRAVATOKEN environment variable
# This is used for Bearer authentication against Strava's API
STRAVAREFRESHTOKEN = os.environ.get('STRAVAREFRESHTOKEN')
if STRAVAREFRESHTOKEN is None:
    print("STRAVAREFRESHTOKEN variable not set. Unable to launch bot.")
    sys.exit()
else:
    pass

# STRAVACLIENTID environment variable
STRAVACLIENTID = os.environ.get('STRAVACLIENTID')
if STRAVACLIENTID is None:
    print("STRAVACLIENTID variable not set. Unable to launch bot.")
    sys.exit()
else:
    pass

# STRAVASECRET environment variable
STRAVASECRET = os.environ.get('STRAVASECRET')
if STRAVASECRET is None:
    print("STRAVASECRET variable not set. Unable to launch bot.")
    sys.exit()
else:
    pass

# Grab the Strava Club ID from STRAVACLUB environment variable
STRAVACLUB = os.environ.get('STRAVACLUB')
if STRAVACLUB is None:
    print("STRAVACLUB variable not set. Unable to launch bot.")
    sys.exit()
else:
    pass

# Grab the Strava Club ID from STRAVACLUB_PRETTYNAME environment variable
STRAVACLUB_PRETTYNAME = os.environ.get('STRAVACLUB_PRETTYNAME')
if STRAVACLUB_PRETTYNAME is None:
    print("STRAVACLUB_PRETTYNAME variable not set. Unable to launch bot.")
    sys.exit()
else:
    pass

# Header used for requests to Strava's open/public APIs
stravaPublicHeader = {'Host': 'www.strava.com ',
                      'Accept': 'text/javascript,application/javascript ',
                      'Referer': 'https://www.strava.com/clubs/' + STRAVACLUB,
                      'X-Requested-With': 'XMLHttpRequest'}

class StravaIntegration(discord.Client):

    async def on_ready(self):
        ''' Function fires when bot connects '''
        print('Logged on as', self.user)

    def refresh_token(self):
        print("Refreshing token")
        payload = {
                'client_id' : STRAVACLIENTID,
                'client_secret' : STRAVASECRET,
                'refresh_token' : STRAVAREFRESHTOKEN,
                'grant_type' : "refresh_token",
                'f':'json'
            }
        stravaTokenReq = requests.post('https://www.strava.com/oauth/token',
                                    data=payload)

        access_token = stravaTokenReq.json()['access_token']
        access_token_expiry = stravaTokenReq.json()['expires_at']
        try:
            redis_conn.set('token', access_token)
        except redis.RedisError as e:
            print('Redis exception: ', e)
        try:
            redis_conn.set('expiry', access_token_expiry)
        except redis.RedisError as e:
            print('Redis exception: ', e)
        return access_token, access_token_expiry

    async def on_message(self, message):
        ''' Primary inbound message parsing function '''

        if message.author == self.user:
            return

        if message.content == '!stats':
            try:
                access_token = redis_conn.get('token').decode()
                token_expiry = redis_conn.get('expiry').decode()
            except:
                # If we except here, its due to a none byte error against decode
                # TODO there might be a better way to handle this
                access_token, token_expiry  = self.refresh_token()

            token_expire_time = datetime.utcnow() + timedelta(seconds=int(token_expiry))

            if datetime.utcnow() > token_expire_time:
                access_token, token_expiry  = self.refresh_token()
            else:
                print("Current token is active")

            stravaAuthHeader = {'Content-Type': 'application/json',
                    'Authorization': 'Bearer {}'.format(access_token)}

            embed = discord.Embed()
            embed = discord.Embed(color=0x00ff00)
            embed.title = f"**{STRAVACLUB_PRETTYNAME} Weekly Statistics:**\n"

            stravaResult = requests.get('https://www.strava.com/api/v3/clubs/' +
                                        STRAVACLUB+'/activities',
                                        headers=stravaAuthHeader)
            totalDistance = 0
            totalElevationGain = 0
            totalMovingTime = 0
            totalActivitiesRecorded = len(stravaResult.json())

            print("Results in dataset: ", totalActivitiesRecorded)
            # print(stravaResult.json())

            for activity in stravaResult.json():
                totalDistance += activity['distance']
                totalElevationGain += activity['total_elevation_gain']
                totalMovingTime += activity['moving_time']

            humanMovingTime = humanfriendly.format_timespan(totalMovingTime)
            statisticsMsg = 'Together we have run: ' + \
                             "{:,}".format(round(totalDistance/1000, 2)) + \
                             ' km (' + \
                             metersToMiles(totalDistance) + ')' +\
                             ' over ' + str(totalActivitiesRecorded) + ' activities. \n'
            statisticsMsg += 'Our total elevation gain is ' + \
                              "{:,}".format(round(totalElevationGain,2)) + ' m (' + \
                                 metersToFeet(totalElevationGain) +'). \n'
            statisticsMsg += 'Our total time spent moving is ' + \
                              humanMovingTime + '. \n'

            embed.description = statisticsMsg
            await message.channel.send(embed=embed)

        if message.content == '!leaderboard' or message.content == '!lb':
            embed = discord.Embed()
            embed = discord.Embed(color=0x00ff00)
            embed.title = f"**{STRAVACLUB_PRETTYNAME} Weekly Distance Leaderboard:**\n"

            publicLeaderboard = requests.get('https://www.strava.com/clubs/' +
                                             STRAVACLUB + '/leaderboard',
                                             headers=stravaPublicHeader)

            leaderboardJSON = json.loads(publicLeaderboard.content)
            leaderboardMsg = ""
            for i, rankedUser in enumerate(leaderboardJSON['data']):
                boldstr = ""
                if i < 10:
                    boldstr = "**"
                leaderboardMsg +=   boldstr + str(rankedUser['rank']) + '. ' + \
                                    rankedUser['athlete_firstname'] + ' ' + \
                                    rankedUser['athlete_lastname'] + ' - ' + \
                                    "{:,}".format(round(rankedUser['distance']/1000, 2)) + \
                                    ' km (' + \
                                    metersToMiles(rankedUser['distance']) + \
                                    ')' + boldstr + '\n'
            embed.description = leaderboardMsg
            await message.channel.send(embed=embed)

        if message.content == '!monthleaderboard' or message.content == '!monthlb':
            try:
                access_token = redis_conn.get('token').decode()
                token_expiry = redis_conn.get('expiry').decode()
            except:
                # If we except here, its due to a none byte error against decode
                # TODO there might be a better way to handle this
                access_token, token_expiry  = self.refresh_token()

            token_expire_time = datetime.utcnow() + timedelta(seconds=int(token_expiry))

            if datetime.utcnow() > token_expire_time:
                access_token, token_expiry  = self.refresh_token()
            else:
                print("Current token is active")

            stravaAuthHeader = {'Content-Type': 'application/json',
                    'Authorization': 'Bearer {}'.format(access_token)}

            embed = discord.Embed()
            embed = discord.Embed(color=0x00ff00)
            embed.title = f"**{STRAVACLUB_PRETTYNAME} Monthly Leaderboard:**\n"

            # get first day of current month
            today = datetime.utcnow()
            firstDayCurrentMonth = datetime(today.year, today.month, 1)
            firstDayCurrentMonth = time.mktime(firstDayCurrentMonth.timetuple())
            monthActivities = []
            page_no = 1
            per_page = 5
            msg = f'TEST\n{firstDayCurrentMonth}\n'

            while 1:
                try:
                    msg += 'page ' + str(page_no) + ':\t'
                    requestParams = {'page': page_no}#, 'per_page': per_page}#, 'after': firstDayCurrentMonth}
                    msg += str(json.dumps(requestParams)) + '\n'
                    clubActivities = requests.get('https://www.strava.com/api/v3/clubs/' + STRAVACLUB + '/activities',
                                                headers=stravaAuthHeader,
                                                params=requestParams)
                    msg += 'after request\n'
                    try:
                        clubActivities = clubActivities.json()
                        msg += str(clubActivities)
                    except Exception as e:
                        msg += 'it breaks on .json()\n'
                        msg += e
                    try:
                        msg += str(dir(clubActivities))
                    except Exception as e:
                        msg += 'dir() doesnt work'
                        break
                    break
                    monthActivities.extend(clubActivities['data'])
                    if len(clubActivities['data']) < 100:
                        break
                    page_no += 1
                except Exception as e:
                    break



            embed.description = msg
            await message.channel.send(embed=embed)

        if message.content == '!vertleaderboard' or message.content == '!vertlb':
            embed = discord.Embed()
            embed = discord.Embed(color=0x00ff00)
            embed.title = f"**{STRAVACLUB_PRETTYNAME} Weekly Vert Leaderboard:**\n"

            publicLeaderboard = requests.get('https://www.strava.com/clubs/' +
                                             STRAVACLUB + '/leaderboard',
                                             headers=stravaPublicHeader)

            leaderboardJSON = json.loads(publicLeaderboard.content)
            leaderboardMsg = ""
            leaderboardJSON['data'].sort(key=lambda x: x['elev_gain'], reverse=True)
            for i, rankedUser in enumerate(leaderboardJSON['data']):
                boldstr = ""
                if i < 10:
                    boldstr = "**"
                leaderboardMsg +=   boldstr + str(i+1) + '. ' + \
                                    rankedUser['athlete_firstname'] + ' ' + \
                                    rankedUser['athlete_lastname'] + ' - ' + \
                                   "{:,}".format(round(rankedUser['elev_gain'], 2)) + \
                                    ' m (' + \
                                    metersToFeet(rankedUser['elev_gain']) + \
                                    ')' + boldstr + '\n'
            embed.description = leaderboardMsg
            await message.channel.send(embed=embed)

        if message.content == '!strava':
            embed = discord.Embed()
            embed = discord.Embed(color=0x00ff00)
            embed.title = f"**{STRAVACLUB_PRETTYNAME} Strava Club:**\n"

            stravaMsg = 'Join our Strava club: https://www.strava.com/clubs/' + STRAVACLUB + '\n'
            stravaMsg += 'Show weekly distance leaderboard: `!leaderboard` or `!lb`\n'
            stravaMsg += 'Show weekly vert leaderboard: `!vertleaderboard` or just `!vertlb`\n'
            stravaMsg += 'Show 7-day statistics: `!stats`\n'
            stravaMsg += 'Show this message: `!strava`'
            embed.description = stravaMsg
            await message.channel.send(embed=embed)


client = StravaIntegration()
client.run(DISCORDTOKEN)
