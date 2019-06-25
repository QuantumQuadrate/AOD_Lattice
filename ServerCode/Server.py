from flask import Flask, jsonify, Response, render_template, request
from Tools.WaveformMonitor import WaveformMonitor
from Tools.WaveformManager import WaveformManager
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import io
import json


class Server(object):

    def runServer(self, waveMon, waveManager):

        app = Flask(__name__, static_url_path='/static')
        @app.route('/', methods=['GET'])
        def index():
            return render_template('JSONeditor.html')

        @app.route('/trapPage', methods=['GET'])
        def trapPage():
            return render_template('trapPage.html')

        @app.route('/plot.png')
        def plot_png():
            fig = create_figure()
            output = io.BytesIO()
            FigureCanvas(fig).print_png(output)
            return Response(output.getvalue(), mimetype='image/png')

        def create_figure():
            waves = waveMon.getOutputWaveform()
            fig = Figure()
            axis = fig.add_subplot(1, 1, 1)
            for wave in waves:
                axis.plot(wave)
            return fig

        @app.route('/action/<action>/<channel>', methods=['POST', 'GET'])
        def action(action, channel):
            if request.method == 'POST':
                content = request.data
                content = json.loads(content)
                print content
            if action == "update":
                waveManager.updateJsonData(content)
                waveManager.saveJsonData()
            elif action == 'randomizePhases':
                waveManager.updateJsonData(content)
                waveManager.randomizePhases(int(channel))
                waveManager.saveJsonData()
            elif action == 'getPower':
                waveManager.getJsonData()
                return str(int(waveManager.getTotalPower(int(channel))*100)/100.0)
            elif action == 'getWaveformArguments':
                return jsonify(waveManager.getJsonData())
            else:
                return 'error'
            return ''

        app.run(host='0.0.0.0', debug=True, use_reloader=True, port=80)


waveManager = WaveformManager("Resources/waveformArguments.json")
waveMonitor = WaveformMonitor("Resources/waveformArguments.json")
Server = Server()
Server.runServer(waveMonitor, waveManager)
