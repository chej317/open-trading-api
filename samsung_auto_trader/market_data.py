from .logger import logger

def get_current_price(client, symbol):
    """
    주식 현재가 시세 조회
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
            price = int(res['output']['stck_prpr']) # 현재가
            logger.info(f"[{symbol}] 현재가: {price}원")
            return price
        except (KeyError, ValueError) as e:
            logger.error(f"현재가 데이터 파싱 실패: {e}")
    return None
