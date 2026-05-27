from .config import CAN_ACCOUNT, ACCOUNT_PRODUCT_CODE
from .logger import logger

def place_order(client, ord_dv, symbol, qty, price):
    """
    주문 실행 (매수/매도)
    ord_dv: 'buy' 또는 'sell'
    """
    url = "/uapi/domestic-stock/v1/trading/order-cash"
    
    if ord_dv == "buy":
        tr_id = "VTTC0012U" # 모의투자 매수
    else:
        tr_id = "VTTC0011U" # 모의투자 매도
        
    data = {
        "CANO": CAN_ACCOUNT,
        "ACNT_PRDT_CD": ACCOUNT_PRODUCT_CODE,
        "PDNO": symbol,
        "ORD_DVSN": "00", # 지정가
        "ORD_QTY": str(qty),
        "ORD_UNPR": str(price),
        "EXCG_ID_DVSN_CD": "KRX",
        "SLL_TYPE": "01" if ord_dv == "sell" else "",
        "CNDT_PRIC": "",
        "ALGO_NO": ""
    }
    
    logger.info(f"[{ord_dv.upper()}] 주문 요청: {symbol}, {qty}주, {price}원")
    res = client.post(url, tr_id, data=data)
    
    if res and res.get('rt_cd') == '0':
        ord_no = res.get('output', {}).get('ODNO')
        logger.info(f"주문 성공! 주문번호: {ord_no}")
        return ord_no
    else:
        logger.error(f"주문 실패: {res.get('msg1') if res else '응답 없음'}")
        return None

def buy_limit_order(client, symbol, qty, price):
    return place_order(client, "buy", symbol, qty, price)

def sell_limit_order(client, symbol, qty, price):
    return place_order(client, "sell", symbol, qty, price)
