import uhd
from uhd import libpyuhd as lib
import threading
from Tools.WaveformMonitor import WaveformMonitor
import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class EventHandler(FileSystemEventHandler):
    def __init__(self, streamingThread, waveMan):
        super(EventHandler, self).__init__()
        self.streamingThread = streamingThread
        self.waveMan = waveMan

    def on_any_event(self, event):
        if waveMan.compareFreqs(self.waveMan.getJsonData()):
            result = None
            while result is None:
                try:
                    self.waveMan.jsonData = self.waveMan.getJsonData()
                    result = 1
                except:
                    pass
            self.waveMan.initializeWaveforms()
        else:
            result = None
            while result is None:
                try:
                    self.waveMan.jsonData = self.waveMan.getJsonData()
                    result = 1
                except:
                    pass
        self.waveMan.initializeSDR()
        self.streamingThread.wave = self.waveMan.getOutputWaveform()


def streamWaveform(streamer, wave, metadata):
    t = threading.currentThread()
    while getattr(t, "run", True):
        streamingWave = getattr(t, "wave", wave)
        streamer.send(streamingWave, metadata)


usrp = uhd.usrp.MultiUSRP('')
waveMan = WaveformMonitor("Resources/waveformArguments.json", usrp)
waveMan.initializeWaveforms()
jsonData = waveMan.getJsonData()
waveMan.initializeSDR()

st_args = lib.usrp.stream_args("fc32", "sc16")
st_args.channels = range(len(jsonData['channels']))
streamer = usrp.get_tx_stream(st_args)
buffer_samps = streamer.get_max_num_samps()
metadata = lib.types.tx_metadata()

wave = waveMan.getOutputWaveform()

stream = threading.Thread(target=streamWaveform, args=(streamer, wave, metadata))
stream.start()


path = os.path.abspath("Resources")
event_handler = EventHandler(stream, waveMan)
observer = Observer()
observer.schedule(event_handler, path)
observer.start()
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    observer.stop()
observer.join()
