import time
import requests
from .config import APP_KEY, APP_SECRET, BASE_URL
from .logger import logger
from .auth import get_access_token

class KISClient:
    def __init__(self, access_token=None):
        self.access_token = access_token
        self.last_call_time = 0

    def _get_headers(self, tr_id, tr_cont=""):
        # 토큰 자동 갱신 (유효 기간 확인 및 발급)
        self.access_token = get_access_token()
        headers = {
            "Content-Type": "application/json",
            "authorization": f"Bearer {self.access_token}",
            "appkey": APP_KEY,
            "appsecret": APP_SECRET,
            "tr_id": tr_id,
            "tr_cont": tr_cont,
            "custtype": "P", # 개인
        }
        return headers

    def _wait_for_rate_limit(self):
        # 모의투자 기준 1초당 2건 제한이 있는 경우가 많으므로 0.5초 대기
        now = time.time()
        elapsed = now - self.last_call_time
        if elapsed < 0.5:
            time.sleep(0.5 - elapsed)
        self.last_call_time = time.time()

    def get(self, url, tr_id, params=None, retry=True):
        self._wait_for_rate_limit()
        headers = self._get_headers(tr_id)
        try:
            res = requests.get(f"{BASE_URL}{url}", headers=headers, params=params, timeout=10)
            
            # 토큰 만료 에러 (EGW00123) 처리
            if res.status_code in [401, 500]:
                try:
                    res_json = res.json()
                    if res_json.get("msg_cd") == "EGW00123" and retry:
                        logger.warning("토큰 만료 감지 (EGW00123). 토큰 강제 갱신 후 재시도합니다.")
                        get_access_token(force_refresh=True)
                        return self.get(url, tr_id, params, retry=False)
                except:
                    pass

            res.raise_for_status()
            return res.json()
        except Exception as e:
            logger.error(f"GET 요청 실패 ({tr_id}): {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"상세 에러: {e.response.text}")
            return None

    def post(self, url, tr_id, data=None, retry=True):
        self._wait_for_rate_limit()
        headers = self._get_headers(tr_id)
        # 로그용 데이터 마스킹
        log_data = data.copy() if data else {}
        if "CANO" in log_data:
            log_data["CANO"] = log_data["CANO"][:4] + "****"
            
        try:
            res = requests.post(f"{BASE_URL}{url}", headers=headers, json=data, timeout=10)
            
            # 토큰 만료 에러 (EGW00123) 처리
            if res.status_code in [401, 500]:
                try:
                    res_json = res.json()
                    if res_json.get("msg_cd") == "EGW00123" and retry:
                        logger.warning("토큰 만료 감지 (EGW00123). 토큰 강제 갱신 후 재시도합니다.")
                        get_access_token(force_refresh=True)
                        return self.post(url, tr_id, data, retry=False)
                except:
                    pass

            res.raise_for_status()
            return res.json()
        except Exception as e:
            logger.error(f"POST 요청 실패 ({tr_id}): {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    err_json = e.response.json()
                    logger.error(f"상세 에러: {err_json.get('msg_cd')} - {err_json.get('msg1')}")
                except:
                    logger.error(f"상세 에러: {e.response.text}")
            return None
