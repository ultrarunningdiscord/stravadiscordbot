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
    currentMonth = currentTime.month
    currentMonthYear = currentTime.strftime(botGlobals.monthFormat)
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

                await userData.setMontlyMileage(monthyear=currentMonthYear, data=dataValues)
                    


    # Run each day at 1am to check if we are at the start of the new month
    # on Mondays at 1am update monthly data from last weeks leaderboard
    if currentTime.hour == 1:
        if currentTime.weekday() == 0: # Monday
            print('# ALS - *** UPDATING MILEAGE from last week***')
            leaderboardJSON = await botGlobals.loadLastLeaderboard()

            if leaderboardJSON is not None:
                # Monthly data is format
                # {"6_2021" : {'stravaId': meters,
                #             'stravaId2': meters}}
                dataValues = {}
                for i, rankedUser in enumerate(leaderboardJSON['data']):
                    athleteId = rankedUser['athlete_id']
                    meters = rankedUser['distance']
                    dataValues[str(athleteId)] = rankedUser['distance']

                # Add last weeks to this weeks
                # Use the global saved month as this could be day #1 of a new month
                currentMileage = await userData.getMontlyMileage(monthyear=botGlobals.currentMonthYear)

                # Add the mileage together
                metersPerAthlete = currentMileage[botGlobals.currentMonthYear]
                for strava,m in metersPerAthlete.items():
                    if strava in dataValues:
                        # Update their total mileage
                        dataValues[strava] = dataValues[strava] + m
                    else:
                        # New person add to the month
                        dataValues[strava] = m


                await userData.setMontlyMileage(monthyear=botGlobals.currentMonthYear, data=dataValues)

        # Now check to see if we rolled into a new month everyday
        if currentMonth != botGlobals.currentMonth:

            # If start of new month is Monday the above Monday update has occurred
            # so last week data is already added. Get the current leaderboard and
            # add it to the database
            lastMonthDistance = {}
            leaderboardJSON = await botGlobals.loadLeaderboard()
            if leaderboardJSON is not None:
                # Monthly data is format
                # {"6_2021" : {'stravaId': meters,
                #             'stravaId2': meters}}
                dataValues = {}
                for i, rankedUser in enumerate(leaderboardJSON['data']):
                    athleteId = rankedUser['athlete_id']
                    meters = rankedUser['distance']
                    dataValues[str(athleteId)] = rankedUser['distance']
                    # Save this remnant as we need to use this as NEGATIVE for the current month
                    lastMonthDistance[str(athleteId)] = -1 * rankedUser['distance']

                # Add last weeks to this weeks
                # Use the global saved month as this could be day #1 of a new month
                currentMileage = await userData.getMontlyMileage(monthyear=botGlobals.currentMonthYear)

                # Add the mileage together
                metersPerAthlete = currentMileage[botGlobals.currentMonthYear]
                for strava,m in metersPerAthlete.items():
                    if strava in dataValues:
                        # Update their total mileage
                        dataValues[strava] = dataValues[strava] + m
                    else:
                        # New person add to the month
                        dataValues[strava] = m


                await userData.setMontlyMileage(monthyear=botGlobals.currentMonthYear, data=dataValues)



            # New month so build new collection and rev the month
            botGlobals.currentMonth = currentMonth
            botGlobals.currentMonthYear = currentMonthYear

            await userData.setMontlyMileage(monthyear=botGlobals.currentMonthYear, data=lastMonthDistance)






@updateMonthlyData.before_loop
async def before_my_task():

    if botGlobals.bot is not None:
        await botGlobals.bot.wait_until_ready()
