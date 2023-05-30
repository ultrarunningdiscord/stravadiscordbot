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
import distanceLeader

# Commands for the bot...just make sure to append to the commandList to register the command
commandList = []

@commands.command()
async def debug(ctx, *args):
    user = ctx.message.author
    currChannel = ctx.message.channel
    admin = await botGlobals.checkAdmin(ctx=ctx)
    if admin:
        dmChannel = user.dm_channel
        if dmChannel is None:
            dmChannel = await user.create_dm()
        embed = discord.Embed()
        embed = discord.Embed(color=0x00ff00)
        embed.title = f"**DEBUG:**\n"
        embed.description = botGlobals.debugInit
        monthCollection = await userData.getDataCollection(botGlobals.monthlyMileageData)
        currentMileage = await userData.getMontlyMileage(monthyear=botGlobals.currentMonthYear)
        await dmChannel.send('Test working...')
        currentTime = datetime.now()
        currentMonth = currentTime.month
        currentMonthYear = currentTime.strftime(botGlobals.monthFormat)

        leaderboardJSON = await botGlobals.loadLastLeaderboard()

        if leaderboardJSON is not None:
            await dmChannel.send('Crown last weeks...')
            # Monthly data is format
            # {"6.2021" : {'stravaId': {meters,
            #             'stravaId2': meters}}
            # dataValues = {}
            # for i, rankedUser in enumerate(leaderboardJSON['data']):
            #     athleteId = rankedUser['athlete_id']
            #     meters = rankedUser['distance']
            #     dataValues[str(athleteId)] = rankedUser['distance']
            #
            # await userData.setMontlyMileage(monthyear=currentMonthYear, data=dataValues)
            await distanceLeader.crownDistanceLeadersImpl(channel=dmChannel)







commandList.append(debug)

@commands.command(name='fulllb', aliases=('fullleaderboard','fullboard'))
async def _fullleaderboard(ctx, *args):
    user = ctx.message.author
    currChannel = ctx.message.channel
    await cmdImpl.leaderboardImpl(channel=currChannel, bot=ctx.bot, registeredOnly=False)

commandList.append(_fullleaderboard)

@commands.command(name='fullvert', aliases=('fullvertlb','fullvlb'))
async def _fullvert(ctx, *args):
    user = ctx.message.author
    currChannel = ctx.message.channel
    await cmdImpl.vertleaderboardImpl(channel=currChannel, bot=ctx.bot)
commandList.append(_fullvert)

@commands.command(name='distanceleader', aliases=('dlb','dleader'))
async def _distanceLeader(ctx, *args):
    # Update the Mongo DB data for avatar_url and display_name
    # ADMIN ONLY
    user = ctx.message.author
    dmChannel = user.dm_channel
    if dmChannel is None:
        dmChannel = await user.create_dm()


    admin = await botGlobals.checkAdmin(ctx=ctx)
    if admin:
        try:
            await dmChannel.send('Starting assignment...')
            leaderboardJSON = await botGlobals.loadLastLeaderboard()

            if leaderboardJSON is not None:

                distanceWinnerMale = None
                distanceWinnerFemale = None
                for i, rankedUser in enumerate(leaderboardJSON['data']):
                    athleteId = rankedUser['athlete_id']
                    meters = rankedUser['distance']
                    aUser = await userData.retrieveNickname(athleteId)
                    if aUser is not None:
                        # Retrieve the gender
                        gender = await userData.retrieveGender(athleteId)
                        if gender == 'male':
                            if distanceWinnerMale is None:
                                distanceWinnerMale = await userData.retrieveDiscordID(athleteId)
                        elif gender == 'female':
                            if distanceWinnerFemale is None:
                                distanceWinnerFemale = await userData.retrieveDiscordID(athleteId)


                currentMale, currentFemale = await userData.getDistanceLeader()
                maleWinner = None
                femaleWinner = None
                if distanceWinnerMale is not None:



                    # Put into database
                    await userData.setDistanceLeader(gender='male', id=distanceWinnerMale)
                    maleWinner = await cmdImpl.assignLeader(role=botGlobals.distanceMaleRole, id=distanceWinnerMale,
                                                            currentLeader=currentMale['male'])
                if distanceWinnerFemale is not None:


                    # Put into database
                    await userData.setDistanceLeader(gender='female', id=distanceWinnerFemale)
                    femaleWinner = await cmdImpl.assignLeader(role=botGlobals.distanceFemaleRole, id=distanceWinnerFemale,
                                                              currentLeader=currentFemale['female'])

                announceChannel = None
                for c in botGlobals.bot.get_all_channels():
                    if c.name == botGlobals.announceChannel:
                        announceChannel = c
                await dmChannel.send('Announce channel '+str(announceChannel))
                if announceChannel is not None:
                    doAnnounce = False
                    mesg = 'Last week leaderboard results:\n'

                    if maleWinner is not None:
                        doAnnounce = True
                        mesg += maleWinner.mention + ': Distance King.\n'
                    if femaleWinner is not None:
                        doAnnounce = True
                        mesg += femaleWinner.mention + ': Distance Queen.\n'

                    if doAnnounce:
                        try:
                            await cmdImpl.leaderboardImpl(channel=announceChannel, bot=botGlobals.bot,registeredOnly=True,
                                                  entries=None, leaderboardJSON=leaderboardJSON)
                        except Exception as e:
                            print(e)


                        await announceChannel.send(mesg)

        except Exception as e:
            await dmChannel.send(e)

    else:
        dmChannel.send('!distanceleader is an admin only command.')

    pass
