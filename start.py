#!/usr/bin/env python
"""Signal Web Gateway"""

import os
import json
import re
from subprocess import Popen
from flask import Flask, request
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
UPLOAD_FOLDER = '/tmp'
SIGNAL_BASEDIR = '/signal'
JSON_MESSAGE = os.getenv('JSON_MESSAGE', 'message')

APP = Flask(__name__)

def allowed_file(filename):
    """if uploaded filename is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def send_message(message, recipient, filename=None):
    """send message via janimos textsecure binary"""
    signal_cmd = SIGNAL_BASEDIR + '/textsecure'
    signal_opts = [signal_cmd, '-to', recipient, '-message', message]
    if filename is not None:
        signal_opts.extend(['-attachment', filename])
    if re.findall(r"([a-fA-F\d]{32})", recipient):
        signal_opts.extend(['-group'])
    Popen(signal_opts)
    return json.dumps({'success':True}), 200, {'ContentType':'application/json'}

@APP.route('/', methods=['POST'])
def multipart_formpost():
    """handle multiform requests with possible file uploads"""
    message = request.form.get('message')
    if message:
        recipient = request.form.get('to', False)
        if recipient:
            file = request.files.get('file', False)
            if file:
                if allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(UPLOAD_FOLDER, filename))
                    return send_message(message, recipient, os.path.join(UPLOAD_FOLDER, filename))
            return send_message(message, recipient)
        return json.dumps({'success':False, 'error':'no recipient'}), 500, {'ContentType':'application/json'}
    return json.dumps({'success':False, 'error':'no message input'}), 500, {'ContentType':'application/json'}


@APP.route('/<recipient>', methods=['POST'])
def json_datapost(recipient):
    """handle json post data to specific recipient url"""
    message = request.get_json()[JSON_MESSAGE]
    if message:
        return send_message(message, recipient)
    return json.dumps({'success':False, 'error':'no message input'}), 500, {'ContentType':'application/json'}

@APP.route('/<recipient>', methods=['DELETE'])
def rekey(recipient):
    """delete existing recipient key in case the user re-installed signal"""
    if os.path.isfile(SIGNAL_BASEDIR + '/.storage/identity/remote_' + recipient):
        os.remove(SIGNAL_BASEDIR + '/.storage/identity/remote_' + recipient)
        return json.dumps({'success':True}), 200, {'ContentType':'application/json'}
    else:
        return json.dumps({'success':False, 'error':'identity ' + recipient + ' not found'}), 500, {'ContentType':'application/json'}
