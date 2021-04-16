import json
import numpy as np
import random
import os
import math


waveforms = {
    "sine": lambda n, tone_offset, rate: np.exp(n * 2j * np.pi * tone_offset / rate)
}


class WaveformManager(object):

    def __init__(self, waveformFile):
        self.waveformFile = waveformFile
        self.jsonData = self.getJsonData()
        self.initializeWaveforms()
        self.modTime = os.stat(self.waveformFile).st_mtime

    def changeFile(self, file):
        self.waveformFile = file
        self.initializeWaveforms()
        self.jsonData = self.getJsonData()
        self.modTime = os.stat(self.waveformFile).st_mtime

    def getTotalPower(self, channel):
        # power out of SDR with 4db attenuator and 0 gain with waveforms at 1
        zeroPower = -20
        amplifier = 34
        sumOfWaveforms = 10*math.log10(sum(self.getAmplitudes(channel)))
        return zeroPower+amplifier+sumOfWaveforms+self.jsonData['channels'][str(channel)]['gain']

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

    def getJsonData(self):
        with open(self.waveformFile) as read_file:
            data = json.load(read_file)
        read_file.close()
        return data

    def updateJsonData(self, jsonData):
        self.jsonData = jsonData

    def saveJsonData(self):
        with open(self.waveformFile, 'w') as outfile:
            json.dump(self.jsonData, outfile, indent=4, separators=(',', ': '))
        outfile.close()

    def randomizePhases(self, channel):
        lines = len(self.jsonData['channels'][str(channel)]['waves'])
        ampThreshold = 4*sum(self.getAmplitudes(channel))/lines
        maxAmp = ampThreshold + 1
        while(maxAmp > ampThreshold):
            newPhases = [random.random() for _ in range(lines)]
            self.changePhases(channel, newPhases)
            maxAmp = self.getMaxAmp(channel)
            print (maxAmp)
        self.updateJsonData(self.jsonData)

    def getMaxAmp(self, channel):
        wave = self.getWaveform(channel)
        return np.max(np.real(wave), axis=0) - np.min(np.real(wave), axis=0)

    def getAmplitudes(self, channel):
        amplitudes = []
        for wave in self.jsonData['channels'][str(channel)]['waves']:
            amplitudes.append(wave['amplitude'])
        return amplitudes

    def getPhases(self, channel):
        phases = []
        for wave in self.jsonData['channels'][str(channel)]['waves']:
            phases.append(wave['phase'])
        return phases

    def changeAmplitudes(self, channel, amplitudes):
        i = 0
        for wave in self.jsonData['channels'][str(channel)]['waves']:
            wave['amplitude'] = amplitudes[i]
            i += 1
        return True

    def changePhases(self, channel, phases):
        i = 0
        for wave in self.jsonData['channels'][str(channel)]['waves']:
            wave['phase'] = phases[i]
            i += 1
        return True

    def makeWaveform(self, freqsList, templateFile):
        data = {}
        with open(templateFile) as read_file:
            data = json.load(read_file)
        print (len(freqsList))
        for channel in range(len(freqsList)):
            for freq in freqsList[channel]:
                data['channels'][str(channel)]['waves'].append({"freq": freq, "amplitude": .2, "phase": 0})
        self.updateJsonData(data)
        self.initializeWaveforms()
        self.randomizePhases(0)
        self.randomizePhases(1)
        self.saveJsonData()

    def makeLatticeWaveform(self, lines, spacing, templateFile):
        freqs = np.arange(-(lines-1)/2.0*spacing, ((lines-1)/2.0+1)*spacing, spacing)
        freqsList = [freqs, freqs]
        print (freqsList)
        self.makeWaveform(freqsList, templateFile)
        self.changeAmplitudes(1, self.getAmplitudes(0))
        self.changePhases(1, self.getPhases(0))
