import requests
import logging
import sys
import time
import threading
from datetime import datetime
from datetime import timedelta
import streamObject
#from StreamObject import StreamObject
from chat_archive import fetch

log = logging.getLogger('stream')
#log = logging.getLogger(__name__)  #Typical notation
handler = logging.FileHandler("stream.log")
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
log.addHandler(handler)
log.setLevel(10)

class StreamCheck:
    def __init__(self, write_response):
        self.OPTS = {"lookback_hours":"0", "max_upcoming_hours":"168"}
        self.URL = "https://api.holotools.app/v1/live"
        self.writeState = write_response
        self.memberList = ["UCL_qhgtOy0dy1Agp8vkySQg",  #Calli
        "UCHsx4Hqa-1ORjQTh9TYDhww",                     #Kiara
        "UCoSrY_IQQVpmIRZ9Xf-y93g",                     #Gura
        "UCyl1z3jo3XHR1riLFKG5UAg",                     #Ame
        "UCMwGHR0BTZuLsmjY_NT5Pwg",                     #Ina
        "UC1CfXB_kRs3C-zaeTG3oGyg",                     #HAACHAMACHAMA!
        "UCYz_5n-uDuChHtLo7My1HnQ",                     #Ollie
        "UCS9uQI-jC3DE0L4IpXyvr6w"                      #Kaichou!
        ]

        self.keyList = ["archive",
        "asmr",
        "アーカイブ",
        "録画は残しません"
        ]
        #Hold threads here, sever chat on exit, ytdl as needed?

        self.found = dict()
        self.excluded = set()
        self.streamLoop()

    def apiRequest(self):
        while True:
            try:
                return requests.get(self.URL, params=self.OPTS)
            except:
                log.warning("Requests failed")
                time.sleep(15)
                continue

    def process(self, item, ytID):
        if ytID in self.found:
            #Check "live_start"? If found, add and exclude
            if self.found[ytID]["live_schedule"][:-1] == item["live_schedule"][:-1]:
                return True
            #Stream postponed; thread should take care of it.
            elif self.found[ytID]["live_schedule"][:-1] < item["live_schedule"][:-1]:
                return True
        else:
            log.info("Item found: %s", ytID)
            #add chat to thread group. fabric? loom?
            threading.Thread(target=fetch, args = (ytID,)).start()
            #check if chat was previously unavailable?
        self.found[ytID] = item

        if item['live_start'] == None:
            #This is a direct calc for datetime.timestamp()
            delta = (datetime.fromisoformat(item["live_schedule"][:-1]) - datetime.utcnow())/timedelta(seconds=1)
            if delta > 300:
                threading.Thread(target=streamObject.StreamObject, args = (item, delta - 270, self,)).start()
            elif delta > 30:
                threading.Thread(target=streamObject.StreamObject, args = (item, delta - 30, self,)).start()
            else:
                threading.Thread(target=streamObject.StreamObject, args = (item, 0, self,)).start()
        else:
            threading.Thread(target=streamObject.StreamObject, args = (item, 0, self,)).start()
            self.excluded.add(item['yt_video_key'])
        return True

    def streamSearch(self, data):
        for item in data:
            ytID = item['yt_video_key']
            if ytID in self.excluded:
                continue
            if item['channel']['yt_channel_id'] in self.memberList:
                self.process(item, ytID)
                continue
            for word in self.keyList:
                if word in item['title'].casefold().strip():
                    self.process(item, ytID)
                    continue
            self.excluded.add(item['yt_video_key'])

    def pipeLoop(self):
        FIFO = 'urlpipe'
        try:
            os.mkfifo(FIFO)
        except OSError as osErr:
            if osErr.errno != errno.EEXIST:
                raise
        while True:
            with open(FIFO) as fifo:
                input = fifo.readline().rstrip()
                if len(input) < 10:
                    log.warning('Input found, but less than 10 characters: %s', input)
                    break
                if len(input) == 11:
                    log.info("Item found from pipe: %s", input)
                    #add to queue
                elif "youtu" in input:
                    val = str.format(input[-11:])
                    log.info("Item found from pipe: %s", input)
                    #add to queue
                else:
                    log.warning("Item found from pipe: %s, not a Youtube value", input)
                    #add to queue anyways

    def streamLoop(self):
        while True:
            self.apiState = self.apiRequest()
            #Double check state isn't empty?
            if(self.writeState):
                rFile = open("apiResponse.json", "w")
                rFile.write(self.apiState.text)
                rFile.close()

            self.streamSearch(self.apiState.json()['live'])
            self.streamSearch(self.apiState.json()['upcoming'])

            time.sleep(60)

def main():
    primary = StreamCheck(True)

if __name__ == "__main__":
    main()
