import os
import json
import re
from subprocess import Popen
from distutils.util import strtobool
from flask import Flask, request, redirect, url_for
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
UPLOAD_FOLDER = '/tmp'

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def send_message(message, recipient, group, filename=None):
    signal_cmd = "/signal/textsecure"
    signal_opts = [signal_cmd, '-to', recipient, '-message', message]
    if filename is not None:
        signal_opts.extend(['-attachment', filename])
    if group:
        signal_opts.extend(['-group'])
    Popen(signal_opts)
    return json.dumps({'success':True}), 200, {'ContentType':'application/json'}

@app.route('/', methods=['POST','GET'])
def get_message():
    if request.method == 'POST':
        group = False
        message = request.form.get('message')
        if message:
            recipient = request.form.get('to')
            if recipient:
                if re.findall(r"([a-fA-F\d]{32})", recipient):
                    group = True
                try:
                    file = request.files['file']
                    if file:
                        if allowed_file(file.filename):
                            filename=secure_filename(file.filename)
                            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                            return send_message(message, recipient, group, os.path.join(app.config['UPLOAD_FOLDER'], filename))
                except:
                    return send_message(message, recipient, group)
            else:
                return json.dumps({'success':False, 'error':'no recipient'}), 500, {'ContentType':'application/json'}
        else:
            return json.dumps({'success':False, 'error':'no message input'}), 500, {'ContentType':'application/json'}
    return json.dumps({'success':False}), 500, {'ContentType':'application/json'}
