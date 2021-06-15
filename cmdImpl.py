import discord

from conversions import metersToMiles
import botGlobals
import userData

# Helper implementations for various bot commands to facilitate simple re-use and maintenance
async def leaderboardImpl(channel, bot, entries=None):
    linesPerEmbed = 20

    embedMesg = []
    embed = discord.Embed()
    embed = discord.Embed(color=0x0000ff)
    embed.title = f"**{botGlobals.STRAVACLUB_PRETTYNAME} Weekly Distance Leaderboard:**\n"
    if entries is None:
        embedMesg.append(embed)
        embed = discord.Embed()
        embed = discord.Embed(color=0x0000ff)
    leaderboardJSON = await botGlobals.loadLeaderboard()

    if leaderboardJSON is not None:
        leaderboardMsg = ""
        for i, rankedUser in enumerate(leaderboardJSON['data']):
            if entries is not None:
                if i >= entries:
                    break

            boldstr = ""
            if i < 10:
                boldstr = "**"
            athleteId = rankedUser['athlete_id']
            discordId = await userData.retrieveDiscordID(athleteId)
            aUser = None
            if discordId and bot is not None:
                aUser = await bot.fetch_user(discordId)

            leaderboardMsg +=   boldstr + str(rankedUser['rank']) + '. '

            if aUser:
                leaderboardMsg += str(aUser.display_name)
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
            await channel.send('Failed to load leaderboard. Please try again later.')

    return leaderboardJSON