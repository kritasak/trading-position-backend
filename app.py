import config

from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin

import hashlib
import hmac
import json
import requests

app = Flask(__name__)
CORS(app, support_credentials=True)

# API info
API_HOST = 'https://api.bitkub.com'
API_KEY = config.API_KEY
API_SECRET = bytes(config.API_SECRET, 'utf-8')

def json_encode(data):
	return json.dumps(data, separators=(',', ':'), sort_keys=True)

def sign(data):
	j = json_encode(data)
	print('Signing payload: ' + j)
	h = hmac.new(API_SECRET, msg=j.encode(), digestmod=hashlib.sha256)
	return h.hexdigest()

header = {
	'Accept': 'application/json',
	'Content-Type': 'application/json',
	'X-BTK-APIKEY': API_KEY,
}

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

@app.route('/greeting')
def greeting():
	name=request.args.get('name')
	return '<h3>Hello '+name+'</h3>'

@app.route('/history')
def history():
	sym=request.args.get('sym')

	# Code from Bitkub
	response = requests.get(API_HOST + '/api/servertime')
	ts = int(response.text)

	data = {
		'sym': sym,
		'ts': ts,
	}
	signature = sign(data)
	data['sig'] = signature

	print('Payload with signature: ' + json_encode(data))
	response = requests.post(API_HOST + '/api/market/my-order-history', headers=header, data=json_encode(data))
	info = response.json()

	return jsonify(info['result'])

app.run()