from .config import CAN_ACCOUNT, ACCOUNT_PRODUCT_CODE
from .logger import logger

def place_order(client, ord_dv, symbol, qty, price):
    """
    주문 실행 (매수/매도)
    ord_dv: 'buy' 또는 'sell'
    """
    url = "/uapi/domestic-stock/v1/trading/order-cash"
    
    # 국내주식 모의투자 표준 TR_ID
    if ord_dv == "buy":
        tr_id = "VTTC0802U" # 모의투자 매수
    else:
        tr_id = "VTTC0801U" # 모의투자 매도
        
    data = {
        "CANO": CAN_ACCOUNT,
        "ACNT_PRDT_CD": ACCOUNT_PRODUCT_CODE,
        "PDNO": symbol,
        "ORD_DVSN": "00", # 지정가
        "ORD_QTY": str(qty),
        "ORD_UNPR": str(price),
        "EXCG_ID_DVSN_CD": "KRX", # 모의투자에서도 KRX 지정 권장
        "SLL_TYPE": "01" if ord_dv == "sell" else "00", # 매도 시 01(일반), 매수 시 00
        "CTAC_TLNO": "",
        "ALGO_NO": ""
    }
    
    logger.info(f"[{ord_dv.upper()}] 주문 요청: {symbol}, {qty}주, {price}원 (TR_ID: {tr_id})")
    res = client.post(url, tr_id, data=data)
    
    if res and res.get('rt_cd') == '0':
        ord_no = res.get('output', {}).get('ODNO')
        logger.info(f"주문 성공! 주문번호: {ord_no}")
        return ord_no
    else:
        error_msg = res.get('msg1') if res else '응답 없음'
        logger.error(f"주문 실패: {error_msg}")
        return None

def cancel_order(client, symbol, ord_no, qty, price):
    """
    주문 취소
    """
    url = "/uapi/domestic-stock/v1/trading/order-rvsecncl"
    tr_id = "VTTC0803U" # 모의투자 정정/취소 표준
    
    data = {
        "CANO": CAN_ACCOUNT,
        "ACNT_PRDT_CD": ACCOUNT_PRODUCT_CODE,
        "KRX_FWDG_ORD_ORGNO": "", # 모의투자는 공백 허용
        "ORGN_ODNO": ord_no,
        "ORD_DVSN": "00", # 지정가
        "RVSE_CNCL_DVSN_CD": "02", # 01: 정정, 02: 취소
        "ORD_QTY": str(qty),
        "ORD_UNPR": str(price),
        "QTY_ALL_ORD_YN": "Y", # 전량 취소
        "EXCG_ID_DVSN_CD": "KRX"
    }
    
    logger.info(f"[CANCEL] 주문 취소 요청: {symbol}, 주문번호: {ord_no}")
    res = client.post(url, tr_id, data=data)
    
    if res and res.get('rt_cd') == '0':
        logger.info(f"주문 취소 성공! (원주문: {ord_no})")
        return True, res
    else:
        msg = res.get('msg1') if res else '응답 없음'
        logger.error(f"주문 취소 실패: {msg}")
        return False, res

def buy_limit_order(client, symbol, qty, price):
    return place_order(client, "buy", symbol, qty, price)

def sell_limit_order(client, symbol, qty, price):
    return place_order(client, "sell", symbol, qty, price)
