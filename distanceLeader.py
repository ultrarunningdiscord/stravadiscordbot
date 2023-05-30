from discord.ext import commands, tasks
from datetime import datetime, timedelta

import botGlobals
import cmdImpl
import userData

async def crownDistanceLeadersImpl(channel=None):
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
            try:
                await userData.setDistanceLeader(gender='male', id=distanceWinnerMale)
                maleWinner = await cmdImpl.assignLeader(role=botGlobals.distanceMaleRole, id=distanceWinnerMale,
                                                        currentLeader=currentMale['male'], channel=channel)
            except:
                print("Failed to crown male distance leader")


        if distanceWinnerFemale is not None:


            # Put into database
            await userData.setDistanceLeader(gender='female', id=distanceWinnerFemale)
            femaleWinner = await cmdImpl.assignLeader(role=botGlobals.distanceFemaleRole, id=distanceWinnerFemale,
                                                      currentLeader=currentFemale['female'])

        announceChannel = None
        for c in botGlobals.bot.get_all_channels():
            if c.name == botGlobals.announceChannel:
                announceChannel = c

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

@tasks.loop(minutes=60)
async def crownDistanceLeaders():
    if datetime.now().hour == botGlobals.resolveTime and datetime.now().weekday() == botGlobals.resolveDay:
        crownDistanceLeadersImpl()


@crownDistanceLeaders.before_loop
async def before_my_task():
    if botGlobals.bot is not None:
        await botGlobals.bot.wait_until_ready()
