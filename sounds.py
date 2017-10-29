#!/usr/bin/python

import os

from pygame import mixer
from threading import Thread, Lock

from utils import LOGGER

class Sound(object):
    def __init__(self, filename):
        if not os.path.isfile(filename):
            raise IOError("No such file: " + filename)
        # TODO check if file is actual sound file

        # internal state
        self.loaded     = False
        self.playing    = False

        # attributes
        self.volume     = 1.0
        self.length     = None

        # commands
        self.cstop      = False
        self.cstart     = False
        self.cvolume    = False

        # internal sound object
        self.sobj       = None

        # init lock around object
        self.lock       = Lock()

        # remember own filename
        self.filename   = filename

        LOGGER.logDebug("loading: " + filename)

        # load the sound
        Thread(target=self.__load).start()

    def __load(self):
        self.sobj = mixer.Sound(self.filename)
        self.loaded = True
        self.length = self.sobj.get_length()

        # make sure we catch all commands during load
        self.__update()

    def __update(self):
        if not self.loaded:
            return

        self.lock.acquire()
        #LOGGER.logDebug("acquired lock", self)

        if self.cstart and not self.playing:
            LOGGER.logDebug("start", self)
            self.sobj.play(-1)
            self.cstart = False
            self.playing = True

        if self.cstop and self.playing:
            LOGGER.logDebug("stop", self)
            self.sobj.stop()
            self.cstop = False
            self.playing = False

        if self.cvolume:
            LOGGER.logDebug("set volume to {} %".format(self.volume*100), self)
            self.sobj.set_volume(self.volume)
            self.cvolume = False

        #LOGGER.logDebug("releasing lock", self)
        self.lock.release()

    def setVolume(self, vol):
        self.cvolume = True
        self.volume  = vol
        self.__update()

    def getVolume(self):
        return self.volume

    def getLength(self):
        return self.length

    def play(self):
        self.cstart = True
        self.__update()

    def stop(self):
        self.cstop = True
        self.__update()

class SoundPool(object):
    def __init__(self):
        self.pool = dict()

    def get(self, filename):
        if not filename in self.pool:
            self.pool[filename] = Sound(filename)
        return self.pool[filename]
