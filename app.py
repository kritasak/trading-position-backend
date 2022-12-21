import config

from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin

from pymongo import MongoClient

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

# MongoDB info
MONGODB_USERNAME = config.MONGODB_USERNAME
MONGODB_PASSWORD = config.MONGODB_PASSWORD

client = MongoClient("mongodb+srv://" + MONGODB_USERNAME + ":" + MONGODB_PASSWORD + "@cluster0.wdsdfvv.mongodb.net/?retryWrites=true&w=majority")
db = client.senior_project
userCollection = db.users

def json_encode(data):
	return json.dumps(data, separators=(',', ':'), sort_keys=True)

def sign(data):
	j = json_encode(data)
	print('Signing payload: ' + j)
	h = hmac.new(API_SECRET, msg=j.encode(), digestmod=hashlib.sha256)
	return h.hexdigest()

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

@app.route('/greeting')
def greeting():
	name=request.args.get('name')
	return '<h3>Hello '+name+'</h3>'

# Trading History
@app.route('/history')
def history():
	sym=request.args.get('sym')

	# Code from Bitkub
	header = {
		'Accept': 'application/json',
		'Content-Type': 'application/json',
		'X-BTK-APIKEY': API_KEY,
	}
	response = requests.get(API_HOST + '/api/servertime')
	ts = int(response.text)

	data = {
		'sym': sym, #THB_ETH
		'ts': ts,
	}
	signature = sign(data)
	data['sig'] = signature

	print('Payload with signature: ' + json_encode(data))
	response = requests.post(API_HOST + '/api/market/my-order-history', headers=header, data=json_encode(data))
	info = response.json()

	return jsonify(info['result'])

# Sign Up
@app.route('/adduser')
def addUser():
	email=request.args.get('email')
	password=request.args.get('password')

	infoDict = {
		"email": email,
		"password": password,
		"api": {}
	}
	user = userCollection.find_one({"email": email})
	if user == None:
		userCollection.insert_one(infoDict)
		return '<h1>Successfully added</h1>'
	else:
		return '<h1>Email already exists</h1>'

# Log in
@app.route('/getinfo')
def getInfo():
	email=request.args.get('email')
	password=request.args.get('password')

	user = userCollection.find_one({"email": email})
	del user["_id"]
	if user == None:
		return '<h1>Email does not exist</h1>'
	else:
		collectedPassword = user["password"]
		if password == collectedPassword:
			return jsonify(user)
		else:
			return '<h1>Password is incorrect</h1>'

# Change Password
@app.route('/changepassword')
def changePassword():
	email=request.args.get('email')
	oldPassword = request.args.get('old')
	newPassword = request.args.get('new')

	user = userCollection.find_one({"email": email})
	if oldPassword == user["password"]:
		userCollection.update_one({"email": email}, {"$set": {"password": newPassword}})
		return '<h1>Password is updated</h1>'
	else:
		return '<h1>Password is incorrect</h1>'

# Add API
@app.route('/addapi')
def addAPI():
	email=request.args.get('email')
	exchange=request.args.get('exchange')
	key=request.args.get('key')
	secret=request.args.get('secret')

	user = userCollection.find_one({"email": email})
	updateInfo = dict()
	updateInfo['api'] = user['api']

	updateInfo['api'][exchange] = {'API_KEY': key, 'API_SECRET': secret}
	userCollection.update_one({"email": email}, {"$set": updateInfo})
	return '<h1>Add API Sucessful</h1>'

# Edit API
@app.route('/editapi')
def editAPI():
	email=request.args.get('email')
	exchange=request.args.get('exchange')
	key=request.args.get('key')
	secret=request.args.get('secret')

	user = userCollection.find_one({"email": email})
	updateInfo = dict()
	updateInfo['api'] = user['api']

	updateInfo['api'][exchange] = {'API_KEY': key, 'API_SECRET': secret}
	userCollection.update_one({"email": email}, {"$set": updateInfo})
	return '<h1>Edit API Sucessful</h1>'

# Delete API
@app.route('/deleteapi')
def deleteAPI():
	email=request.args.get('email')
	exchange=request.args.get('exchange')

	user = userCollection.find_one({"email": email})
	updateInfo = dict()
	updateInfo['api'] = user['api']

	del updateInfo['api'][exchange]
	userCollection.update_one({"email": email}, {"$set": updateInfo})
	return '<h1>Delete API Sucessful</h1>'

app.run()