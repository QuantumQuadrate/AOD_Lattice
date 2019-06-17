import uhd
from uhd import libpyuhd as lib
import json
import time
import threading
import os
import numpy as np

allWaves = []


class SoftwareDefinedRadio(object):

        def initializeSDR(self, jsonData):
            rate = jsonData['Rate']
            gain = jsonData['Gain']
            centerFreq = jsonData['CenterFreq']
            channels = jsonData['Channels']
            usrp = uhd.usrp.MultiUSRP('')

            for chan in channels:
                usrp.set_tx_rate(rate, chan)
                usrp.set_tx_freq(lib.types.tune_request(centerFreq), chan)
                usrp.set_tx_gain(gain, chan)
            st_args = lib.usrp.stream_args("fc32", "sc16")
            st_args.channels = channels
            streamer = usrp.get_tx_stream(st_args)
            self.buffer_samps = streamer.get_max_num_samps()
            self.metadata = lib.types.tx_metadata()

        def initializeWaveforms(self, jsonData):
            allWaves = self.generateWaveforms(jsonData)

        def streamWaveform(streamer, wave):
            t = threading.currentThread()
            while getattr(t, "run", True):
                wave = getattr(t, "wave", wave)
                streamer.send(wave, self.metadata)


        def generateOutputWaveform(allWaves, jsonData):
            waves = []
            for channel in range(len(jsonData['Channels'])):
                wave = allWaves[0][0]*0
                i = 0
                for currentWave in jsonData['Waves'][channel]:
                        wave = np.add(wave, currentWave['amplitude']*allWaves[i]*np.exp(currentWave['phase']*np.pi*2j))
                        i += 1
                waves.append(wave)
            outputWave = waves[0]
            if len(waves) == 2:
                outputWave = np.stack((waves[0], waves[1]), axis=0)
            return outputWave


        def generateWaveforms(jsonData):
            dataSize = int(np.floor(jsonData["Rate"] / jsonData['waveFreq']))
            outputWaveform = []
            for channel in range(len(jsonData['Channels'])):
                for currentWave in jsonData['Waves'][channel]:
                    wave = np.array(list(map(lambda n: waveforms['sine'](n, currentWave['freq'], jsonData["Rate"]), np.arange(dataSize, dtype=np.complex64))), dtype=np.complex64)
                    outputWaveform.append(wave)
            allWave
            return outputWaveform


        def main():

            modTimeOrig = os.stat(waveformFile).st_mtime
            stream = threading.Thread(target=streamWaveform, args=(streamer, wave, metadata))
            stream.start()
            while True:
                time.sleep(.05)
                modTime = os.stat(waveformFile).st_mtime
                if modTime != modTimeOrig:
                    print "changed"
                    try:
                        with open(waveformFile) as read_file:
                            data = json.load(read_file)
                        read_file.close()
                        newWave = generateOutputWaveform(allWaves, data)
                        stream.wave = newWave
                        stream.isAlive()
                        modTimeOrig = modTime
                    except:
                        time.sleep(.005)
