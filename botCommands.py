import asyncio
import aiohttp
import discord
import humanfriendly
import json
import requests
import swagger_client as swagger_client
from swagger_client.rest import ApiException
import time

from datetime import datetime, date, timedelta
from conversions import metersToMiles, metersToFeet, getMinPerKm, getMinPerMile

from discord.ext import commands



import globals
import userData

globalData = globals.Globals()
uData = userData.UserData()
# Commands for the bot...just make sure to append to the commandList to rgister the command
commandList = []



@commands.command()
async def debug(ctx, *args):
    user = ctx.message.author
    currChannel = ctx.message.channel
    embed = discord.Embed()
    embed = discord.Embed(color=0x00ff00)
    embed.title = f"**DEBUG:**\n"
    embed.description = "I am alive and well."
    await currChannel.send(embed=embed)

commandList.append(debug)

@commands.command(name='leaderboard', aliases=('lb','foo'))
async def _leaderboard(ctx, *args):
    user = ctx.message.author
    currChannel = ctx.message.channel
    embed = discord.Embed()
    embed = discord.Embed(color=0x00ff00)
    embed.title = f"**{globalData.STRAVACLUB_PRETTYNAME} Weekly Distance Leaderboard:**\n"

    leaderboardJSON = await globalData.loadLeaderboard()

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
    await currChannel.send(embed=embed)

commandList.append(_leaderboard)

@commands.command(name='monthleaderboard', aliases=('monthlb', 'month'))
async def _monthleaderboard(ctx, *args):
    user = ctx.message.author
    currChannel = ctx.message.channel
    try:
        access_token = globalData.redis_conn.get('token').decode()
        token_expiry = globalData.redis_conn.get('expiry').decode()
    except:
        # If we except here, its due to a none byte error against decode
        # TODO there might be a better way to handle this
        access_token, token_expiry  = globalData.refresh_token()

    token_expire_time = datetime.utcnow() + timedelta(seconds=int(token_expiry))

    if datetime.utcnow() > token_expire_time:
        access_token, token_expiry  = globalData.refresh_token()
    else:
        print("Current token is active")

    stravaAuthHeader = {'Content-Type': 'application/json',
                        'Authorization': 'Bearer {}'.format(access_token)}



    # get first day of current month
    today = datetime.utcnow()
    firstDayCurrentMonth = datetime(today.year, today.month, 1)

    embed = discord.Embed()
    embed = discord.Embed(color=0x00ff00)
    embed.title = f"**{globalData.STRAVACLUB_PRETTYNAME} {today.strftime('%B')} Leaderboard:**\n"

    firstDayCurrentMonth = time.mktime(firstDayCurrentMonth.timetuple())
    page_no = 1
    per_page = 5
    leaderboard = []
    total_activities = 0
    leaderboardMsg = ''

    while 1:
        try:
            leaderboardMsg += f"------Page {page_no}------\n"
            requestParams = {'page': page_no, 'per_page': per_page}#, 'after': firstDayCurrentMonth}
            result = requests.get('https://www.strava.com/api/v3/clubs/' + globalData.STRAVACLUB + '/activities',
                                  headers=stravaAuthHeader,
                                  params=requestParams)
            clubActivities = result.json()

            for activity in clubActivities:
                # filter by type: 'Run'
                if activity['type'] != 'Run':
                    continue

                total_activities += 1
                # check if athlete exists in leaderboard
                name = activity['athlete']['firstname'] + ' ' + activity['athlete']['lastname']
                found = False
                for athlete in leaderboard:
                    if athlete['name'] == name:
                        found = True
                        athlete['distance'] += activity['distance']
                        athlete['total_elevation_gain'] += activity['total_elevation_gain']
                        athlete['num_activities'] += 1
                        break

                # otherwise add athlete to leaderboard
                if not found:
                    leaderboard.append({
                        'name': name,
                        'distance': activity['distance'],
                        'total_elevation_gain': activity['total_elevation_gain'],
                        'num_activities': 1
                    })
            if len(clubActivities) < per_page or page_no > 20:
                break
            page_no += 1
        except:
            break
    leaderboardMsg += f'{total_activities} total activities.\n'
    leaderboardMsg += f'{len(leaderboard)} total athletes.\n\n'
    if len(leaderboard) > 0:
        leaderboard.sort(key=lambda x: x['distance'], reverse=True)
    for i, athlete in enumerate(leaderboard):
        boldstr = ""
        if i < 10:
            boldstr = "**"
        leaderboardMsg +=   boldstr + str(i+1) + '. ' + \
                            athlete['name'] + ' - ' + \
                            "{:,}".format(round(athlete['distance']/1000, 2)) + \
                            ' km (' + \
                            metersToMiles(athlete['distance']) + \
                            ')' + boldstr + ' over ' + str(athlete['num_activities']) + ' runs\n'
    embed.description = leaderboardMsg
    await currChannel.send(embed=embed)

