from discord.ext import commands, tasks
from datetime import datetime, timedelta

import botGlobals
import cmdImpl
import userData

@tasks.loop(minutes=60)
async def crownDistanceLeaders():
    if datetime.now().hour == botGlobals.resolveTime and datetime.now().weekday() == botGlobals.resolveDay:
        leaderboardJSON = await botGlobals.loadLastLeaderboard()

        if leaderboardJSON is not None:

            distanceWinnerMale = None
            for i, rankedUser in enumerate(leaderboardJSON['data']):
                athleteId = rankedUser['athlete_id']
                meters = rankedUser['distance']
                aUser = await userData.retrieveNickname(athleteId)
                if aUser is not None:
                    distanceWinnerMale = await userData.retrieveDiscordID(athleteId)
                    break


            if distanceWinnerMale is not None:
                currentMale, currentFemale = await userData.getDistanceLeader()
                maleRole = None
                femaleRole = None
                # Put into database
                await userData.setDistanceLeader(gender='male', id=distanceWinnerMale)
                await cmdImpl.assignLeader(role=botGlobals.distanceMaleRole, id=distanceWinnerMale,
                                           currentLeader=currentMale)









@crownDistanceLeaders.before_loop
async def before_my_task():
    if botGlobals.bot is not None:
        await botGlobals.bot.wait_until_ready()
