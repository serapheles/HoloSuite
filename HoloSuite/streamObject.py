from __future__ import unicode_literals
import threading
import requests
import youtube_dl
import logging
import shutil
import time
from youtube_dl.utils import DownloadError

#How useful is this?
stream_log = logging.getLogger('stream.threads')


#Add hook for error chain?
def cleanup(d):
    if d['status']=='finished':
        try:
            shutil.move(d['filename'], 'finished/')
            shutil.move(d['filename'].replace('.mp4','.info.json'),'finished/')
            stream_log.info("File moved: %s", d['filename'])
        except:
            stream_log.error("File failed to move: %s", d['filename'])

class StreamObject:
    def __init__(self, data, delta, caller):
        self.URL = "https://api.holotools.app/v1/videos/youtube/"
        self.streamInfo = data
        self._time = delta
        self.parent = caller
        self.ytID = self.streamInfo['yt_video_key']

        #If this works, try changing the last bit
        self.logger = logging.getLogger('stream.threads.' + self.ytID)

        #add cookie option?
        self.ydl_opts = {
            'nopart': True,
            'hls_use_mpegts': True,
            #'verbose': True,
            'quiet': True,
            'nooverwrites': True,
            'writeinfojson': True,
            'logger': self.logger,
            'skip_download': False,     #REMOVE THIS, FOR TESTING
            #'cookiefile': "/home/siorraidh/code/cookies.txt",
            'socket_timeout': 75,
            'progress_hooks':[cleanup],    #What is this notation?
            'fixup': 'detect_or_warn',   #Is this helpful at all?
            }

        # r = requests.get("https://api.holotools.app/v1/videos/youtube/" + self.ytID)
        # rfile = open("r.json", 'a')
        # rfile.write(r.text)
        # rfile.close()

        self.loop()
        #sever thread here?

    def loop(self):
        #time.sleep(self._time)
        #Currently not
        self.logger.info("Initial Delta: %s", self._time)
        while self._time >= 0:
            self.ytCall()
            self.logger.info("Current Delta: %s", self._time)
            if self._time > 0:
                time.sleep(self._time)

    def ytCall(self):
        with youtube_dl.YoutubeDL(self.ydl_opts) as ydl:
            try:
                ydl.download([self.ytID])
                self._time = -1
            except DownloadError as error:
                self.errorCheck(error)

    def errorCheck(self, error):
        strError = str(error)
        if "This live event will begin in" in strError:
            if "a few moments." in strError:
                self._time = 10
                return
            error_string = strError.split()
            if (error_string[-1] == "minutes."):
                mins = (int(error_string[-2]))
                #Could use huristics here, but we're already one layer in.
                self._time = (mins * 45)
                return

            if (error_string[-1] == "hours."):
                self._time = (int(error_string[-2]) * 3600)
                #self.logger.warning(error)
                return

            if (error_string[-1] == "days."):
                self._time = (int(error_string[-2]) * 3600 * 24)
                return

        if "No video formats found" in strError:
            self.logger.warning(error)
            self._time = 10
            return

        if "Join this channel to get access to members-only content like this video" \
            + ", and other exclusive perks." in strError:
            #logging.debug("Member video: %s", self.ytID)
            self._time = -1
            return

        #logging.debug(error)
        self._time = -1

#https://www.youtube.com/watch?v=aVbLkjhdbSc test age
