import discord
import humanfriendly
import json
import requests
import time

from datetime import datetime, date, timedelta
from conversions import metersToMiles, metersToFeet, getMinPerKm, getMinPerMile

from discord.ext import commands

import botGlobals
import cmdImpl
import help
import userData


# Commands for the bot...just make sure to append to the commandList to rgister the command
commandList = []



@commands.command()
async def debug(ctx, *args):
    user = ctx.message.author
    currChannel = ctx.message.channel
    dmChannel = user.dm_channel
    if dmChannel is None:
        dmChannel = await user.create_dm()
    embed = discord.Embed()
    embed = discord.Embed(color=0x00ff00)
    embed.title = f"**DEBUG:**\n"
    embed.description = botGlobals.debugInit
    await dmChannel.send(embed=embed)

commandList.append(debug)

@commands.command(name='fulllb', aliases=('fullleaderboard','fullboard'))
async def _fullleaderboard(ctx, *args):
    user = ctx.message.author
    currChannel = ctx.message.channel
    await cmdImpl.leaderboardImpl(channel=currChannel, bot=ctx.bot)

commandList.append(_fullleaderboard)

@commands.command(name='fullvert', aliases=('fullvertlb','fullvlb'))
async def _fullvert(ctx, *args):
    user = ctx.message.author
    currChannel = ctx.message.channel
    embedMesg = []
    embed = discord.Embed()
    embed = discord.Embed(color=0xff0000)
    embed.title = f"**{botGlobals.STRAVACLUB_PRETTYNAME} Weekly Vert Leaderboard:**\n"
    embedMesg.append(embed)
    embed = discord.Embed()
    embed = discord.Embed(color=0xff0000)
    leaderboardJSON = await botGlobals.loadLeaderboard()
    if leaderboardJSON is not None:
        leaderboardMsg = ""
        leaderboardJSON['data'].sort(key=lambda x: x['elev_gain'], reverse=True)
        linesPerEmbed = 20
        for i, rankedUser in enumerate(leaderboardJSON['data']):
            boldstr = ""
            if i < 10:
                boldstr = "**"
            athleteId = rankedUser['athlete_id']
            discordId = await userData.retrieveDiscordID(athleteId)
            aUser = None
            if discordId:
                aUser = await ctx.bot.fetch_user(discordId)

            leaderboardMsg +=   boldstr + str(i+1) + '. ' + \
                                rankedUser['athlete_firstname'] + ' ' + \
                                rankedUser['athlete_lastname']
            if aUser:
                leaderboardMsg += ' [' + str(aUser.display_name) + ']'

            leaderboardMsg +=   ' - ' + \
                                "{:,}".format(round(rankedUser['elev_gain'], 2)) + \
                                ' m (' + \
                                metersToFeet(rankedUser['elev_gain']) + \
                                ')' + ' : '
            leaderboardMsg +=   ' - ' + \
                                "{:,}".format(round(rankedUser['distance']/1000, 2)) + \
                                ' km (' + \
                                metersToMiles(rankedUser['distance']) + \
                                ')' + boldstr + '\n'
            if linesPerEmbed <= 0:
                # Store current
                embed.description = leaderboardMsg
                embedMesg.append(embed)

                # Start a new embed message
                embed = discord.Embed()
                embed = discord.Embed(color=0x00ff00)
                linesPerEmbed = 20
                leaderboardMsg = ''
            else:
                linesPerEmbed -= 1

        if leaderboardMsg:
            embed.description = leaderboardMsg
            embedMesg.append(embed)

        for e in embedMesg:
            await currChannel.send(embed=e)
    else:
        await currChannel.send('Failed to load leaderboard. Please try again later.')
commandList.append(_fullvert)


@commands.command(name='leaderboard', aliases=('lb','leader'))
async def _leaderboard(ctx, *args):
    user = ctx.message.author
    currChannel = ctx.message.channel
    await cmdImpl.leaderboardImpl(channel=currChannel, bot=ctx.bot, entries=30)

commandList.append(_leaderboard)

