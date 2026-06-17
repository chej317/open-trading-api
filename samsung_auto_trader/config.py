import os
from dotenv import load_dotenv

# .env 파일 로드 (있을 경우)
load_dotenv()

# KIS API Credentials
APP_KEY = os.getenv("GH_APPKEY")
APP_SECRET = os.getenv("GH_APPSECRET")
_RAW_ACCOUNT = os.getenv("GH_ACCOUNT") # 종합계좌번호 (예: 5001234501 또는 50012345)

# 계좌번호 처리 (하이픈 제거 및 8/10자리 대응)
if _RAW_ACCOUNT:
    _RAW_ACCOUNT = _RAW_ACCOUNT.replace("-", "").strip()
    if len(_RAW_ACCOUNT) >= 10:
        CAN_ACCOUNT = _RAW_ACCOUNT[:8]
        ACCOUNT_PRODUCT_CODE = _RAW_ACCOUNT[8:10]
    else:
        CAN_ACCOUNT = _RAW_ACCOUNT
        # 모의투자의 경우 보통 '01'을 사용합니다.
        ACCOUNT_PRODUCT_CODE = os.getenv("GH_ACCOUNT_PRDT_CD", "01")
else:
    CAN_ACCOUNT = None
    ACCOUNT_PRODUCT_CODE = "01"

# [중요] "모의투자 주문이 불가한 계좌입니다" 에러 발생 시 확인 사항:
# 1. GH_ACCOUNT에 입력한 계좌가 실제 '모의투자용 계좌'인지 확인하십시오. (실전 계좌는 모의 서버에서 주문 불가)
# 2. 한국투자증권 홈페이지/앱에서 '모의투자 신청'이 완료되었는지 확인하십시오.
# 3. AppKey/AppSecret이 모의투자용으로 발급된 것인지 확인하십시오.

# Trading Settings
SYMBOL = "005930"  # 삼성전자
BUY_OFFSET = 2000  # 현재가 - 2000
SELL_OFFSET = 2000 # 현재가 + 2000

# API URLs (Mock Trading / 모의투자)
# 실전투자 시: https://openapi.koreainvestment.com:9443
BASE_URL = "https://openapivts.koreainvestment.com:29443"

# Token Cache File
TOKEN_CACHE_FILE = "token_cache.json"

# Polling Interval (seconds)
POLLING_INTERVAL = 60

# Trading Window
START_TIME = "09:10"
END_TIME = "15:30"
