from flask import Flask, jsonify, Response, render_template, request
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import io
import json


class Server(object):

    def runServer(self, waveMon, waveManager, peakTool, trapFeedback):
        app = Flask(__name__, static_url_path='/static')


        @app.route('/', methods=['GET'])
        def index():
            return render_template('JSONeditor.html')

        @app.route('/trapPage', methods=['GET'])
        def trapPage():
            return render_template('trapPage.html')

        @app.route('/plot.png')
        def plot_png():
            self.running = False
            top = int(request.args.get('top'))
            bottom = int(request.args.get('bottom'))
            left = int(request.args.get('left'))
            right = int(request.args.get('right'))
            rotation = int(request.args.get('rotation'))
            cutSizeY = int(request.args.get('cutSizeY'))
            cutSizeX = int(request.args.get('cutSizeX'))

            def generate():
                while self.running:
                    output = io.BytesIO()
                    figure = peakTool.getPlot(top, bottom, left, right, rotation, cutSizeX, cutSizeY)
                    FigureCanvas(figure).print_png(output)
                    yield (b'--frame\r\n' b'Content-Type: image/png\r\n\r\n' + output.getvalue() + b'\r\n')
            self.running = True
            return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

        @app.route('/streamControl')
        def stopStream():
            command = request.args.get('command')
            if command == "STOP":
                self.running = False
            if command == "START":
                self.running = True
            return "Done"

        @app.route('/peakData')
        def peakData():
            return str(peakTool.measureIntensities())

        @app.route('/waveforms.png', methods=['GET'])
        def plot_waveforms():
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
                waveManager.initializeWaveforms()
                waveManager.saveJsonData()
            elif action == 'randomizePhases':
                waveManager.updateJsonData(content)
                waveManager.initializeWaveforms()
                waveManager.randomizePhases(int(channel))
                waveManager.saveJsonData()
            elif action == 'getPower':
                waveManager.getJsonData()
                return str(int(waveManager.getTotalPower(int(channel))*100)/100.0)
            elif action == 'getWaveformArguments':
                return jsonify(waveManager.getJsonData())
            elif action == 'startFeedback':
                trapFeedback.initializePIDs(int(channel))
                trapFeedback.startFeedback(int(channel))
            elif action == 'stopFeedback':
                trapFeedback.stopFeedback(int(channel))
            else:
                return 'error'
            return ''

        app.run(host='10.140.178.187', debug=False, use_reloader=False, port=80)
