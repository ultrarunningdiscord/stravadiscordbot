import asyncio
import discord
import schedule
import threading
import time


from threading import Timer, Thread, Event

import botGlobals


class DistanceLeader(Thread):
    def __init__(self, event):
        print('# ALS - DistanceLeader __init__')
        Thread.__init__(self)
        self.finished = event
        schedule.every().day.at(botGlobals.resolveTime).do(self.crownDistanceLeader)
        #schedule.every(30).seconds.do(self.crownDistanceLeader)
        self.loop = None

    def closeLoop(self):
        if self.loop is not None:
            self.loop.close()
            self.loop = None

    def cancel(self):
        #Terminate this thread
        # if self.loop is not None:
        #     self.closeLoop()

        self.finished.set()
    def crownDistanceLeader(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        self.loop.run_until_complete(self.findLeader())
        self.loop.close()

    async def findLeader(self):
        leaderboardJSON = await botGlobals.loadLeaderboard()
        print('# ALS - leaderboard '+str(leaderboardJSON))

    def run(self):
        while True:
            schedule.run_pending()
            time.sleep(1)