@commands.command()#name='monthleaderboard', aliases=('monthlb', 'month'))
async def _monthleaderboard(ctx, *args):
    user = ctx.message.author
    currChannel = ctx.message.channel
    try:
        access_token = botGlobals.redis_conn.get('token').decode()
        token_expiry = botGlobals.redis_conn.get('expiry').decode()
    except:
        # If we except here, its due to a none byte error against decode
        # TODO there might be a better way to handle this
        access_token, token_expiry  = botGlobals.refresh_token()

    token_expire_time = datetime.utcnow() + timedelta(seconds=int(token_expiry))

    if datetime.utcnow() > token_expire_time:
        access_token, token_expiry  = botGlobals.refresh_token()
    else:
        print("Current token is active")

    stravaAuthHeader = {'Content-Type': 'application/json',
                        'Authorization': 'Bearer {}'.format(access_token)}



    # get first day of current month
    today = datetime.utcnow()
    firstDayCurrentMonth = datetime(today.year, today.month, 1)

    embed = discord.Embed()
    embed = discord.Embed(color=0x00ff00)
    embed.title = f"**{botGlobals.STRAVACLUB_PRETTYNAME} {today.strftime('%B')} Leaderboard:**\n"

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
            result = requests.get('https://www.strava.com/api/v3/clubs/' + botGlobals.STRAVACLUB + '/activities',
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

@commands.command(name='register')
async def _register(ctx, *args):
    # Interact with the user to connect their strava athlete id w/ discord id
    # using the current leaderboard rank
    # !register - sends DM describing command flow and leaderboard in a DM w/ leaderboard first
    # !register <number of leaderboard> - Assigns the current strava athlete at that position to
    #                                     the discord user and prints out confirmation
    # !register erase - Removes the current discord id from any strava id connection
    # !register erase <number of lb> - Admin only command that removes that discord id from that strava athlete id
    user = ctx.message.author
    currChannel = ctx.message.channel
    dmChannel = user.dm_channel
    if dmChannel is None:
        dmChannel = await user.create_dm()

    if (len(args) == 0):
        # Open DM channel and display leaderboard w/ help on !register <rank>


        leaderboard = await cmdImpl.leaderboardImpl(channel=dmChannel, bot=ctx.bot)
        # Display information for the user to execute the command to associate the strava id w/ discord id
        mesg = '\n\n'
        mesg += '```To associate your discord ID with a specific Strava rank in the leaderboard.\n'
        mesg += '!register <rank>\n'
        mesg += 'If you make a mistake, just use !register erase```'
        await dmChannel.send(mesg)

        # Cache the leaderboard for 10 minutes
        #uData = userData.getData(user=ctx.message.author.id)

    elif (len(args) == 1):
        if args[0] == 'erase':

            # Erase my entry in the database for discord id
            deleteWorked = await userData.deleteDiscordID(discordId=ctx.message.author.id)
            mesg = ''
            if deleteWorked is not None:
                mesg = 'Successfully removed registration. Type !register to restart the process if needed.'
            else:
                mesg = 'Registration not found for you.'

            await dmChannel.send(mesg)

        elif args[0].isdigit():
            rankPos = int(args[0])
            # Check the cache to see if its valid

            # Set the strava ID
            stravaId = None
            wrongRank = True
            leaderboardJSON = await botGlobals.loadLeaderboard()
            if leaderboardJSON is not None:
                for rank, rankedUser in enumerate(leaderboardJSON['data']):
                    if rank == (rankPos - 1):
                        # This is our athlete
                        stravaId = rankedUser['athlete_id']
                        wrongRank = False
                        break

                if stravaId is not None:
                    # Delete any potential current registration
                    result = await userData.deleteDiscordID(discordId=ctx.message.author.id)

                    dataSet = await userData.setRegistration(discordId=ctx.message.author.id, stravaId=stravaId)

                    if dataSet:
                        # Display leaderboard for last check
                        await cmdImpl.leaderboardImpl(channel=dmChannel, bot=ctx.bot)
                        # Remove cache and cache expiration
                        mesg = 'Please check above leaderboard to see if its accurate. If not type:\n'
                        mesg += '       !register erase then !register to restart registration process.'
                        await dmChannel.send(mesg)
                    else:
                        await dmChannel.send('Failed to set registration for strava ID: '+str(stravaId))
                else:
                    if wrongRank:
                        await dmChannel.send('The rank you entered does not exist.')
            else:
                # Failed to load leaderboard
                await dmChannel.send('Failed to load leaderboard try again later.')


    elif (len(args) == 2):
        admin = await botGlobals.checkAdmin(ctx=ctx)
        if admin:
            if args[0] == 'erase':
                if args[1].isdigit():
                    deletePos = int(args[1])
                    stravaId = None
                    leaderboardJSON = await botGlobals.loadLeaderboard()
                    if leaderboardJSON is not None:
                        for rank, rankedUser in enumerate(leaderboardJSON['data']):
                            if rank == (deletePos - 1):
                                # This is our athlete
                                stravaId = rankedUser['athlete_id']
                                break
                        if stravaId is not None:
                            discordId = await userData.retrieveDiscordID(stravaId=stravaId)
                            deleteWorked = await userData.deleteDiscordID(discordId=discordId)
                            if deleteWorked:
                                await dmChannel.send('{ADMIN} : Deletion success.')
                    else:
                        await dmChannel.send('Failed to load the leaderboard.')

                pass

commandList.append(_register)

@commands.command()
async def stats(ctx, *args):
    user = ctx.message.author
    currChannel = ctx.message.channel

    access_token = botGlobals.getToken()
    if access_token is not None:
        stravaAuthHeader = {'Content-Type': 'application/json',
                            'Authorization': 'Bearer {}'.format(access_token)}

        embed = discord.Embed()
        embed = discord.Embed(color=0x00ff00)
        embed.title = f"**{botGlobals.STRAVACLUB_PRETTYNAME} Weekly Statistics:**\n"

        stravaResult = requests.get('https://www.strava.com/api/v3/clubs/' +
                                    botGlobals.STRAVACLUB+'/activities',
                                    headers=stravaAuthHeader)
        if stravaResult.status_code == 200:
            totalDistance = 0
            totalElevationGain = 0
            totalMovingTime = 0
            totalActivitiesRecorded = len(stravaResult.json())

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
        else:
            await currChannel.send('Failed to authorize to load activity data.')
    else:
        await currChannel.send('Error with Strava API. Try again later.')

commandList.append(stats)

@commands.command()
async def strava(ctx, *args):
    user = ctx.message.author
    currChannel = ctx.message.channel
    embed = await help.helpMsg()


    await currChannel.send(embed=embed)

commandList.append(strava)

@commands.command(name='vertleaderboard', aliases=('vertlb','vlb'))
async def _vertleaderboard(ctx, *args):
    user = ctx.message.author
    currChannel = ctx.message.channel
    embed = discord.Embed()
    embed = discord.Embed(color=0xff0000)
    embed.title = f"**{botGlobals.STRAVACLUB_PRETTYNAME} Weekly Vert Leaderboard:**\n"
    leaderboardJSON = await botGlobals.loadLeaderboard()
    if leaderboardJSON is not None:
        leaderboardMsg = ""
        leaderboardJSON['data'].sort(key=lambda x: x['elev_gain'], reverse=True)
        for i, rankedUser in enumerate(leaderboardJSON['data']):
            if i < 30:
                boldstr = ""
                if i < 10:
                    boldstr = "**"
                athleteId = rankedUser['athlete_id']
                discordId = await userData.retrieveDiscordID(athleteId)
                aUser = None
                if discordId:
                    aUser = await ctx.bot.fetch_user(discordId)

                leaderboardMsg +=   boldstr + str(i+1) + '. ' + \
                                    rankedUser['athlete_firstname'] + ' ' + \
                                    rankedUser['athlete_lastname']
                if aUser:
                    leaderboardMsg += ' [' + str(aUser.display_name) + ']'

                leaderboardMsg +=   ': ' + \
                                    "{:,}".format(round(rankedUser['elev_gain'], None)) + \
                                    'm (' + \
                                    metersToFeet(rankedUser['elev_gain'], roundTo=None) + \
                                    ')'

                leaderboardMsg +=   ' over ' + \
                                    "{:,}".format(round(rankedUser['distance']/1000, None)) + \
                                    'km (' + \
                                    metersToMiles(meters=rankedUser['distance'], showUnit=False, roundTo=None) + \
                                    'mi)' + boldstr + '\n'



        embed.description = leaderboardMsg

        await currChannel.send(embed=embed)
    else:
        await currChannel.send('Failed to load leaderboard. Please try again later.')
commandList.append(_vertleaderboard)

