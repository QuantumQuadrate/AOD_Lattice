from Tools.WaveformManager import WaveformManager

waveManager = WaveformManager("Resources/waveformArguments.json")
freqs = [[-1e6, 1e6], [0]]
waveManager.makeWaveform(freqs, "Resources/waveformTemplate.json")
waveManager.saveJsonData()
print waveManager.getJsonData()
