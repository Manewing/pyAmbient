#!/usr/bin/python

import os

from pygame import mixer
from threading import Thread, Lock

from utils import LOGGER

# @class Sound
# @brief Wrapper around pygame.mixer.sound class, which provides a
#   non-blocking (of the loading process) interface to said wrapped class.
class Sound(object):
    def __init__(self, filename):
        if not os.path.isfile(filename):
            raise IOError("No such file: " + filename)
        # TODO check if file is actual sound file

        # internal state
        self.loaded     = False

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

    # @brief __load - loads the actual sound file and runs update
    def __load(self):
        self.sobj = mixer.Sound(self.filename)
        self.loaded = True
        self.length = self.sobj.get_length()

        # make sure we catch all commands during load
        self.__update()

    # @brief __update - updates the current state of the sound file,
    #   if the actual file is not loaded does nothing
    def __update(self):
        if not self.loaded:
            return

        self.lock.acquire()
        #LOGGER.logDebug("acquired lock", self)

        if self.cstart:
            LOGGER.logDebug("start", self)
            self.sobj.play(-1)
            self.cstart = False

        if self.cstop:
            LOGGER.logDebug("stop", self)
            self.sobj.stop()
            self.cstop = False

        if self.cvolume:
            LOGGER.logDebug("set volume to {} %".format(self.volume*100), self)
            self.sobj.set_volume(self.volume)
            self.cvolume = False

        #LOGGER.logDebug("releasing lock", self)
        self.lock.release()

    # @brief setVolume - sets the volume of the sound
    # @param[in] vol - the volume to set (range 0.0 to 1.0)
    def setVolume(self, vol):
        self.cvolume = True
        self.volume  = vol
        self.__update()

    # @brief getVolume - get the volume of the sound
    def getVolume(self):
        return self.volume

    # @brief getLength - get the length of the sound
    def getLength(self):
        return self.length

    # @brief play - starts playback of the sound
    def play(self):
        self.cstart = True
        self.__update()

    # @brief stop - stops the playback of the sound
    def stop(self):
        self.cstop = True
        self.__update()

# @class SoundPool
# @brief Handles Sound instances by file path
class SoundPool(object):

    # @brief constructor
    def __init__(self):
        self.pool = dict()

    # @brief get - gets a sound by filename
    # @param[in] filename - path to the sound file to get
    def get(self, filename):
        if not filename in self.pool:
            self.pool[filename] = Sound(filename)
        return self.pool[filename]

    # @brief reset - resets the sound pool
    def reset(self):
        self.pool = dict()
