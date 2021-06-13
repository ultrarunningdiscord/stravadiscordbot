from datetime import datetime, date, timedelta
import json
import os
import pickle
import redis
import requests
import sys
import time



# Global data for environment, tokens, other global information the bot needs as well as global functions

debug = False
running = True
userDataFile = 'stravaBot.userData'
userData = {}
redis_conn = None
STRAVACLUB = ''
STRAVACLUB_PRETTYNAME = ''
STRAVAREFRESHTOKEN = ''
STRAVATOKEN = ''
STRAVACLIENTID = ''
STRAVASECRET = ''
botToken = None
stravaToken = None
stravaTokenExpire = None
stravaPublicHeader = None
admin = [302457136959586304]
session = None
cacheTimeout = 3600
initialFree = 10000.0
resolveTime = '23:59'
leaderThread = None

def init():
    global redis_conn
    try:
        redis_conn = redis.Redis(host='localhost', port=6379, db=0)
    except (redis.exceptions.ConnectionError, ConnectionRefusedError) as e:
        print('Redis connection error: ', e)


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





def refresh_token():
    global stravaToken, stravaTokenExpire, redis_conn
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

        if redis_conn is not None:
            try:
                redis_conn.set('token', stravaToken)
            except redis.RedisError as e:
                print('Redis exception: ', e)
            try:
                redis_conn.set('expiry', pickle.dumps(stravaTokenExpire))
            except redis.RedisError as e:
                print('Redis exception: ', e)

    return stravaToken, stravaTokenExpire

def getToken():
    global redis_conn, stravaToken, stravaTokenExpire
    if redis_conn is not None:
        try:
            stravaToken = redis_conn.get('token').decode()
            stravaTokenExpire = redis_conn.get('expiry')
            if stravaTokenExpire is None:
                stravaToken, stravaTokenExpire = refresh_token()
            else:
                # Convert to datetime object
                stravaTokenExpire = pickle.dumps(stravaTokenExpire)
        except:
            # If we except here, its due to a none byte error against decode
            # TODO there might be a better way to handle this
            stravaToken, stravaTokenExpire = refresh_token()

    if datetime.utcnow() > stravaTokenExpire:
        stravaToken, stravaTokenExpire = refresh_token()
    else:
        print("Current token is active")

    return stravaToken

def getNewToken():
    global stravaToken, stravaTokenExpire
    stravaToken, stravaTokenExpire = refresh_token()

    print('# Refresh token')

    return stravaToken

async def loadLeaderboard():
    print('# ALS - load leaderboard')
    publicLeaderboard = requests.get('https://www.strava.com/clubs/' +
                                     STRAVACLUB + '/leaderboard',
                                     headers=stravaPublicHeader)
    print('# ALS - lb '+str(publicLeaderboard))
    leaderboardJSON = None
    if publicLeaderboard.status_code == 200:
        print('# ALS - load json')
        leaderboardJSON = json.loads(publicLeaderboard.content)
        print('# ALS - finished json load')

    return leaderboardJSON

async def getUserData():
    global userData
    return userData

async def writeData():
    global redis_conn
    global userDataFile
    global userData
    try:
        redis_conn.set(userDataFile, json.dumps(userData))
    except Exception as e:
        print('# Failed to access redis-server in writeData')

    # File system approach
    # try:
    #     bFileDesc = open(botGlobals.userDataFile, "w")
    #     json.dump(userData, bFileDesc)
    #     bFileDesc.close()
    # except Exception as e:
    #     pass

async def registerStravaID(user, stravaId):
    global userData
    # Register the user with their strava ID for leaderboard, etc.
    user = str(user) # Convert number id to string for easy lookup
    if user not in userData:
        userData[user] = {'stravaId': stravaId}
    else:
        data = userData[user]
        data['stravaId'] = stravaId
        userData[user] = data

    await writeData()

async def retrieveDiscordID(stravaId):
    global userData
    for u,d in userData.items():
        if 'stravaId' in d:
            id = d['stravaId']
            if id == stravaId:
                return u

    return None

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





