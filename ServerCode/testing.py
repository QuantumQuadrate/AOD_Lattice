from Tools.WaveformMonitor import WaveformMonitor


waveMan = WaveformMonitor("Resources/waveformArguments.json")
jsonData = waveMan.getJsonData()
print len(jsonData['channels'])
for channel in jsonData['channels']:
    print jsonData[channel]["rate"]
    print channel[channel]["centerFreq"]
    print channel[channel]["gain"]
#
# st_args = lib.usrp.stream_args("fc32", "sc16")
# st_args.channels = channels
# streamer = usrp.get_tx_stream(st_args)
# buffer_samps = streamer.get_max_num_samps()
# metadata = lib.types.tx_metadata()
