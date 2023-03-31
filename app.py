import config

from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin

from pymongo import MongoClient

from binance.client import Client
from datetime import datetime

import hashlib
import hmac
import json
import requests

app = Flask(__name__)
CORS(app, support_credentials=True)

# Bitkub API info
API_HOST = 'https://api.bitkub.com'
BITKUB_API_KEY = config.BITKUB_API_KEY
BITKUB_API_SECRET = config.BITKUB_API_SECRET
#BITKUB_API_SECRET = bytes(config.BITKUB_API_SECRET, 'utf-8')

# Binance API info
BINANCE_API_KEY = config.BINANCE_API_KEY
BINANCE_API_SECRET = config.BINANCE_API_SECRET

# MongoDB info
MONGODB_USERNAME = config.MONGODB_USERNAME
MONGODB_PASSWORD = config.MONGODB_PASSWORD

client = MongoClient("mongodb+srv://" + MONGODB_USERNAME + ":" + MONGODB_PASSWORD + "@cluster0.wdsdfvv.mongodb.net/?retryWrites=true&w=majority")
db = client.senior_project
userCollection = db.users

def json_encode(data):
	return json.dumps(data, separators=(',', ':'), sort_keys=True)

def sign(data, secret):
	byteSecret = bytes(secret, 'utf-8')
	j = json_encode(data)
	print('Signing payload: ' + j)
	h = hmac.new(byteSecret, msg=j.encode(), digestmod=hashlib.sha256)
	return h.hexdigest()

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

@app.route('/greeting')
def greeting():
	name=request.args.get('name')
	return '<h3>Hello '+name+'</h3>'

# Creating Token
@app.route('/token', methods=["POST", "GET"])
def token():
	if request.method == "POST":
		data = request.get_json()
		# data = json.loads(request.data)
		print(data)
		tokenValue = {"token": "test123"}
		return jsonify(tokenValue)
	elif request.method == "GET":
		tokenValue = {"token": "test123"}
		return jsonify(tokenValue)

# Trading History
@app.route('/history', methods=["POST", "GET"])
def history():
	if request.method == "POST":
		data = request.get_json()
		email = data["email"]
		exchange = data["exchange"]
		sym = data["sym"]
		user = userCollection.find_one({"email": email})
		if exchange in user["api"].keys():
			if exchange == "bitkub":
				# Code from Bitkub
				header = {
					'Accept': 'application/json',
					'Content-Type': 'application/json',
					'X-BTK-APIKEY': user["api"][exchange]["API_KEY"],
				}
				response = requests.get(API_HOST + '/api/servertime')
				ts = int(response.text)

				data = {
					'sym': sym, #THB_ETH
					'ts': ts,
				}
				signature = sign(data, user["api"][exchange]["API_SECRET"])
				data['sig'] = signature

				print('Payload with signature: ' + json_encode(data))
				response = requests.post(API_HOST + '/api/market/my-order-history', headers=header, data=json_encode(data))
				info = response.json()
				if "result" in info.keys():
					historyData = []
					for oneInfo in info["result"]:
						historyData.append({"date": oneInfo["date"], "side": oneInfo["side"], "price": oneInfo["rate"], "amountBase": oneInfo["amount"], "amountQuote": str(round(float(oneInfo["rate"])*float(oneInfo["amount"]), 4))})
					return jsonify(historyData)
				else:
					return jsonify([])
			elif exchange == "binance":
				client = Client(user["api"][exchange]["API_KEY"], user["api"][exchange]["API_SECRET"])
				info = client.get_my_trades(symbol=sym) #BTCUSDT
				historyData = []
				for oneInfo in info:
					side = ""
					if oneInfo["isBuyer"]:
						side = "buy"
					else:
						side = "sell"
					historyData.append({"date": datetime.fromtimestamp(int(oneInfo["time"]/1000)).strftime("%Y-%m-%d %H:%M:%S"), "side": side, "price": oneInfo["price"], "amountBase": oneInfo["qty"], "amountQuote": oneInfo["quoteQty"]})
				return jsonify(historyData)

		else:
			return jsonify([])

	elif request.method == "GET":
		sym=request.args.get('sym')
		exchange=request.args.get('exchange')

		if exchange == "bitkub":
			# Code from Bitkub
			header = {
				'Accept': 'application/json',
				'Content-Type': 'application/json',
				'X-BTK-APIKEY': BITKUB_API_KEY,
			}
			response = requests.get(API_HOST + '/api/servertime')
			ts = int(response.text)

			data = {
				'sym': sym, #THB_ETH
				'ts': ts,
			}
			signature = sign(data, BITKUB_API_SECRET)
			data['sig'] = signature

			print('Payload with signature: ' + json_encode(data))
			response = requests.post(API_HOST + '/api/market/my-order-history', headers=header, data=json_encode(data))
			info = response.json()
			return jsonify(info['result'])
		elif exchange == "binance":
			client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)
			info = client.get_my_trades(symbol=sym) #BTCUSDT
			return jsonify(info)
		else:
			return '<h3>Exchange is wrong!</h3>'