commandList.append(_distanceLeader)

@commands.command(name='lastmonth', aliases=('last', 'lmonth'))
async def _lastmonth(ctx, *args):
    user = ctx.message.author
    currChannel = ctx.message.channel



    # Monthly data is format
    # {"6_2021" : {'stravaId': meters,
    #             'stravaId2': meters}}
    dataValues = {}


    currentTime = datetime.now()
    currentMonth = currentTime.month
    lastMonth = currentTime.replace(month=currentMonth-1).strftime(botGlobals.monthFormat)
    #lastMonth = botGlobals.currentMonthYear-1
    currentMileage = await userData.getMontlyMileage(monthyear=lastMonth)

    # Add the mileage together
    metersPerAthlete = currentMileage[lastMonth]
    for strava,m in metersPerAthlete.items():

        dataValues[strava] = m



    # Display the new information
    dataValues = dict(sorted(dataValues.items(), key=lambda x: x[1], reverse=True))
    linesPerEmbed = 20
    embedMesg = []
    embed = discord.Embed()
    embed = discord.Embed(color=0x0000ff)
    embed.title = f"**{botGlobals.STRAVACLUB_PRETTYNAME} {lastMonth} Monthly Distance Leaderboard:**\n"

    embedMesg.append(embed)
    embed = discord.Embed()
    embed = discord.Embed(color=0x0000ff)
    i = 0
    leaderboardMsg = ""
    for strava,m in dataValues.items():
        # Don't display until the athlete overcame the left-over mileage at the beginning of month
        if m <= 0:
            continue

        boldstr = ""
        if i < 10:
            boldstr = "**"

        aUser = await userData.retrieveNickname(int(strava))



        if aUser is not None:
            leaderboardMsg += boldstr + str(i+1) + '. '
            leaderboardMsg += aUser


            leaderboardMsg +=   ' - ' + \
                                "{:,}".format(round(m/1000, 2)) + \
                                ' km (' + \
                                metersToMiles(m) + \
                                ')' + boldstr + '\n'
            # Printing everything so use lines per embed
            if linesPerEmbed <= 0:
                # Store current
                embed.description = leaderboardMsg
                embedMesg.append(embed)

                # Start a new embed message
                embed = discord.Embed()
                embed = discord.Embed(color=0x0000ff)
                linesPerEmbed = 20
                leaderboardMsg = ''
            else:
                linesPerEmbed -= 1
            i += 1


    if leaderboardMsg:
        embed.description = leaderboardMsg
        embedMesg.append(embed)
    # Add info text at hte bottom
    embed = discord.Embed()
    embed = discord.Embed(color=0x0000ff)
    infoMesg = 'Shows and tracks registered users only. Type !register for details on how to register.'
    embed.description = infoMesg
    embedMesg.append(embed)
    for e in embedMesg:
        await currChannel.send(embed=e)
commandList.append(_lastmonth)

@commands.command(name='leaderboard', aliases=('lb','leader'))
async def _leaderboard(ctx, *args):
    user = ctx.message.author
    currChannel = ctx.message.channel
    await cmdImpl.leaderboardImpl(channel=currChannel, bot=ctx.bot, entries=30)

commandList.append(_leaderboard)

