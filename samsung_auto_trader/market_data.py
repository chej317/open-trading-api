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
