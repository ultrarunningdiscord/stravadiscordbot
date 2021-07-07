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
                try:
                    for g in botGlobals.bot.guilds:
                        for r in g.roles:
                            if r.name == botGlobals.distanceMaleRole:
                                maleRole = r
                            if r.name == botGlobals.distanceFemaleRole:
                                femaleRole = r
                    if maleRole is not None:
                        # Remove the distance leader role

                        if currentMale is not None:
                            for m in botGlobals.bot.get_all_members():
                                if m.id == currentMale['male']:
                                    await m.remove_roles(maleRole)
                                    break
                        # Assign the role
                        for m in botGlobals.bot.get_all_members():
                            if m.id == distanceWinnerMale.id:
                                # Assign role and save this

                                await m.add_roles(maleRole)
                                break
                except Exception as e:
                    print(e)

                # if femaleRole is not None:
                #     if currentFemale is not None:
                #         for m in botGlobals.bot.get_all_members():
                #             if m.id == currentFemale['female']:
                #                 await m.remove_roles(femaleRole)
                #                 break

                    # Assign the role
                    # TODO Female distance king
                    # for m in botGlobals.bot.get_all_members():
                    #     if m.id == distanceWinnerMale.id:
                    #         # Assign role and save this
                    #         #await userData.setDistanceLeader(gender='male', id=distanceWinnerMale.id)
                    #         #await m.add_roles(maleRole)
                    #         break






@crownDistanceLeaders.before_loop
async def before_my_task():
    if botGlobals.bot is not None:
        await botGlobals.bot.wait_until_ready()
