from Tools.WaveformManager import WaveformManager
from Tools.WaveformMonitor import WaveformMonitor
from Tools.SoftwareDefinedRadio import SoftwareDefinedRadio

waveManager = WaveformManager("Resources/waveformArguments.json")
waveManager.makeLatticeWaveform(5, 7e5, "Resources/waveformTemplate.json")
waveMonitor = WaveformMonitor("Resources/waveformArguments.json")

SDR = SoftwareDefinedRadio(waveMonitor)
SDR.initializeSDR()
SDR.startMonitor()