@commands.command(name='monthleaderboard', aliases=('monthlb', 'month'))
async def _monthleaderboard(ctx, *args):
    user = ctx.message.author
    currChannel = ctx.message.channel


    # Load the current leaderboard and add up everything then sort
    leaderboardJSON = await botGlobals.loadLeaderboard()
    if leaderboardJSON is not None:
        # Monthly data is format
        # {"6_2021" : {'stravaId': meters,
        #             'stravaId2': meters}}
        dataValues = {}
        for i, rankedUser in enumerate(leaderboardJSON['data']):
            athleteId = rankedUser['athlete_id']
            meters = rankedUser['distance']
            aUser = await userData.retrieveNickname(athleteId)
            if aUser is not None:
                dataValues[str(athleteId)] = rankedUser['distance']



        currentMileage = await userData.getMontlyMileage(monthyear=botGlobals.currentMonthYear)

        # Add the mileage together
        metersPerAthlete = currentMileage[botGlobals.currentMonthYear]
        for strava,m in metersPerAthlete.items():
            if strava in dataValues:
                dataValues[strava] = dataValues[strava] + m
            else:
                # This athelete wasn't found in the current leaderboard add their data
                dataValues[strava] = m



        # Display the new information
        dataValues = dict(sorted(dataValues.items(), key=lambda x: x[1], reverse=True))
        linesPerEmbed = 20
        embedMesg = []
        embed = discord.Embed()
        embed = discord.Embed(color=0x0000ff)
        embed.title = f"**{botGlobals.STRAVACLUB_PRETTYNAME} {botGlobals.currentMonthYear} Monthly Distance Leaderboard:**\n"

        embedMesg.append(embed)
        embed = discord.Embed()
        embed = discord.Embed(color=0x0000ff)
        i = 0
        leaderboardMsg = ""
        for strava,m in dataValues.items():
            # Don't display until the athlete overcame the left-over mileage at the beginning of month
            if m <= 0:
                continue

            boldstr = ""
            if i < 10:
                boldstr = "**"

            aUser = await userData.retrieveNickname(int(strava))



            if aUser is not None:
                leaderboardMsg += boldstr + str(i+1) + '. '
                leaderboardMsg += aUser


                leaderboardMsg +=   ' - ' + \
                                    "{:,}".format(round(m/1000, 2)) + \
                                    ' km (' + \
                                    metersToMiles(m) + \
                                    ')' + boldstr + '\n'
                # Printing everything so use lines per embed
                if linesPerEmbed <= 0:
                    # Store current
                    embed.description = leaderboardMsg
                    embedMesg.append(embed)

                    # Start a new embed message
                    embed = discord.Embed()
                    embed = discord.Embed(color=0x0000ff)
                    linesPerEmbed = 20
                    leaderboardMsg = ''
                else:
                    linesPerEmbed -= 1
                i += 1


        if leaderboardMsg:
            embed.description = leaderboardMsg
            embedMesg.append(embed)
        # Add info text at hte bottom
        embed = discord.Embed()
        embed = discord.Embed(color=0x0000ff)
        infoMesg = 'Shows and tracks registered users only. Type !register for details on how to register.'
        embed.description = infoMesg
        embedMesg.append(embed)
        for e in embedMesg:
            await currChannel.send(embed=e)

commandList.append(_monthleaderboard)

