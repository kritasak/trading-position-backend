import os
from dotenv import load_dotenv

load_dotenv()

BITKUB_API_KEY = os.getenv('BITKUB_API_KEY')
BITKUB_API_SECRET = os.getenv('BITKUB_API_SECRET')
BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
BINANCE_API_SECRET = os.getenv('BINANCE_API_SECRET')
MONGODB_USERNAME = os.getenv('MONGODB_USERNAME')
MONGODB_PASSWORD = os.getenv('MONGODB_PASSWORD')