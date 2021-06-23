
from datetime import datetime, date, timedelta
import pickle

import botGlobals

async def getDataCollection(collectionName):
    # Retrieves the collection of data from the Mongo DB
    collection = None # Default no data for this user
    if botGlobals.mongoDb is not None:
        collectionList = await botGlobals.mongoDb.list_collection_names()
        if collectionName in collectionList:
            collection = botGlobals.mongoDb[collectionName] # Mongo collection

    return collection

async def setData(collectionName, data):
    # Set the collection data in the Mongo DB
    # *** CALLER RESPONSIBILITY TO DELETE IF NEEDED ****
    if botGlobals.mongoDb is None:
        # No access to Mongo DB
        return False

    collection = botGlobals.mongoDb[collectionName] # Retrieves the discord id data(Mongo collection)

    try:
        # Add the key/value
        _id = await collection.insert_one(data)

    except Exception as e:
        print(e)
        return False

    return True

async def setRegistration(discordId, stravaId, displayName, avatarURL, nickname=None):
    d = {'id':discordId, 'stravaId':stravaId, 'display_name':displayName,
         'avatar_url':str(avatarURL)}

    if nickname is not None:
        d = {'id':discordId, 'stravaId':stravaId, 'display_name':displayName,
             'avatar_url':str(avatarURL), 'nick':nickname}

    dataset = await setData(collectionName=botGlobals.registrationData,
                            data=d)
    return dataset

async def buildRegistrationCache():
    if botGlobals.registrationCache is None:
        # Cache the database collection the cache is cleared when someone starts registration
        collection = await getDataCollection(collectionName=botGlobals.registrationData)

        if collection is not None:
            # Load the cache for faster lookup
            cursor = collection.find()
            botGlobals.registrationCache = {}
            for r in await cursor.to_list(length=1000):
                botGlobals.registrationCache[str(r['stravaId'])] = {'id':r['id'], 'display_name':r['display_name'],
                                                                    'avatar_url':r['avatar_url']}
                if 'nick' in r:
                    botGlobals.registrationCache[str(r['stravaId'])] = {'id':r['id'], 'display_name':r['display_name'],
                                                                        'avatar_url':r['avatar_url'], 'nick':r['nick']}

async def retrieveDiscordID(stravaId):
    discordId = None
    # Search the database for this stravaId
    await buildRegistrationCache()

    if str(stravaId) in botGlobals.registrationCache:
        user = botGlobals.registrationCache[str(stravaId)]
        discordId = int(user['id']) # Convert back into integer



    return discordId

async def retrieveNickname(stravaId):
    # Retrieve nickname from database and if it doesn't exist get display_name
    nickName = None
    await buildRegistrationCache()

    if str(stravaId) in botGlobals.registrationCache:
        user = botGlobals.registrationCache[str(stravaId)]
        nickName = user['display_name']
        if 'nick' in user:
            nickName = user['nick']

    return nickName


async def deleteDiscordID(discordId):
    # Delete the database registration entry
    result = None
    collection = await getDataCollection(collectionName=botGlobals.registrationData)
    if collection is not None:
        result = await collection.delete_one({'id': discordId})
    return result

async def resetLeaderBoardCache(lbJson, discordId):
    # Resets the leaderboard cache for this user to prevent
    # accidental registration if they are AFK for more than 10 minutes
    # and the leaderboard changes
    resetSuccess = False
    # Use fixed time for expiration 10 minutes
    expiration = datetime.utcnow() + timedelta(seconds=int(10 * 60))
    try:
        expiration = pickle.dumps(expiration)
        # Attempt to delete the current cache
        collection = await getDataCollection(collectionName=botGlobals.cacheData)
        if collection is not None:
            result = await collection.delete_many({'id':discordId})


        resetSuccess = await setData(collectionName=botGlobals.cacheData,
                                     data={'id':discordId, 'leaderboardData':lbJson, 'expires':expiration})
    except Exception as e:
        print(e)
        botGlobals.debugInit += e

    return resetSuccess



async def checkLeaderBoardCache(discordId):
    cacheData = None
    collection = await getDataCollection(collectionName=botGlobals.cacheData)
    if collection is not None:
        result = await collection.find_one({'id': discordId})
        if result is not None:
            expiration = pickle.loads(result['expires'])
            if datetime.utcnow() <= expiration:
                # Valid cache
                cacheData = result['leaderboardData']

    return cacheData

async def clearLeaderBoardCache():
    # Clear out any expired caches
    collection = await getDataCollection(collectionName=botGlobals.cacheData)
    if collection is not None:

        cursor = collection.find()
        updateData = []
        for r in await cursor.to_list(length=1000):
            expiration = pickle.loads(r['expires'])
            if datetime.utcnow() > expiration:
                updateData.append(r)

        for d in updateData:
            result = await collection.delete_many({'id':d['id']})

async def getMontlyMileage(monthyear):
    # Return the monthly mileage
    monthlyMileage = None
    collection = await getDataCollection(botGlobals.monthlyMileageData)

    if collection is not None:
        monthlyMileage = await collection.find_one({monthyear: {"$exists": True}})


    return monthlyMileage

async def setMontlyMileage(monthyear, data):


    # If you find this strava athlete add to the miles with this weeks miles
    collection = await getDataCollection(botGlobals.monthlyMileageData)

    if collection is not None:
        result = await collection.find_one({monthyear: {"$exists": True}})
        if result is not None:
            # Delete this entry
            result = await collection.delete_many({monthyear: {"$exists": True}})
    # Set the data for this monthYear
    dataset = await setData(collectionName=botGlobals.monthlyMileageData,
                            data={monthyear:data})

    pass