from datetime import datetime, date, timedelta
import json
import motor.motor_tornado
import os
import pickle
import redis
import requests
import sys
import time

from conversions import metersToMiles
import userData

# Global data for environment, tokens, other global information the bot needs as well as global functions
admin = [302457136959586304, 267777327885320193, 498195545228312578]
announceChannel = 'announcements'
bot = None
botToken = None
cacheTimeout = 3600
cacheData = 'userCache'
currentMonth = None
currentMonthYear = None
debug = False
debugInit = ''
distanceLeader = 'distanceLeaders' # Mongo DB collection name
distanceMaleRole = 'distance king'
distanceFemaleRole = 'distance queen'
leaderThread = None
mongoClient = None
mongoDb = None
MONGO_DB_NAME = None
MONGO_USER = None
MONGO_PASSWD = None
monthlyMileageData = 'monthlyMileage'
monthFormat = '%m_%Y'
running = True
registrationCache = None
registrationData = 'registrations'
resolveTime = 2
resolveDay = 0 # Monday for datetime object
STRAVACLUB = ''
STRAVACLUB_PRETTYNAME = ''
STRAVAREFRESHTOKEN = ''
STRAVATOKEN = ''
STRAVACLIENTID = ''
STRAVASECRET = ''
session = None
stravaToken = None
stravaTokenExpire = None
stravaPublicHeader = None
updateDBTime = 23
userDataFile = 'stravaBot_userData'

def init(stravaBot):
    global bot
    bot = stravaBot

    global currentMonth, currentMonthYear, monthFormat
    currentMonth = datetime.now().month # Initialize
    currentMonthYear = datetime.now().strftime(monthFormat)

    # Grab the Strava Club ID from STRAVACLUB environment variable
    global STRAVACLUB
    STRAVACLUB = os.environ.get('STRAVACLUB')
    if STRAVACLUB is None:
        print("STRAVACLUB variable not set. Unable to launch bot.")


    # Grab the Strava Club ID from STRAVACLUB_PRETTYNAME environment variable
    global STRAVACLUB_PRETTYNAME
    STRAVACLUB_PRETTYNAME = os.environ.get('STRAVACLUB_PRETTYNAME')
    if STRAVACLUB_PRETTYNAME is None:
        print("STRAVACLUB_PRETTYNAME variable not set. Unable to launch bot.")
        sys.exit()
    else:
        pass

    # Grab the Strava auth token from STRAVATOKEN environment variable
    # This is used for Bearer authentication against Strava's API
    global STRAVAREFRESHTOKEN
    STRAVAREFRESHTOKEN = os.environ.get('STRAVAREFRESHTOKEN')
    if STRAVAREFRESHTOKEN is None:
        print("STRAVAREFRESHTOKEN variable not set. Unable to launch bot.")


    # Grab the Strava auth token from STRAVATOKEN environment variable
    # This is used for Bearer authentication against Strava's API
    global STRAVATOKEN
    STRAVATOKEN = os.environ.get('STRAVATOKEN')
    if STRAVATOKEN is None:
        print("STRAVATOKEN variable not set. Unable to launch bot.")
        sys.exit()
    else:
        pass

    # STRAVACLIENTID environment variable
    global STRAVACLIENTID
    STRAVACLIENTID = os.environ.get('STRAVACLIENTID')
    if STRAVACLIENTID is None:
        print("STRAVACLIENTID variable not set. Unable to launch bot.")


    # STRAVASECRET environment variable
    global STRAVASECRET
    STRAVASECRET = os.environ.get('STRAVASECRET')
    if STRAVASECRET is None:
        print("STRAVASECRET variable not set. Unable to launch bot.")

    global stravaPublicHeader
    stravaPublicHeader = {'Host': 'www.strava.com ',
                          'Accept': 'text/javascript,application/javascript ',
                          'Referer': 'https://www.strava.com/clubs/' + STRAVACLUB,
                          'X-Requested-With': 'XMLHttpRequest'}

    # Grab the Discord bot token from DISCORDTOKEN environment variable
    global botToken
    botToken = os.environ.get('DISCORDTOKEN')

    if botToken is None:
        print("DISCORDTOKEN variable not set. Unable to launch bot.")

    # Grab the mongoDB user name from MONGO_USER environment variable
    failedMongo = False
    global MONGO_USER
    MONGO_USER = os.environ.get('MONGO_USER')
    if MONGO_USER is None:
        print("MONGO_USER variable not set. Unable to connect to database.")
        failedMongo = True


    global MONGO_PASSWD
    MONGO_PASSWD = os.environ.get('MONGO_PASSWD')
    if MONGO_PASSWD is None:
        print("MONGO_PASSWD variable not set. Unable to connect to database.")

    global MONGO_DB_NAME
    MONGO_DB_NAME = os.environ.get('MONGO_DB_NAME')
    if MONGO_DB_NAME is None:
        print("MONGO_DB_NAME variable not set. Unable to connect to database.")

    if not failedMongo:

        global mongoClient, mongoDb
        global userDataFile
        global userDataBase
        global debugInit
        try:
            mSite = 'mongodb+srv://' + MONGO_USER + ':' + MONGO_PASSWD + '@' + MONGO_DB_NAME
            mSite += '.mongodb.net/' + userDataFile + '?retryWrites=true&w=majority'
            mongoClient = motor.motor_tornado.MotorClient(mSite)
            if mongoClient is not None:
                mongoDb = mongoClient[userDataFile]
            else:
                debugInit += 'Failed to load mongo db\n'

        except Exception as e:
            print(e)
            debugInit += e



