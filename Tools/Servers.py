from flask import Flask, jsonify, Response, render_template, request
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import io
import json


class SDRServer(object):

    def runServer(self, waveManager, trapFeedback):
        app = Flask(__name__, static_url_path='/static')

        @app.route('/', methods=['GET'])
        def index():
            return render_template('JSONeditor.html')

        @app.route('/waveforms.png', methods=['GET'])
        def plot_waveforms():
            fig = create_figure()
            output = io.BytesIO()
            FigureCanvas(fig).print_png(output)
            return Response(output.getvalue(), mimetype='image/png')

        def create_figure():
            waves = waveManager.getOutputWaveform()
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
                print (content)
            if action == "update":
                waveManager.updateJsonData(content)
                waveManager.initializeWaveforms()
                waveManager.saveJsonData()
            elif action == 'randomizePhases':
                waveManager.updateJsonData(content)
                waveManager.initializeWaveforms()
                waveManager.randomizePhases(int(channel))
                waveManager.saveJsonData()
            elif action == 'resetAmplitudes':
                waveManager.updateJsonData(content)
                waveManager.changeAmplitudes
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
                trapFeedback.stopFeedback()
            else:
                return 'error'
            return ''

        @app.route('/feedbackControl/<channel>')
        def feedbackControl(channel):
            trapFeedback.setpoint = int(request.args.get('setpoint'))
            trapFeedback.P = float(request.args.get('P'))
            trapFeedback.I = float(request.args.get('I'))
            trapFeedback.D = float(request.args.get('D'))
            trapFeedback.initializePIDs(channel)
            return "Done"

        app.run(host='0.0.0.0', debug=False, use_reloader=False, port=5050)


class CameraServer(object):

    def runServer(self, peakTool):
        app = Flask(__name__, static_url_path='/static')

        @app.route('/', methods=['GET'])
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
                    #Figure was not returned due to error ... continue through loop
                    if figure is None:
                        continue
                    FigureCanvas(figure).print_png(output)
                    yield (b'--frame\r\n' b'Content-Type: image/png\r\n\r\n' + output.getvalue() + b'\r\n')
            self.running = True
            return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

        @app.route('/streamControl')
        def streamControl():
            command = request.args.get('command')
            if command == "STOP":
                self.running = False
            if command == "START":
                self.running = True
            return "Done"

        @app.route('/cameraControl/<action>')
        def cameraControl(action):
            if action == "exposureTime":
                peakTool.camera.set_exposure(float(request.args.get('exposureTime')) * 1000)
            if action == "prominence":
                peakTool.prominence = int(request.args.get('prominence'))
            else:
                return 'error'
            return ''

        @app.route('/peakData')
        def peakData():
            return json.dumps(peakTool.measureIntensities())

        app.run(host='0.0.0.0', debug=False, use_reloader=False, port=5050)
