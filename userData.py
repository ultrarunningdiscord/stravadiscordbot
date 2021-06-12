import json
import os

from borg import Borg
import globals

globalData = globals.Globals()

class UserData(Borg):
    def __init__(self):
        Borg.__init__(self)

        self.userData = {}
        try:
            f = open(globalData.userDataFile, "r")
            if os.path.getsize(globalData.userDataFile) > 0:
                self.userData = json.load(f)
        except IOError:
            try:
                open(globalData.userDataFile, "w+")
            except:
                print('# FAILED no data and not able to write it')
                exit()

    async def getUserData(self):
        return self.userData

    async def writeData(self):
        try:
            bFileDesc = open(globalData.userDataFile, "w")
            json.dump(self.userData, bFileDesc)
            bFileDesc.close()
        except Exception as e:
            pass

    async def registerStravaID(self, user, stravaId):
        # Register the user with their strava ID for leaderboard, etc.
        user = str(user) # Convert number id to string for easy lookup
        self.userData[user] = stravaId

        await self.writeData()