def refresh_token():
    global stravaToken, stravaTokenExpire
    print("Refreshing token")
    payload = {
        'client_id' : STRAVACLIENTID,
        'client_secret' : STRAVASECRET,
        'refresh_token' : STRAVAREFRESHTOKEN,
        'grant_type' : "refresh_token",
        'f':'json'
    }
    stravaToken = None # Initialize for clients to check against

    stravaTokenReq = requests.post('https://www.strava.com/api/v3/oauth/token',
                                   data=payload)
    if stravaTokenReq.status_code == 200:
        stravaToken = stravaTokenReq.json()['access_token']

        # Use fixed time for expiration 1 hour in seconds
        stravaTokenExpire = datetime.utcnow() + timedelta(seconds=int(60 * 60))



    return stravaToken, stravaTokenExpire

def getToken():
    global stravaToken, stravaTokenExpire
    if stravaToken is not None:
        if datetime.utcnow() > stravaTokenExpire:
            stravaToken, stravaTokenExpire = refresh_token()
        else:
            print("Current token is active")
    else:
        stravaToken, stravaTokenExpire = refresh_token()

    return stravaToken

def getNewToken():
    global stravaToken, stravaTokenExpire
    stravaToken, stravaTokenExpire = refresh_token()

    print('# Refresh token')

    return stravaToken

async def loadLeaderboard():
    publicLeaderboard = requests.get('https://www.strava.com/clubs/' +
                                     STRAVACLUB + '/leaderboard',
                                     headers=stravaPublicHeader)
    leaderboardJSON = None
    if publicLeaderboard.status_code == 200:
        leaderboardJSON = json.loads(publicLeaderboard.content)

    return leaderboardJSON

async def loadLastLeaderboard():
    publicLeaderboard = requests.get('https://www.strava.com/clubs/' +
                                     STRAVACLUB + '/leaderboard?week_offset=1',
                                     headers=stravaPublicHeader)
    leaderboardJSON = None
    if publicLeaderboard.status_code == 200:
        leaderboardJSON = json.loads(publicLeaderboard.content)

    return leaderboardJSON

# Determine if we have access to the Strava API
async def checkStravaAPI(ctx=None):
    stravaAccess = False

    return stravaAccess

async def checkAdmin(ctx=None):
    global admin
    if ctx is not None:
        name = ctx.message.author.id
        if name in admin:
            return True
    return False

async def checkCache(cacheTime):
    loadCache = False
    if cacheTime is None:
        cacheTime = time.time()
        loadCache = True
    else:
        currentTime = time.time()
        if currentTime - cacheTime > cacheTimeout:
            loadCache = True
    return loadCache

async def loadURL(url):
    # Load the URL data
    raw_response = await session.get(url)
    response = await raw_response.text()
    response = json.loads(response)

    return response




