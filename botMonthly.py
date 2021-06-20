from discord.ext import commands, tasks
from datetime import datetime, timedelta

import botGlobals
from conversions import metersToMiles

import userData
# Update everyone's miles each Sunday night similar to the Strava website

checkedInit = False

@tasks.loop(minutes=60)
async def updateMonthlyData():
    global checkedInit
    # Check to see if we have started/initialized the collection for monthly mileage tracking
    # First time we'll load up last week's leaderboard and not confuse with this being a start of a month
    # or not once we start recording monthly mileage this will never happen unless we reset everything
    currentTime = datetime.now()
    month = currentTime.month
    monthYear = currentTime.strftime(botGlobals.monthFormat)
    if not checkedInit:
        checkedInit = True
        monthCollection = await userData.getDataCollection(botGlobals.monthlyMileageData)
        if monthCollection is None:
            leaderboardJSON = await botGlobals.loadLastLeaderboard()
    
            if leaderboardJSON is not None:
                # Monthly data is format
                # {"6.2021" : {'stravaId': {meters,
                #             'stravaId2': meters}}
                dataValues = {}
                for i, rankedUser in enumerate(leaderboardJSON['data']):
                    athleteId = rankedUser['athlete_id']
                    meters = rankedUser['distance']
                    dataValues[str(athleteId)] = rankedUser['distance']

                await userData.setMontlyMileage(monthyear=monthYear, data=dataValues)
                    


    # Run each day at 1am to check if we are at the start of the new month
    # on Mondays at 1am update monthly data from last weeks leaderboard
    if currentTime.hour == 1:
        if currentTime.weekday() == 0: # Monday
            print('# ALS - *** UPDATING MILEAGE from last week***')
            leaderboardJSON = await botGlobals.loadLastLeaderboard()

            if leaderboardJSON is not None:
                # Monthly data is format
                # {"6.2021" : {'stravaId': meters,
                #             'stravaId2': meters}}
                dataValues = {}
                for i, rankedUser in enumerate(leaderboardJSON['data']):
                    athleteId = rankedUser['athlete_id']
                    meters = rankedUser['distance']
                    dataValues[str(athleteId)] = rankedUser['distance']

                # Add last weeks to this weeks
                currentMileage = await userData.getMontlyMileage(monthyear=monthYear)

                # Add the mileage together
                metersPerAthlete = currentMileage[monthYear]
                for strava,m in metersPerAthlete.items():
                    if strava in dataValues:
                        # Update their total mileage
                        dataValues[strava] = dataValues[strava] + m
                    else:
                        # New person add to the month
                        dataValues[strava] = m


                await userData.setMontlyMileage(monthyear=monthYear, data=dataValues)

        # Now check to see if we rolled into a new month everyday
        if month != botGlobals.currentMonth:
            # New month so build new collection and rev the month
            botGlobals.currentMonth = month




@updateMonthlyData.before_loop
async def before_my_task():

    if botGlobals.bot is not None:
        await botGlobals.bot.wait_until_ready()
