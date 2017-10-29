from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash

from utils import LOGGER
from pyambient import AmbientControl

app = Flask(__name__)
LOGGER.setLevel(1)

AMBC_CONFIG = "ambient.config.xml"
AMBC        = AmbientControl(AMBC_CONFIG)
AMB_ID      = -1

@app.route('/play', methods=['POST', 'GET'])
def play():
    global AMB_ID
    if request.method == 'POST':
        try:
            AMB_ID = request.form['id']
            AMBC.switch(AMB_ID)
            AMBC.get().start()
        except Exception as e:
            AMB_ID = -1
            LOGGER.logError(e)
    return redirect(url_for('.index'))

@app.route('/stop', methods=['POST', 'GET'])
def stop():
    global AMB_ID
    if request.method == 'POST' and AMB_ID != -1:
        AMBC.get().stop()
        AMB_ID = -1
    return redirect(url_for('.index'))


@app.route('/')
def index():
    global AMB_ID

    fmt = dict()
    fmt["id_playing"] = AMB_ID

    ambients = AMBC.getAmbients()
    for ambid in ambients:
        fmt["title"+str(ambid)] = ambients[ambid].getName()

    return render_template('index.html', **fmt)
