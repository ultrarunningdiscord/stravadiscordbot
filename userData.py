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
    # *** Deletes the entry and replaces it ****
    if botGlobals.mongoDb is None:
        # No access to Mongo DB
        return False



    collection = botGlobals.mongoDb[collectionName] # Retrieves the discord id data(Mongo collection)

    # Delete the data and replace
    try:
        result = await collection.find_one_and_delete(data)
        # Add the key/value
        _id = await collection.insert_one(data)
    except Exception as e:
        print(e)
        return False

    return True
async def setRegistration(discordId, stravaId):
    dataset = await setData(collectionName=botGlobals.registrationData,
                            data={'id':discordId, 'stravaId':stravaId})
    return dataset

async def retrieveDiscordID(stravaId):
    discordId = None
    # Search the database for this stravaId
    collectionList = await botGlobals.mongoDb.list_collection_names()
    if botGlobals.registrationData in collectionList:
        # Search the collection

        collection = botGlobals.mongoDb[botGlobals.registrationData]
        result = await collection.find_one({'stravaId': stravaId})
        if result is not None:

            discordId = int(result['id']) # Convert back into integer



    return discordId

async def deleteDiscordID(discordId):
    # Delete the database registration entry
    collectionList = await botGlobals.mongoDb.list_collection_names()
    if botGlobals.registrationData in collectionList:
        # Search the collection

        collection = botGlobals.mongoDb[botGlobals.registrationData]
        result = await collection.delete_one({'id': discordId})

    return result