# Balances
@app.route('/balance', methods=["POST", "GET"])
def balance():
	if request.method == "POST":
		data = request.get_json()
		email = data["email"]
		exchange = data["exchange"]
		user = userCollection.find_one({"email": email})
		if exchange in user["api"].keys():
			if exchange == "bitkub":
				# Code from Bitkub
				header = {
					'Accept': 'application/json',
					'Content-Type': 'application/json',
					'X-BTK-APIKEY': user["api"][exchange]["API_KEY"],
				}
				response = requests.get(API_HOST + '/api/servertime')
				ts = int(response.text)

				data = {
					'ts': ts,
				}
				signature = sign(data, user["api"][exchange]["API_SECRET"])
				data['sig'] = signature

				print('Payload with signature: ' + json_encode(data))
				response = requests.post(API_HOST + '/api/market/balances', headers=header, data=json_encode(data))
				info = response.json()
				if "result" in info.keys():
					balanceData = []
					for keys, values in info["result"].items():
						if values["available"] > 0:
							balanceData.append({"asset": keys, "free": values["available"]})
					return jsonify(balanceData)
				else:
					return jsonify([])
			elif exchange == "binance":
				client = Client(user["api"][exchange]["API_KEY"], user["api"][exchange]["API_SECRET"])
				info = client.get_account()
				if "balances" in info.keys():
					balanceData = []
					for oneInfo in info["balances"]:
						if(float(oneInfo['free'])>0):
							balanceData.append({"asset": oneInfo["asset"], "free": oneInfo["free"]})
					return jsonify(balanceData)
				else:
					return jsonify([])

		else:
			return jsonify([])

	elif request.method == "GET":
		exchange = request.args.get('exchange')
		if exchange == "bitkub":
			data = {"bitkub": True}
			return jsonify(data)
		elif exchange == "binance":
			data = {"binance": True}
			return jsonify(data)
		else:
			return jsonify({"data": {}})

# Graph (Bitkub)
@app.route('/graph')
def graph():
	response = requests.get(API_HOST + '/api/servertime')
	ts = int(response.text)
	PARAMS = {
		'symbol': "BTC_THB",
		'resolution': "240",
		'from': 1661124427,
		'to': ts
	}

	info = requests.get(API_HOST + '/tradingview/history', params=PARAMS)

	return info.json()

# Sign Up
@app.route('/adduser', methods=["POST", "GET"])
def addUser():
	if request.method == "POST":
		data = request.get_json()
		email = data["email"]
		password = data["password"]

		infoDict = {
			"email": email,
			"password": password,
			"api": {}
		}
		user = userCollection.find_one({"email": email})
		if user == None:
			userCollection.insert_one(infoDict)
			result = {"result": "Sucessfully Sign Up"}
			return jsonify(result)
		else:
			result = {"result": "Email already exists"}
			return jsonify(result)

	elif request.method == "GET":
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
			return '<h1>Successfully Sign Up</h1>'
		else:
			return '<h1>Email already exists</h1>'

