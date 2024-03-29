import json
import numpy as np
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
from uhd import libpyuhd as lib
import math

waveforms = {
    "sine": lambda n, tone_offset, rate: np.exp(n * 2j * np.pi * tone_offset / rate)
}


class EventHandler(FileSystemEventHandler):
    def __init__(self, streamer, waveMonitor):
        super(EventHandler, self).__init__()
        self.streamer = streamer
        self.waveMonitor = waveMonitor

    def on_any_event(self, event):
        print self.waveMonitor.getTotalPower(0)
        print self.waveMonitor.getTotalPower(1)
        if self.waveMonitor.getTotalPower(1) < 30 and self.waveMonitor.getTotalPower(0) < 30:
            self.streamer.wave = self.waveMonitor.getOutputWaveform()
        else:
            print "WARNING: TOO MUCH POWER"


class WaveformMonitor(object):

    def __init__(self, waveformFile, usrp):
        self.waveformFile = waveformFile
        self.jsonData = self.getJsonData()
        self.usrp = usrp
        self.initializeWaveforms()
        self.modTime = os.stat(self.waveformFile).st_mtime

    def changeFile(self, file):
        self.waveformFile = file
        self.jsonData = self.getJsonData()
        self.initializeWaveforms()
        self.modTime = os.stat(self.waveformFile).st_mtime

    def getTotalPower(self, channel):
        # power out of SDR with 4db attenuator and 0 gain with waveforms at 1
        zeroPower = -20
        amplifier = 34
        sumOfWaveforms = 10*math.log10(sum(self.getAmplitudes(channel)))
        return zeroPower+amplifier+sumOfWaveforms+self.jsonData['channels'][str(channel)]['gain']

    def getAmplitudes(self, channel):
        amplitudes = []
        for wave in self.jsonData['channels'][str(channel)]['waves']:
            amplitudes.append(wave['amplitude'])
        return amplitudes

    def startMonitor(self, stream):
        path = os.path.dirname(os.path.abspath(self.waveformFile))
        event_handler = EventHandler(stream, self)
        observer = Observer()
        observer.schedule(event_handler, path)
        observer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()

    def compareFreqs(self, jsonData):
        for channel in jsonData["channels"]:
            for wave1, wave2 in zip(jsonData["channels"][channel]['waves'], self.jsonData["channels"][channel]['waves']):
                if wave1["freq"] != wave2['freq']:
                    return True
        return False

    def getJsonData(self):
        with open(self.waveformFile) as read_file:
            data = json.load(read_file)
        read_file.close()
        return data

    def initializeSDR(self):
        for channel in self.jsonData['channels']:
            self.usrp.set_tx_rate(self.jsonData['channels'][channel]["rate"], int(channel))
            self.usrp.set_tx_freq(lib.types.tune_request(self.jsonData['channels'][channel]["centerFreq"]), int(channel))
            self.usrp.set_tx_gain(self.jsonData['channels'][channel]["gain"], int(channel))

    def initializeWaveforms(self):
        self.allWaves = [[], []]
        for channel in self.jsonData['channels']:
            dataSize = int(np.floor(self.jsonData['channels'][channel]["rate"] / self.jsonData['channels'][channel]['waveFreq']))
            for currentWave in self.jsonData['channels'][channel]['waves']:
                wave = np.array(list(map(lambda n: waveforms['sine'](n, currentWave['freq'], self.jsonData['channels'][channel]["rate"]), np.arange(dataSize, dtype=np.complex64))), dtype=np.complex64)
                (self.allWaves[int(channel)]).append(wave)

    def getWaveform(self, channel):
        wave = self.allWaves[0][0]*0
        i = 0
        for currentWave in self.jsonData['channels'][str(channel)]['waves']:
                wave = np.add(wave, currentWave['amplitude']*self.allWaves[channel][i]*np.exp(currentWave['phase']*np.pi*2j))
                i += 1
        return wave

    def getOutputWaveform(self):
        outputWave = np.stack((self.getWaveform(0), self.getWaveform(1)), axis=0)
        return outputWave
