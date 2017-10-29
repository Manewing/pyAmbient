#!/usr/bin/python

from pygame import mixer
from threading import Timer
from random import randint
from xml.etree import ElementTree as XmlEt

import argparse

from utils import LOGGER
from sounds import SoundPool

# @brief constrain - constrains x to interval [mi, ma]
def constrain(x, mi, ma):
    return min(ma, max(mi, x))

# @class AmbientSound
# @brief wrapper class around class sounds.Sound, handles updates
#   of volume and stores ambient sound configuration
class AmbientSound(object):

    # @brief constructor
    # @param[in] sound    - the sound object to wrap around
    # @param[in] base     - the base volume of the sound
    # @param[in] drift    - the volume drift of the sound
    # @param[in] rate_min - the minimal update rate of the sound
    # @param[in] rate_max - the maximal update rate of the sound
    def __init__(self, sound, base, drift, rate_min, rate_max):
        self.sound    = sound
        self.base     = base
        self.drift    = drift
        self.rate_min = rate_min
        self.rate_max = rate_max
        self.rate     = (1 - randint(0,1)*2)

        # check base and drift values
        if base - drift < 0.0 or base + drift > 1.0:
          raise ValueError("Volume base +/- drift exceeds boundaries [0.0,1.0]")

        # initialize rate
        self.newRate()

        # initialize sound
        self.sound.setVolume(self.base)

    # @brief newRate - sets new random rate with opposite sign than before
    def newRate(self):
        if self.rate > 0:
            self.rate = -float(randint(self.rate_min, self.rate_max))
        else:
            self.rate = float(randint(self.rate_min, self.rate_max))

    # @brief adaptVolume - adapts the sound volume by 'drift/rate'
    def adaptVolume(self):
        vol     = self.sound.getVolume() + self.drift / self.rate
        max_vol = self.base + self.drift
        min_vol = self.base - self.drift

        # check new volume
        if vol >= max_vol or vol <= min_vol:
            vol = constrain(vol, min_vol, max_vol)
            self.newRate()

        # set new volume
        self.sound.setVolume(vol)

    # @brief play - starts sound playing
    def play(self):
        self.sound.play()

    # @brief stop - stops sound playing
    def stop(self):
        self.sound.stop()

# @class Ambient
# @brief an ambient consisting of different sound files
class Ambient(object):

    # @brief constructor
    # @param[in] configfile - the configuration file of the ambient
    # @param[in] spool      - the sound pool the ambient should use
    def __init__(self, configfile, spool = SoundPool()):

        # load configuration file
        with open(configfile, "r") as f:
            data = f.read()
        root = XmlEt.fromstring(data).find("Ambient")

        # set the name of the ambient
        self.name    = root.get("name")

        LOGGER.logInfo("Ambient '{}'".format(self.name))

        # set the update rate from the volatility
        self.urate   = 1.0 / float(root.get("volatility"))
        self.urate   = constrain(self.urate, 0.0, 5.0)

        # flag indicating whether ambient is currently running
        self.loaded  = False
        self.running = False

        # load sounds and sound configuration
        self.sounds = list()
        self.spool  = spool
        for soundcfg in root.findall("Sound"):
            sfile  = soundcfg.get("file")
            base   = float(soundcfg.get("base"))
            drift  = float(soundcfg.get("drift"))

            self.sounds.append((sfile, base, drift))

            LOGGER.logInfo("'{}': [{}] +/- ({})".format(sfile, base, drift))


    # @brief __load - loads the actual ambient, delayed until it is started
    def __load(self):
        sounds = list()

        for soundcfg in self.sounds:
            sfile, base, drift = soundcfg

            # load sound from sound pool and initialize it
            sound = self.spool.get(sfile)
            sounds.append(AmbientSound(sound, base, drift, 4, 16))

        # reset sounds, original only stored configuration
        self.sounds = sounds
        self.loaded = True


    # @brief __update - internal update function, adapts the volumes of all
    #   sounds
    #
    #   Note: If ambient is running this function schedules itself with
    #     period 'self.urate'
    #
    def __update(self):
        if not self.running:
            return
        LOGGER.logDebug("'{}' update".format(self.name))

        for sound in self.sounds:
            sound.adaptVolume()

        Timer(self.urate, self.__update).start()

    # @brief getName - returns the configured name of the ambient
    def getName(self):
        return self.name

    # @brief start - starts playback of ambient
    def start(self):
        if not self.loaded:
            self.__load()

        for sound in self.sounds:
            sound.play()

        # indicate start
        self.running = True
        self.__update()

    # @brief stop - stops playback of ambient
    def stop(self):
        if not self.loaded:
            return

        for sound in self.sounds:
            sound.stop()

        # indicate stop
        self.running = False

# @class AmbientControl
# @brief Handles a set of configured ambients
class AmbientControl(object):

    # @brief constructor
    # @param[in] configfile - a pyAmbient configuration file
    def __init__(self, configfile):

        # check if mixer is already initialized
        if mixer.get_init() == True:
            raise RuntimeError("pygame.mixer already initialized, abort")

        LOGGER.logDebug("initialize pygame.mixer")

        # set parameters of mixer before init, TODO check values again
        mixer.pre_init(44100, -16, 2, 2048)
        mixer.init()

        # load configuration file
        with open(configfile, "r") as f:
            data = f.read()
        root = XmlEt.fromstring(data)

        # setup ambient dictionary
        self.ambients = dict()
        for elem in root.findall("AmbientConfig"):
            self.ambients[elem.get("id")] = elem.get("file")

        # set current ambient to none
        self.ambient = None

    # @brief getName - get the name of the ambient with given ID
    # @param[in] ambient_id - ID of the ambient to get the name of
    def getName(self, ambient_id):
        return self.ambients

    # @brief switch - switches to ambient with given ID
    # @param[in] ambient_id - ID of the ambient to switch to
    def switch(self, ambient_id):
        if self.ambient != None:
            self.ambient.stop()
        self.ambient = Ambient(self.ambients[ambient_id])
        self.ambient.start()

        LOGGER.logInfo("Switched to ambient '{}'".format(self.ambient.getName()))



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="pyAmbient")
    parser.add_argument("-c", "--config", dest="config", required=True,
            help="the pyAmbient configuration file to load")
    parser.add_argument("-a", "--ambient", dest="ambient", required=True,
            help="the ambient ID of the ambient to start")
    parser.add_argument("-d", "--debug", dest="debug", required=False,
            help="if to log debug information", default=False, action="store_true")
    args = parser.parse_args()

    if args.debug == True:
        LOGGER.setLevel(0)
    else:
        LOGGER.setLevel(1)

    ambc = AmbientControl(args.config)
    ambc.switch(args.ambient)