# Log in
@app.route('/checklogin', methods=["POST", "GET"])
def checkLogin():
	if request.method == "POST":
		data = request.get_json()
		email = data["email"]
		password = data["password"]

		user = userCollection.find_one({"email": email})
		if user == None:
			result = {"result": "Email does not exist"}
			return jsonify(result)
		else:
			collectedPassword = user["password"]
			if password == collectedPassword:
				result = {"result": "Successfully Log In"}
				return jsonify(result)
			else:
				result = {"result": "Password is incorrect"}
				return jsonify(result)

	elif request.method == "GET":
		email=request.args.get('email')
		password=request.args.get('password')

		user = userCollection.find_one({"email": email})
		if user == None:
			return '<h1>Email does not exist</h1>'
		else:
			del user["_id"]
			collectedPassword = user["password"]
			if password == collectedPassword:
				return jsonify(user)
			else:
				return '<h1>Password is incorrect</h1>'

# Get Info
@app.route('/getinfo', methods=["POST", "GET"])
def getInfo():
	if request.method == "POST":
		data = request.get_json()
		print(data)
		email = data["email"]

		user = userCollection.find_one({"email": email})
		if user == None:
			return jsonify({})
		else:
			del user["_id"]
			return jsonify(user)

	elif request.method == "GET":
		email=request.args.get('email')

		user = userCollection.find_one({"email": email})
		if user == None:
			return '<h1>Email does not exist</h1>'
		else:
			del user["_id"]
			return jsonify(user)

# Change Password
@app.route('/changepassword', methods=["POST", "GET"])
def changePassword():
	if request.method == "POST":
		data = request.get_json()
		email = data["email"]
		oldPassword = data["old"]
		newPassword = data["new"]

		user = userCollection.find_one({"email": email})
		del user["_id"]
		if oldPassword == user["password"]:
			userCollection.update_one({"email": email}, {"$set": {"password": newPassword}})
			user["password"] = newPassword
			return jsonify(user)
		else:
			return jsonify(user)

	elif request.method == "GET":
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
@app.route('/addapi', methods=["POST", "GET"])
def addAPI():
	if request.method == "POST":
		data = request.get_json()
		email = data["email"]
		exchange = data["exchange"]
		publicKey = data["publicKey"]
		secretKey = data["secretKey"]

		user = userCollection.find_one({"email": email})
		del user["_id"]
		updateInfo = dict()
		updateInfo['api'] = user['api']

		updateInfo['api'][exchange] = {'API_KEY': publicKey, 'API_SECRET': secretKey}
		user['api'] = updateInfo['api']
		userCollection.update_one({"email": email}, {"$set": updateInfo})
		return jsonify(user)

	elif request.method == "GET":
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
@app.route('/editapi', methods=["POST", "GET"])
def editAPI():
	if request.method == "POST":
		data = request.get_json()
		email = data["email"]
		exchange = data["exchange"]
		publicKey = data["publicKey"]
		secretKey = data["secretKey"]

		user = userCollection.find_one({"email": email})
		del user["_id"]
		updateInfo = dict()
		updateInfo['api'] = user['api']

		updateInfo['api'][exchange] = {'API_KEY': publicKey, 'API_SECRET': secretKey}
		user['api'] = updateInfo['api']
		userCollection.update_one({"email": email}, {"$set": updateInfo})
		return jsonify(user)

	elif request.method == "GET":
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
@app.route('/deleteapi', methods=["POST", "GET"])
def deleteAPI():
	if request.method == "POST":
		data = request.get_json()
		email = data["email"]
		exchange = data["exchange"]

		user = userCollection.find_one({"email": email})
		del user["_id"]
		updateInfo = dict()
		updateInfo['api'] = user['api']

		del updateInfo['api'][exchange]
		user['api'] = updateInfo['api']
		userCollection.update_one({"email": email}, {"$set": updateInfo})
		return jsonify(user)

	elif request.method == "GET":
		email=request.args.get('email')
		exchange=request.args.get('exchange')

		user = userCollection.find_one({"email": email})
		updateInfo = dict()
		updateInfo['api'] = user['api']

		del updateInfo['api'][exchange]
		userCollection.update_one({"email": email}, {"$set": updateInfo})
		return '<h1>Delete API Sucessful</h1>'

app.run()