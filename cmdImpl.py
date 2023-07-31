import datetime

import discord

from conversions import metersToMiles, metersToFeet
import botGlobals
import userData

# Helper implementations for various bot commands to facilitate simple re-use and maintenance
async def leaderboardImpl(channel, bot, registeredOnly=True, entries=None, leaderboardJSON=None):
    linesPerEmbed = 20

    embedMesg = []
    embed = discord.Embed()
    embed = discord.Embed(color=0x0000ff)
    embed.title = f"**{botGlobals.STRAVACLUB_PRETTYNAME} Weekly Distance Leaderboard:**\n"
    if entries is None:
        embedMesg.append(embed)
        embed = discord.Embed()
        embed = discord.Embed(color=0x0000ff)
    if leaderboardJSON is None:
        leaderboardJSON = await botGlobals.loadLeaderboard()

    if leaderboardJSON is not None:
        leaderboardMsg = ""
        currentLeaderboard = []
        for rankedUser in leaderboardJSON['data']:
            athleteId = rankedUser['athlete_id']
            if registeredOnly:

                aUser = await userData.retrieveNickname(athleteId)
                if aUser is not None:
                    currentLeaderboard.append(rankedUser)
            else:
                currentLeaderboard.append(rankedUser)

        for i, rankedUser in enumerate(currentLeaderboard):
            if entries is not None:
                if i >= entries:
                    break

            boldstr = ""
            if i < 10:
                boldstr = "**"
            athleteId = rankedUser['athlete_id']

            aUser = await userData.retrieveNickname(athleteId)


            #leaderboardMsg +=   boldstr + str(rankedUser['rank']) + '. '
            leaderboardMsg += boldstr + str(i+1) + '. '

            if aUser is not None:
                leaderboardMsg += aUser
            else:
                leaderboardMsg += rankedUser['athlete_firstname'] + ' ' + \
                                  rankedUser['athlete_lastname']

            leaderboardMsg +=   ' - ' + \
                                "{:,}".format(round(rankedUser['distance']/1000, 2)) + \
                                ' km (' + \
                                metersToMiles(rankedUser['distance']) + \
                                ')' + boldstr + '\n'

            if entries is None:
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

        if leaderboardMsg:
            embed.description = leaderboardMsg
            embedMesg.append(embed)

        # Add info text at hte bottom
        embed = discord.Embed()
        embed = discord.Embed(color=0x0000ff)
        infoMesg = 'Missing your discord name? Type !register for details on how to register.'
        embed.description = infoMesg
        embedMesg.append(embed)

        if channel is not None:
            for e in embedMesg:
                await channel.send(embed=e)
    else:
        if channel is not None:
            print('# ALS - failed to load')
            await channel.send('Failed to load leaderboard. Please try again later.')

    return leaderboardJSON

async def registerCacheImpl(channel, bot, discordId):
    leaderboard = await leaderboardImpl(channel=channel, bot=bot, registeredOnly=False)
    # Display information for the user to execute the command to associate the strava id w/ discord id
    mesg = '\n\n'
    mesg += '```Find your Strava name and mileage on the leaderboard, then type !register [number] [m or f].\n'
    mesg += 'If its not there, try again a few days after joining the strava group and logging a run.\n'
    mesg += '!register <rank> <gender(m or f)>\n'
    mesg += 'If you make a mistake, just use !register erase```'
    await channel.send(mesg)

    # Cache the leaderboard for 10 minutes
    leaderboardJSON = await botGlobals.loadLeaderboard()
    # Reset the cache
    reset = await userData.resetLeaderBoardCache(lbJson=leaderboardJSON, discordId=discordId)
    if not reset:
        await channel.send('Failed to cache the leaderboard.')

async def updateImpl(bot):
    failed = False
    # Clear our registration cache
    botGlobals.registrationCache = None
    # Update the registration database with additional DISCORD info
    rData = await userData.getDataCollection(botGlobals.registrationData)
    if rData is not None:
        cursor = rData.find()
        updateData = []
        r = await cursor.to_list(length=1)
        while r:
            r = r[0]
            nickName = None
            for m in bot.get_all_members():
                if m.id == r['id']:
                    nickName = m.nick
                    break

            gender = 'male'
            if "gender" in r:
                gender = r['gender']

            d = {'id':r['id'], 'stravaId':r['stravaId'], 'display_name':r['display_name'],
                 #'avatar_url':r['avatar_url'], 'gender':gender}
                'gender':gender}

            if nickName is not None:
                d = {'id':r['id'], 'stravaId':r['stravaId'], 'display_name':r['display_name'],
                     #'avatar_url':r['avatar_url'], 'gender':gender, 'nick':nickName}
                     'gender':gender, 'nick':nickName}
            updateData.append(d)

            r = await cursor.to_list(length=1)

        # Delete everything
        result = await rData.delete_many({'id': {"$exists": True}})
        for d in updateData:
            dataset = await userData.setData(collectionName=botGlobals.registrationData,
                                             data=d)

    else:
        failed = True

    return failed

