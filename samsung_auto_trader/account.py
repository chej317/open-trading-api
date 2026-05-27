from .config import CAN_ACCOUNT, ACCOUNT_PRODUCT_CODE
from .logger import logger

def get_balance(client):
    """
    계좌 잔고 및 예수금 조회
    """
    url = "/uapi/domestic-stock/v1/trading/inquire-balance"
    tr_id = "VTTC8434R" # 모의투자용
    params = {
        "CANO": CAN_ACCOUNT,
        "ACNT_PRDT_CD": ACCOUNT_PRODUCT_CODE,
        "AFHR_FLPR_YN": "N",
        "OFL_YN": "",
        "INQR_DVSN": "02", # 종목별
        "UNPR_DVSN": "01",
        "FUND_STTL_ICLD_YN": "N",
        "FNCG_AMT_AUTO_RDPT_YN": "N",
        "PRCS_DVSN": "00", # 전일매매포함
        "CTX_AREA_FK100": "",
        "CTX_AREA_NK100": ""
    }
    
    res = client.get(url, tr_id, params=params)
    if res:
        # output2에서 예수금 총액 추출
        if 'output2' in res and len(res['output2']) > 0:
            cash = int(res['output2'][0]['dnca_tot_amt'])
            logger.info(f"계좌 예수금: {cash}원")
            return cash, res.get('output1', [])
    
    logger.error("잔고 조회 실패")
    return 0, []

def get_stock_holding(holdings, symbol):
    """
    특정 종목의 보유 수량, 매도 가능 수량, 평균 매입가 확인
    """
    for item in holdings:
        if item['pdno'] == symbol:
            hldg_qty = int(item['hldg_qty'])
            # ord_psbl_qty: 매도 가능 수량
            ord_psbl_qty = int(item.get('ord_psbl_qty', 0))
            # puse_uprc: 평균 매입단가
            avg_price = float(item.get('puse_uprc', 0))
            
            logger.info(f"[{symbol}] 보유: {hldg_qty}주, 매도 가능: {ord_psbl_qty}주, 평단가: {avg_price:,.0f}원")
            return hldg_qty, ord_psbl_qty, avg_price
    return 0, 0, 0.0
