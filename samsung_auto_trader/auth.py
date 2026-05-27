import json
import os
import requests
from datetime import datetime, timedelta
from .config import APP_KEY, APP_SECRET, BASE_URL, TOKEN_CACHE_FILE
from .logger import logger

def get_access_token():
    # 1. 캐시된 토큰 확인
    if os.path.exists(TOKEN_CACHE_FILE):
        try:
            with open(TOKEN_CACHE_FILE, 'r') as f:
                cache = json.load(f)
                
            expire_dt = datetime.strptime(cache['expire_date'], "%Y-%m-%d %H:%M:%S")
            # 만료 1시간 전까지만 유효한 것으로 간주 (여유분)
            if expire_dt > datetime.now() + timedelta(hours=1):
                logger.info("기존 유효한 토큰을 캐시에서 로드했습니다.")
                return cache['access_token']
        except Exception as e:
            logger.error(f"캐시 토큰 로드 중 오류 발생: {e}")

    # 2. 새로운 토큰 발급
    logger.info("새로운 접근 토큰을 발급받습니다...")
    url = f"{BASE_URL}/oauth2/tokenP"
    headers = {"content-type": "application/json"}
    body = {
        "grant_type": "client_credentials",
        "appkey": APP_KEY,
        "appsecret": APP_SECRET
    }

    try:
        res = requests.post(url, headers=headers, data=json.dumps(body))
        res.raise_for_status()
        data = res.json()
        
        access_token = data['access_token']
        expire_date = data['access_token_token_expired'] # "YYYY-MM-DD HH:MM:SS"

        # 3. 토큰 캐싱
        with open(TOKEN_CACHE_FILE, 'w') as f:
            json.dump({
                'access_token': access_token,
                'expire_date': expire_date
            }, f)
        
        logger.info(f"새로운 토큰이 발급 및 저장되었습니다. 만료 시간: {expire_date}")
        return access_token

    except Exception as e:
        logger.error(f"토큰 발급 실패: {e}")
        return None
