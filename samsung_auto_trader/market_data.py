from .logger import logger

def get_current_price(client, symbol):
    """
    주식 현재가 및 시세 정보(고가, 저가 등) 조회
    """
    url = "/uapi/domestic-stock/v1/quotations/inquire-price"
    tr_id = "FHKST01010100"
    params = {
        "FID_COND_MRKT_DIV_CODE": "J", # 주식
        "FID_INPUT_ISCD": symbol
    }
    
    res = client.get(url, tr_id, params=params)
    if res and 'output' in res:
        try:
            output = res['output']
            data = {
                "price": int(output['stck_prpr']), # 현재가
                "high": int(output['stck_hgpr']),  # 고가
                "low": int(output['stck_lwpr']),   # 저가
            }
            logger.info(f"[{symbol}] 현재가: {data['price']}, 고가: {data['high']}, 저가: {data['low']}")
            return data
        except (KeyError, ValueError) as e:
            logger.error(f"시세 데이터 파싱 실패: {e}")
    return None

def get_minute_ohlcv(client, symbol, count=30):
    """
    최근 분봉 데이터(OHLCV) 조회
    """
    url = "/uapi/domestic-stock/v1/quotations/inquire-time-itemchartprice"
    tr_id = "FHKST03010200"
    params = {
        "FID_ETC_CLS_CODE": "",
        "FID_COND_MRKT_DIV_CODE": "J",
        "FID_INPUT_ISCD": symbol,
        "FID_PW_DATA_INCU_YN": "N",
        "FID_HOUR_CLS_CODE": "1" # 1분봉
    }
    
    res = client.get(url, tr_id, params=params)
    if res and 'output2' in res:
        try:
            # 최근 봉부터 오므로 역순으로 정렬하여 반환
            output2 = res['output2'][:count]
            prices = [float(item['stck_prpr']) for item in reversed(output2)]
            return prices
        except (KeyError, ValueError) as e:
            logger.error(f"분봉 데이터 파싱 실패: {e}")
    return []
