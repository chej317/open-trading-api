import json
import os
import requests
from datetime import datetime, timedelta
from .config import APP_KEY, APP_SECRET, BASE_URL, TOKEN_CACHE_FILE
from .logger import logger

# 메모리 캐시 변수
_cached_token = None
_expire_dt = None

def get_access_token(force_refresh=False):
    global _cached_token, _expire_dt

    # 0. 메모리 캐시 확인 (강제 갱신이 아닐 때)
    if not force_refresh and _cached_token and _expire_dt:
        if _expire_dt > datetime.now() + timedelta(hours=1):
            return _cached_token

    # 1. 캐시된 토큰 확인 (강제 갱신이 아닐 때)
    if not force_refresh and os.path.exists(TOKEN_CACHE_FILE):
        try:
            with open(TOKEN_CACHE_FILE, 'r') as f:
                cache = json.load(f)
                
            expire_dt = datetime.strptime(cache['expire_date'], "%Y-%m-%d %H:%M:%S")
            # 만료 1시간 전까지만 유효한 것으로 간주 (여유분)
            if expire_dt > datetime.now() + timedelta(hours=1):
                logger.info("기존 유효한 토큰을 캐시에서 로드했습니다.")
                _cached_token = cache['access_token']
                _expire_dt = expire_dt
                return _cached_token
        except Exception as e:
            logger.error(f"캐시 토큰 로드 중 오류 발생: {e}")

    # 2. 새로운 토큰 발급
    reason = "강제 갱신 요청" if force_refresh else "토큰 만료 또는 없음"
    logger.info(f"새로운 접근 토큰을 발급받습니다... (사유: {reason})")
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
        _cached_token = access_token
        _expire_dt = datetime.strptime(expire_date, "%Y-%m-%d %H:%M:%S")
        
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
