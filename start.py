#!/usr/bin/env python
"""Signal Web Gateway"""

import os
import json
import re
import subprocess
import yaml
from flask import Flask, request
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
UPLOAD_FOLDER = '/tmp'
SIGNAL_BASEDIR = os.getcwd()
JSON_MESSAGE = os.getenv('JSON_MESSAGE', 'message')

APP = Flask(__name__)

def allowed_file(filename):
    """if uploaded filename is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def remote_id_untrusted(recipient):
    """untrusted id found"""
    return json.dumps({
        'success':False,
        'error':'remote identity ' + recipient + ' is not trusted'
        }), 500, {'ContentType':'application/json'}


def send_message(message, recipient, filename=None):
    """send message via janimos textsecure binary"""
    signal_cmd = SIGNAL_BASEDIR + '/textsecure'
    signal_opts = [signal_cmd, '-to', recipient, '-message', message]
    if filename is not None:
        signal_opts.extend(['-attachment', filename])
    if re.findall(r"([a-fA-F\d]{32})", recipient):
        signal_opts.extend(['-group'])
    process = subprocess.Popen(signal_opts,
                               bufsize=0,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    process_stderr = process.communicate()[1].decode('utf-8')
    signal_stderr_regex_handlers = [
        (r'status code 413', remote_id_untrusted),
        ]
    for regex, function in signal_stderr_regex_handlers:
        if re.search(regex, process_stderr, re.IGNORECASE):
            return function(recipient)
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
        return json.dumps({
            'success':False,
            'error':'no recipient'
            }), 500, {'ContentType':'application/json'}
    return json.dumps({
        'success':False,
        'error':'no message input'
        }), 500, {'ContentType':'application/json'}


@APP.route('/<recipient>', methods=['POST'])
def json_datapost(recipient):
    """handle json post data to specific recipient url"""
    message = request.get_json()[JSON_MESSAGE]
    if message:
        return send_message(message, recipient)
    return json.dumps({
        'success':False,
        'error':'no message input'
        }), 500, {'ContentType':'application/json'}

@APP.route('/<recipient>', methods=['DELETE'])
def rekey(recipient):
    """delete existing recipient key in case the user re-installed signal"""
    if os.path.isfile(SIGNAL_BASEDIR + '/.storage/identity/remote_' + recipient):
        os.remove(SIGNAL_BASEDIR + '/.storage/identity/remote_' + recipient)
        return json.dumps({
            'success':True
            }), 200, {'ContentType':'application/json'}
    return json.dumps({
        'success':False,
        'error':'identity ' + recipient + ' not found'
        }), 500, {'ContentType':'application/json'}


@APP.route('/groups', methods=['GET'])
def list_groups():
    """list known groups"""
    groups = {}
    for filename in os.listdir(SIGNAL_BASEDIR + '/.storage/groups'):
        with open(SIGNAL_BASEDIR + '/.storage/groups/' + filename) as ymlfile:
            group = yaml.load(ymlfile)
            if group['hexid'] not in groups:
                groups.update({group['hexid']: {}})
            groups[group['hexid']].update({'name': group['name']})
    return json.dumps({
        'success':True,
        'groups': groups
        }), 200, {'ContentType':'application/json'}


@APP.route('/groups/<hexid>', methods=['GET'])
def list_group(hexid):
    """list group details"""
    group = {}
    with open(SIGNAL_BASEDIR + '/.storage/groups/' + hexid) as ymlfile:
        group = yaml.load(ymlfile)
    return json.dumps({
        'success':True,
        hexid: group
        }), 200, {'ContentType':'application/json'}