async def timeleaderboardImpl(channel, bot):

    embedMesg = []
    embed = discord.Embed()
    embed = discord.Embed(color=0x800080)
    embed.title = f"**{botGlobals.STRAVACLUB_PRETTYNAME} Weekly Time Leaderboard:**\n"

    leaderboardJSON = await botGlobals.loadLeaderboard()

    if leaderboardJSON is not None:
        leaderboardMsg = ""
        leaderboardJSON['data'].sort(key=lambda x: x['moving_time'], reverse=True)
        i = 0
        for j, rankedUser in enumerate(leaderboardJSON['data']):
            if i >= 30:
                break

            boldstr = ""
            if i < 10:
                boldstr = "**"
            athleteId = rankedUser['athlete_id']
            aUser = await userData.retrieveNickname(athleteId)
            if aUser is not None:


                leaderboardMsg +=   boldstr + str(i+1) + '. '


                leaderboardMsg += aUser

                movingTime = datetime.timedelta(seconds=rankedUser['moving_time']) # in seconds

                leaderboardMsg +=   ': ' + \
                                    str(movingTime) + ' time '

                leaderboardMsg +=   ' over ' + \
                                    "{:,}".format(round(rankedUser['distance']/1000, None)) + \
                                    'km (' + \
                                    metersToMiles(meters=rankedUser['distance'], showUnit=False, roundTo=None) + \
                                    'mi)' + boldstr + '\n'
                i += 1



        if leaderboardMsg:
            embed.description = leaderboardMsg
            embedMesg.append(embed)
        if channel is not None:
            embed = discord.Embed()
            embed = discord.Embed(color=0x800080)
            infoMesg = 'Shows and tracks registered users only. Type !register for details on how to register.'
            embed.description = infoMesg
            embedMesg.append(embed)
            for e in embedMesg:
                await channel.send(embed=e)

    return leaderboardJSON

async def vertleaderboardImpl(channel, bot, entries=None):
    linesPerEmbed = 20

    embedMesg = []
    embed = discord.Embed()
    embed = discord.Embed(color=0xff0000)
    embed.title = f"**{botGlobals.STRAVACLUB_PRETTYNAME} Weekly Vert Leaderboard:**\n"
    if entries is None:
        embedMesg.append(embed)
        embed = discord.Embed()
        embed = discord.Embed(color=0x0000ff)
    leaderboardJSON = await botGlobals.loadLeaderboard()

    if leaderboardJSON is not None:
        leaderboardMsg = ""
        leaderboardJSON['data'].sort(key=lambda x: x['elev_gain'], reverse=True)
        for i, rankedUser in enumerate(leaderboardJSON['data']):
            if entries is not None:
                if i >= entries:
                    break

            boldstr = ""
            if i < 10:
                boldstr = "**"
            athleteId = rankedUser['athlete_id']

            aUser = await userData.retrieveNickname(athleteId)


            leaderboardMsg +=   boldstr + str(i+1) + '. '

            if aUser:
                leaderboardMsg += aUser
            else:
                leaderboardMsg += rankedUser['athlete_firstname'] + ' ' + \
                                  rankedUser['athlete_lastname']

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

            if entries is None:
                # Printing everything so use lines per embed
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
        if channel is not None:
            for e in embedMesg:
                await channel.send(embed=e)
    else:
        if channel is not None:
            await channel.send('Failed to load vertical leaderboard. Please try again later.')

    return leaderboardJSON

async def assignLeader(role, id, currentLeader, channel=None):
    distanceRole = None
    for g in botGlobals.bot.guilds:
        for r in g.roles:
            if channel is not None:
                await channel.send('Roles : ' + str(r))
            if r.name == role:
                distanceRole = r
                break
    aUser = await userData.retrieveNick(currentLeader)
    if channel is not None:
        await channel.send('Found distance role ' + str(distanceRole) + ' current leader ' + str(currentLeader) +
                           ' nick ' + str(aUser))
    winner = None
    if distanceRole is not None:
        # Remove the distance leader role
        if currentLeader is not None:
            for m in botGlobals.bot.get_all_members():
                if m.id == currentLeader:
                    try:
                        await m.remove_roles(distanceRole)
                        break
                    except:
                        print('# Failed removal role exception')
                        break

        if channel is not None:
            await channel.send('Removed role successful')

        # Assign the role
        for m in botGlobals.bot.get_all_members():
            if m.id == id:
                print('# Assign role...')
                # Assign role and save this
                try:
                    await m.add_roles(distanceRole)
                    winner = m
                except:
                    print('# Failed to assign role')
                break

    return winner