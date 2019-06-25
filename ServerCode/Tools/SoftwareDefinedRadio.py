import uhd
from uhd import libpyuhd as lib
import threading


def streamWaveform(streamer, wave, metadata):
    t = threading.currentThread()
    while getattr(t, "run", True):
        streamingWave = getattr(t, "wave", wave)
        streamer.send(streamingWave, metadata)


class SoftwareDefinedRadio(object):

        def __init__(self, waveMonitor):
            self.waveMonitor = waveMonitor

        def initializeSDR(self):
            jsonData = self.waveMonitor.getJsonData()
            rate = jsonData['Rate']
            gain = jsonData['Gain']
            centerFreq = jsonData['CenterFreq']
            channels = jsonData['Channels']
            # type=x300,addr=192.168.30.2,second_addr=192.168.40.2
            usrp = uhd.usrp.MultiUSRP('')

            for chan in channels:
                usrp.set_tx_rate(rate, chan)
                usrp.set_tx_freq(lib.types.tune_request(centerFreq), chan)
                usrp.set_tx_gain(gain, chan)
            st_args = lib.usrp.stream_args("fc32", "sc16")
            st_args.channels = channels
            self.streamer = usrp.get_tx_stream(st_args)
            self.buffer_samps = self.streamer.get_max_num_samps()
            self.metadata = lib.types.tx_metadata()

        def startStreamingWaveform(self):
            if self.waveMonitor.getTotalPower() < 30:
                wave = self.waveMonitor.getOutputWaveform()
                self.stream = threading.Thread(target=streamWaveform, args=[self.streamer, wave, self.metadata])
                self.stream.start()
            else:
                print "WARNING: TOO MUCH POWER"

        def startMonitor(self):
            self.waveMonitor.startMonitor(self.stream)

        def updateWaveform(self):
            self.stream.wave = self.waveMonitor.getOutputWaveform()
            self.stream.isAlive()
