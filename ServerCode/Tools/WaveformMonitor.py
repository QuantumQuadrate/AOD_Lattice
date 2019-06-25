import json
import numpy as np
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
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

    def __init__(self, waveformFile):
        self.waveformFile = waveformFile
        self.jsonData = self.getJsonData()
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
        return zeroPower+amplifier+sumOfWaveforms+self.jsonData['Gain']

    def getAmplitudes(self, channel):
        amplitudes = []
        for wave in self.jsonData['Waves'][channel]:
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

    def getJsonData(self):
        with open(self.waveformFile) as read_file:
            data = json.load(read_file)
        read_file.close()
        return data

    def initializeWaveforms(self):
        dataSize = int(np.floor(self.jsonData["Rate"] / self.jsonData['waveFreq']))
        self.allWaves = []
        for channel in self.jsonData["Channels"]:
            self.allWaves.append([])
            for currentWave in self.jsonData['Waves'][channel]:
                wave = np.array(list(map(lambda n: waveforms['sine'](n, currentWave['freq'], self.jsonData["Rate"]), np.arange(dataSize, dtype=np.complex64))), dtype=np.complex64)
                (self.allWaves[channel]).append(wave)

    def getWaveform(self, channel):
        wave = self.allWaves[0][0]*0
        i = 0
        for currentWave in self.jsonData['Waves'][channel]:
                wave = np.add(wave, currentWave['amplitude']*self.allWaves[channel][i]*np.exp(currentWave['phase']*np.pi*2j))
                i += 1
        return wave

    def getOutputWaveform(self):
        outputWave = np.stack((self.getWaveform(0), self.getWaveform(1)), axis=0)
        return outputWave