commandList.append(_monthleaderboard)

@commands.command()
async def register(ctx, *args):
    print('# ALS - register username w/ strava')
    user = ctx.message.author.id

    try:
        access_token = globalData.redis_conn.get('token').decode()
        token_expiry = globalData.redis_conn.get('expiry').decode()
    except:
        # If we except here, its due to a none byte error against decode
        # TODO there might be a better way to handle this
        access_token, token_expiry  = globalData.refresh_token()

    token_expire_time = datetime.utcnow() + timedelta(seconds=int(token_expiry))

    if datetime.utcnow() > token_expire_time:
        access_token, token_expiry = globalData.refresh_token()
    else:
        print("Current token is active")

    stravaAuthHeader = {'Content-Type': 'application/json',
                        'Authorization': 'Bearer {}'.format(access_token)}
    stravaResult = requests.get('https://www.strava.com/api/v3/athlete/',
                                headers=stravaAuthHeader)
    stravaAthleteId = json.loads(stravaResult.content)['id']
    await uData.registerStravaID(user=user, stravaId=stravaAthleteId)

commandList.append(register)

@commands.command()
async def stats(ctx, *args):
    user = ctx.message.author
    currChannel = ctx.message.channel

    try:
        access_token = globalData.redis_conn.get('token').decode()
        token_expiry = globalData.redis_conn.get('expiry').decode()
    except:
        # If we except here, its due to a none byte error against decode
        # TODO there might be a better way to handle this
        access_token, token_expiry  = globalData.refresh_token()

    token_expire_time = datetime.utcnow() + timedelta(seconds=int(token_expiry))

    if datetime.utcnow() > token_expire_time:
        access_token, token_expiry  = globalData.refresh_token()
    else:
        print("Current token is active")

    stravaAuthHeader = {'Content-Type': 'application/json',
                        'Authorization': 'Bearer {}'.format(access_token)}

    embed = discord.Embed()
    embed = discord.Embed(color=0x00ff00)
    embed.title = f"**{globalData.STRAVACLUB_PRETTYNAME} Weekly Statistics:**\n"

    stravaResult = requests.get('https://www.strava.com/api/v3/clubs/' +
                                globalData.STRAVACLUB+'/activities',
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
                    metersToMiles(totalDistance) + ')' + \
                    ' over ' + str(totalActivitiesRecorded) + ' activities. \n'
    statisticsMsg += 'Our total elevation gain is ' + \
                     "{:,}".format(round(totalElevationGain,2)) + ' m (' + \
                     metersToFeet(totalElevationGain) +'). \n'
    statisticsMsg += 'Our total time spent moving is ' + \
                     humanMovingTime + '. \n'

    embed.description = statisticsMsg
    await currChannel.send(embed=embed)

commandList.append(stats)

@commands.command()
async def strava(ctx, *args):
    # TODO fix this to use help command itself
    user = ctx.message.author
    currChannel = ctx.message.channel
    embed = discord.Embed()
    embed = discord.Embed(color=0x00ff00)
    embed.title = f"**{globalData.STRAVACLUB_PRETTYNAME} Strava Club:**\n"

    stravaMsg = 'Join our Strava club: https://www.strava.com/clubs/' + globalData.STRAVACLUB + '\n'

    stravaMsg += 'Show weekly distance leaderboard: `!leaderboard` or `!lb`\n'
    stravaMsg += 'Show weekly vert leaderboard: `!vertleaderboard` or just `!vertlb`\n'
    stravaMsg += 'Show 7-day statistics: `!stats`\n'
    stravaMsg += 'Show this message: `!strava`'
    embed.description = stravaMsg


    await currChannel.send(embed=embed)

commandList.append(strava)

@commands.command(name='vertleaderboard', aliases=('vertlb','vlb'))
async def _vertleaderboard(ctx, *args):
    user = ctx.message.author
    currChannel = ctx.message.channel
    embed = discord.Embed()
    embed = discord.Embed(color=0x00ff00)
    embed.title = f"**{globalData.STRAVACLUB_PRETTYNAME} Weekly Vert Leaderboard:**\n"

    publicLeaderboard = requests.get('https://www.strava.com/clubs/' +
                                     globalData.STRAVACLUB + '/leaderboard',
                                     headers=globalData.stravaPublicHeader)
    print('# ALS - pub header + ' + str(globalData.stravaPublicHeader))
    print('# ALS - publicLeaderboard '+ str(publicLeaderboard.content))
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
    await currChannel.send(embed=embed)

commandList.append(_vertleaderboard)

