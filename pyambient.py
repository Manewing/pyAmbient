#!/usr/bin/python

from pygame import mixer
from xml.etree import ElementTree as XmlEt

from utils import LOGGER
from sounds import SoundPool
from threading import Timer
from random import randint

def constrain(x, mi, ma):
    return min(ma, max(mi, x))

class AmbientSound(object):
    def __init__(self, sound, base, drift, rate_min, rate_max):
        self.sound    = sound
        self.base     = base
        self.drift    = drift
        self.rate_min = rate_min
        self.rate_max = rate_max
        self.rate     = (1 - randint(0,1)*2)

        # initialize rate
        self.newRate()

        # initialize sound
        self.sound.setVolume(self.base)

    def newRate(self):
        if self.rate > 0:
            self.rate = -float(randint(self.rate_min, self.rate_max))
        else:
            self.rate = float(randint(self.rate_min, self.rate_max))

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

    def play(self):
        self.sound.play()

    def stop(self):
        self.sound.stop()


class Ambient(object):
    def __init__(self, configfile, spool):

        # load configuration file
        with open(configfile, "r") as f:
            data = f.read()
        root = XmlEt.fromstring(data)

        # set the name of the ambient
        self.name    = root.get("name")

        # set the update rate from the volatility
        self.urate   = 1.0 / float(root.get("volatility"))
        self.urate   = constrain(self.urate, 0.0, 5.0)

        # flag indicating whether ambient is currently running
        self.running = False

        # load sounds and sound configuration
        self.sounds = list()
        for soundcfg in root.findall("Sound"):
            sfile  = soundcfg.get("file")
            base   = float(soundcfg.get("base"))
            drift  = float(soundcfg.get("drift"))

            LOGGER.logDebug("load sound {} with [{}] +/- ({})".format(sfile, base, drift))

            # load sound from sound pool and initialize it
            sound = spool.get(sfile)
            self.sounds.append(AmbientSound(sound, base, drift, 4, 16))

    def __update(self):
        if not self.running:
            return
        LOGGER.logDebug("'{}' update".format(self.name))

        for sound in self.sounds:
            sound.adaptVolume()

        Timer(self.urate, self.__update).start()

    def getName(self):
        return self.name

    def start(self):
        for sound in self.sounds:
            sound.play()

        # indicate start
        self.running = True
        self.__update()

    def stop(self):
        for sound in self.sounds:
            sound.stop()

        # indicate stop
        self.running = False

class AmbientControl(object):
    def __init__(self, configfile):

        # check if mixer is already initialized
        if mixer.get_init() == True:
            raise RuntimeError("pygame.mixer already initialized, abort")

        LOGGER.logDebug("initialize pygame.mixer")

        # set parameters of mixer before init, TODO check values again
        mixer.pre_init(44100, -16, 2, 2048)
        mixer.init()

        # initialize sound pool
        self.spool = SoundPool()
