
import asyncio
import aiohttp
import json
import os
import redis
import requests
import sys
import time

from borg import Borg

# Global data class for environment, tokens, other global information the bot needs as well as global functions
class Globals(Borg):
    def __init__(self):
        Borg.__init__(self)
        self.debug = False
        self.running = True

        try:
            self.redis_conn = redis.Redis(host='localhost', port=6379, db=0)
        except (redis.exceptions.ConnectionError, ConnectionRefusedError) as e:
            print('Redis connection error: ', e)


        # Grab the Strava Club ID from STRAVACLUB environment variable
        self.STRAVACLUB = os.environ.get('STRAVACLUB')
        if self.STRAVACLUB is None:
            print("STRAVACLUB variable not set. Unable to launch bot.")
            sys.exit()
        else:
            pass

        # Grab the Strava Club ID from STRAVACLUB_PRETTYNAME environment variable
        self.STRAVACLUB_PRETTYNAME = os.environ.get('STRAVACLUB_PRETTYNAME')
        if self.STRAVACLUB_PRETTYNAME is None:
            print("STRAVACLUB_PRETTYNAME variable not set. Unable to launch bot.")
            sys.exit()
        else:
            pass

        # Grab the Strava auth token from STRAVATOKEN environment variable
        # This is used for Bearer authentication against Strava's API
        self.STRAVAREFRESHTOKEN = os.environ.get('STRAVAREFRESHTOKEN')
        if self.STRAVAREFRESHTOKEN is None:
            print("STRAVAREFRESHTOKEN variable not set. Unable to launch bot.")
            sys.exit()
        else:
            pass

        # STRAVACLIENTID environment variable
        self.STRAVACLIENTID = os.environ.get('STRAVACLIENTID')
        if self.STRAVACLIENTID is None:
            print("STRAVACLIENTID variable not set. Unable to launch bot.")
            sys.exit()
        else:
            pass

        # STRAVASECRET environment variable
        self.STRAVASECRET = os.environ.get('STRAVASECRET')
        if self.STRAVASECRET is None:
            print("STRAVASECRET variable not set. Unable to launch bot.")
            sys.exit()
        else:
            pass

        self.stravaPublicHeader = {'Host': 'www.strava.com ',
                                   'Accept': 'text/javascript,application/javascript ',
                                   'Referer': 'https://www.strava.com/clubs/' + self.STRAVACLUB,
                                   'X-Requested-With': 'XMLHttpRequest'}

        # Grab the Discord bot token from DISCORDTOKEN environment variable
        self.botToken = os.environ.get('DISCORDTOKEN')

        if self.botToken is None:
            print("DISCORDTOKEN variable not set. Unable to launch bot.")
            sys.exit()
        else:
            pass

        self.admin = [302457136959586304]
        self.session = None
        self.cacheTimeout = 3600
        self.initialFree = 10000.0
        self.resolveTime = '11:54'
        self.resolveThread = None

    def refresh_token(self):
        print("Refreshing token")
        payload = {
            'client_id' : self.STRAVACLIENTID,
            'client_secret' : self.STRAVASECRET,
            'refresh_token' : self.STRAVAREFRESHTOKEN,
            'grant_type' : "refresh_token",
            'f':'json'
        }
        stravaTokenReq = requests.post('https://www.strava.com/api/v3/oauth/token',
                                       data=payload)

        access_token = stravaTokenReq.json()['access_token']
        access_token_expiry = stravaTokenReq.json()['expires_at']
        try:
            self.redis_conn.set('token', access_token)
        except redis.RedisError as e:
            print('Redis exception: ', e)
        try:
            self.redis_conn.set('expiry', access_token_expiry)
        except redis.RedisError as e:
            print('Redis exception: ', e)
        return access_token, access_token_expiry

    async def checkCache(self, cacheTime):
        loadCache = False
        if cacheTime is None:
            cacheTime = time.time()
            loadCache = True
        else:
            currentTime = time.time()
            if currentTime - cacheTime > self.cacheTimeout:
                loadCache = True
        return loadCache

    async def loadURL(self, url):
        # Load the URL data
        raw_response = await self.session.get(url)
        response = await raw_response.text()
        response = json.loads(response)

        return response

    async def validateResponse(self, response):
        # Check to see if we have a valid url JSON returned
        if response:
            if response[self.successKey] is not None:
                # Check to see we got money line data
                if response[self.successKey]:
                    return True

        return False

    async def checkType(self, sport):
        # Validate sport argument
        found = False
        if sport.lower() == self.nfl.lower():
            found = True
        elif sport.lower() == self.nba.lower():
            found = True
        elif sport.lower() == self.mlb.lower():
            found = True

        return found