import os
from dotenv import load_dotenv

# .env 파일 로드 (있을 경우)
load_dotenv()

# KIS API Credentials
APP_KEY = os.getenv("GH_APPKEY")
APP_SECRET = os.getenv("GH_APPSECRET")
CAN_ACCOUNT = os.getenv("GH_ACCOUNT") # 종합계좌번호 (8자리)

# Trading Settings
SYMBOL = "005930"  # 삼성전자
BUY_OFFSET = 2000  # 현재가 - 2000
SELL_OFFSET = 2000 # 현재가 + 2000

# API URLs (Mock Trading / 모의투자)
BASE_URL = "https://openapivts.koreainvestment.com:29443"

# Token Cache File
TOKEN_CACHE_FILE = "token_cache.json"

# Polling Interval (seconds)
POLLING_INTERVAL = 60

# Trading Window
START_TIME = "09:10"
END_TIME = "15:30"

# Mock Trading Account Product Code (보통 '01'이 종합계좌 상품코드)
ACCOUNT_PRODUCT_CODE = "01"