@commands.command(name='register')
async def _register(ctx, *args):
    # Interact with the user to connect their strava athlete id w/ discord id
    # using the current leaderboard rank
    # !register - sends DM describing command flow and leaderboard in a DM w/ leaderboard first
    # !register <number of leaderboard> <gender> - Assigns the current strava athlete at that position to
    #                                     the discord user and prints out confirmation
    # !register erase - Removes the current discord id from any strava id connection
    # !register erase <number of lb> - Admin only command that removes that discord id from that strava athlete id
    user = ctx.message.author
    currChannel = ctx.message.channel
    dmChannel = user.dm_channel
    if dmChannel is None:
        dmChannel = await user.create_dm()
        # Test to see if the channel was created
        try:
            await dmChannel.send('Starting the registration process..')
        except Exception as e:
            print(e)
            # Tell the user to turn on direct messages
            mesg = user.mention + ' please turn on direct messages to start the registration process.'
            await currChannel.send(mesg)

    if (len(args) == 0):
        # Open DM channel and display leaderboard w/ help on !register <rank>
        await cmdImpl.registerCacheImpl(channel=dmChannel, bot=ctx.bot, discordId=ctx.message.author.id)

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
            checkCache = await userData.checkLeaderBoardCache(discordId=ctx.message.author.id)
            if checkCache is not None:
                # Set the strava ID
                stravaId = None
                wrongRank = True
                # Use the cached leaderboard
                leaderboardJSON = checkCache
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
                        nickName = None
                        for m in botGlobals.bot.get_all_members():
                            if m.id == ctx.message.author.id:
                                nickName = m.nick
                                break
                        dataSet = await userData.setRegistration(discordId=ctx.message.author.id, stravaId=stravaId,
                                                                 displayName=ctx.message.author.display_name,
                                                                 #avatarURL=ctx.message.author.avatar_url,
                                                                 nickname=nickName)

                        if dataSet:
                            # Display leaderboard for last check
                            await cmdImpl.leaderboardImpl(channel=dmChannel, bot=ctx.bot, registeredOnly=False)
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
                    print('# ALS - failed to load')
                    await dmChannel.send('Failed to load leaderboard try again later.')
            else:
                # Cache is invalid display leaderboard and re-cache
                await cmdImpl.registerCacheImpl(channel=dmChannel, bot=ctx.bot, discordId=ctx.message.author.id)
                await dmChannel.send('```Please try again as the leaderboard may have changed and type !register <rank>.```')

    elif (len(args) == 2):

        admin = await botGlobals.checkAdmin(ctx=ctx)
        if args[0] == 'erase':
            if admin:
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
                        print('# ALS - failed to load(3)')
                        await dmChannel.send('Failed to load the leaderboard.')

                pass
        elif args[0].isdigit():
            rankPos = int(args[0])
            gender = 'male'
            if args[1] == 'female' or args[1] == 'f':
                gender = 'female'
            # Check the cache to see if its valid
            checkCache = await userData.checkLeaderBoardCache(discordId=ctx.message.author.id)
            if checkCache is not None:
                # Set the strava ID
                stravaId = None
                wrongRank = True
                # Use the cached leaderboard
                leaderboardJSON = checkCache
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
                        nickName = None
                        for m in botGlobals.bot.get_all_members():
                            if m.id == ctx.message.author.id:
                                nickName = m.nick
                                break
                        dataSet = await userData.setRegistration(discordId=ctx.message.author.id, stravaId=stravaId,
                                                                 displayName=ctx.message.author.display_name,
                                                                 #avatarURL=ctx.message.author.avatar_url,
                                                                 nickname=nickName, gender=gender)

                        if dataSet:
                            # Display leaderboard for last check
                            await cmdImpl.leaderboardImpl(channel=dmChannel, bot=ctx.bot, registeredOnly=False)
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
                    print('# ALS - failed to load')
                    await dmChannel.send('Failed to load leaderboard try again later.')
            else:
                # Cache is invalid display leaderboard and re-cache
                await cmdImpl.registerCacheImpl(channel=dmChannel, bot=ctx.bot, discordId=ctx.message.author.id)
                await dmChannel.send('```Please try again as the leaderboard may have changed and type !register <rank>.```')

    # Clear our local registration cache
    botGlobals.registrationCache = None

commandList.append(_register)

@commands.command()
async def shutdown(ctx, *args):
    admin = await botGlobals.checkAdmin(ctx=ctx)
    if admin:
        await ctx.bot.close()

commandList.append(shutdown)

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

@commands.command(name='time', aliases=('timelb','tlb'))
async def _time(ctx, *args):
    user = ctx.message.author
    currChannel = ctx.message.channel
    await cmdImpl.timeleaderboardImpl(channel=currChannel, bot=ctx.bot)

commandList.append(_time)

@commands.command()
async def update(ctx, *args):
    # Update the Mongo DB data for avatar_url and display_name
    # ADMIN ONLY
    user = ctx.message.author
    dmChannel = user.dm_channel
    if dmChannel is None:
        dmChannel = await user.create_dm()


    admin = await botGlobals.checkAdmin(ctx=ctx)
    if admin:
        failed = await cmdImpl.updateImpl(bot=botGlobals.bot)#await cmdImpl.updateImpl(ctx.bot)
        if failed:
            # Failure
            await dmChannel.send('During the update command there was a failure')
    else:
        dmChannel.send('!update is an admin only command.')

    pass
commandList.append(update)

@commands.command(name='vertleaderboard', aliases=('vertlb','vlb'))
async def _vertleaderboard(ctx, *args):
    user = ctx.message.author
    currChannel = ctx.message.channel
    await cmdImpl.vertleaderboardImpl(channel=currChannel, bot=ctx.bot, entries=30)

commandList.append(_vertleaderboard)
