

from datetime import datetime, date, timedelta
import json
import os
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
STRAVACLUB = None
STRAVACLUB_PRETTYNAME = None
STRAVAREFRESHTOKEN = None
STRAVATOKEN = None
STRAVACLIENTID = None
STRAVASECRET = None
botToken = None
stravaPublicHeader = None
admin = [302457136959586304]
session = None
cacheTimeout = 3600
initialFree = 10000.0
resolveTime = '23:59'
leaderThread = None

def initUserData():
    # Load the data
    global userData
    global redis_conn
    global userDataFile
    try:
        userData = json.loads(redis_conn.get(userDataFile))
        if not userData:
            # Initialize it with empty dictionary
            userData = {}
            redis_conn.set(userDataFile, json.dumps(userData))
    except Exception as e:
        print('# Failed to access redis-server in initUserData')

    # File system approach
    # try:
    #     f = open(botGlobals.userDataFile, "r")
    #     if os.path.getsize(botGlobals.userDataFile) > 0:
    #         userData = json.load(f)
    # except IOError:
    #     try:
    #         open(botGlobals.userDataFile, "w+")
    #     except:
    #         print('# FAILED no data and not able to write it')
    #         exit()

def init():

    try:
        global redis_conn
        redis_conn = redis.Redis(host='localhost', port=6379, db=0)
    except (redis.exceptions.ConnectionError, ConnectionRefusedError) as e:
        print('Redis connection error: ', e)


    # Grab the Strava Club ID from STRAVACLUB environment variable
    global STRAVACLUB
    STRAVACLUB = os.environ.get('STRAVACLUB')
    if STRAVACLUB is None:
        print("STRAVACLUB variable not set. Unable to launch bot.")
        sys.exit()
    else:
        pass

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
        sys.exit()
    else:
        pass

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
        sys.exit()
    else:
        pass

    # STRAVASECRET environment variable
    global STRAVASECRET
    STRAVASECRET = os.environ.get('STRAVASECRET')
    if STRAVASECRET is None:
        print("STRAVASECRET variable not set. Unable to launch bot.")
        sys.exit()
    else:
        pass
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
        sys.exit()
    else:
        pass

    # Initialize data file
    initUserData()


def refresh_token():
    print("Refreshing token")
    payload = {
        'client_id' : STRAVACLIENTID,
        'client_secret' : STRAVASECRET,
        'refresh_token' : STRAVAREFRESHTOKEN,
        'grant_type' : "refresh_token",
        'f':'json'
    }
    stravaTokenReq = requests.post('https://www.strava.com/api/v3/oauth/token',
                                   data=payload)

    access_token = stravaTokenReq.json()['access_token']
    #access_token_expiry = stravaTokenReq.json()['expires_in']
    # Use fixed time for expiration 1 hour in seconds
    access_token_expiry = 60 * 60
    global redis_conn
    try:
        redis_conn.set('token', access_token)
    except redis.RedisError as e:
        print('Redis exception: ', e)
    try:
        redis_conn.set('expiry', access_token_expiry)
    except redis.RedisError as e:
        print('Redis exception: ', e)
    return access_token, access_token_expiry

def getToken():
    global redis_conn
    try:
        access_token = redis_conn.get('token').decode()
        token_expiry = redis_conn.get('expiry').decode()
    except:
        # If we except here, its due to a none byte error against decode
        # TODO there might be a better way to handle this
        access_token, token_expiry = refresh_token()

    token_expire_time = datetime.utcnow() + timedelta(seconds=int(token_expiry))

    if datetime.utcnow() > token_expire_time:
        access_token, token_expiry = refresh_token()
    else:
        print("Current token is active")

    return access_token

def getNewToken():
    global redis_conn

    access_token, token_expiry = refresh_token()

    print('# Refresh token')

    return access_token

async def loadLeaderboard():
    publicLeaderboard = requests.get('https://www.strava.com/clubs/' +
                                     STRAVACLUB + '/leaderboard',
                                     headers=stravaPublicHeader)

    leaderboardJSON = json.loads(publicLeaderboard.content)

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





