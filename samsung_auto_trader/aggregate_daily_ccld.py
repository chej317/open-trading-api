import json
from datetime import datetime, timedelta
import time
from samsung_auto_trader.config import CAN_ACCOUNT, ACCOUNT_PRODUCT_CODE, SYMBOL
from samsung_auto_trader.auth import get_access_token
from samsung_auto_trader.api_client import KISClient


def fetch_for_date(client, date_str):
    buy_amt = 0
    sell_amt = 0
    trades = 0

    FK100 = ""
    NK100 = ""

    for page in range(10):
        params = {
            "CANO": CAN_ACCOUNT,
            "ACNT_PRDT_CD": ACCOUNT_PRODUCT_CODE,
            "INQR_STRT_DT": date_str,
            "INQR_END_DT": date_str,
            "SLL_BUY_DVSN_CD": "00",
            "PDNO": SYMBOL,
            "CCLD_DVSN": "01",  # 체결만
            "INQR_DVSN": "00",
            "INQR_DVSN_3": "00",
            "EXCG_ID_DVSN_CD": "KRX",
        }

        # Include CTX_AREA only if valid and not suspicious
        if FK100 and '+' not in FK100:
            params['CTX_AREA_FK100'] = FK100
        if NK100 and '+' not in NK100:
            params['CTX_AREA_NK100'] = NK100

        res = client.get("/uapi/domestic-stock/v1/trading/inquire-daily-ccld", "VTTC0081R", params=params)
        if not res:
            break

        out1 = res.get('output1', [])
        # accumulate
        for row in out1:
            qty = int(row.get('tot_ccld_qty', row.get('ord_qty', 0)) or 0)
            amt = int(row.get('tot_ccld_amt', 0) or 0)
            kind = row.get('sll_buy_dvsn_cd') or row.get('sll_buy_dvsn_cd_name','')
            if qty > 0 and amt != 0:
                trades += 1
                # kind: '01' 매도, '02' 매수
                if kind == '01' or '매도' in str(kind):
                    sell_amt += amt
                else:
                    buy_amt += amt

        # check for pagination ctx area
        FK100 = res.get('ctx_area_fk100', '') or FK100
        NK100 = res.get('ctx_area_nk100', '') or NK100

        # wait between pages to respect rate limits
        time.sleep(1.5)

        # heuristics: if no more output or no ctx keys, stop
        if not NK100 and not FK100:
            break

    return buy_amt, sell_amt, trades


def main():
    token = get_access_token()
    if not token:
        print(json.dumps({"error": "token_issue"}, ensure_ascii=False))
        return

    client = KISClient(token)

    start = datetime.strptime("2026-05-26", "%Y-%m-%d")
    end = datetime.strptime("2026-06-17", "%Y-%m-%d")

    total_buy = 0
    total_sell = 0
    total_trades = 0

    d = start
    while d <= end:
        date_str = d.strftime("%Y%m%d")
        b, s, t = fetch_for_date(client, date_str)
        if t > 0:
            print(json.dumps({"date": date_str, "buy_amt": b, "sell_amt": s, "trades": t}, ensure_ascii=False))
        total_buy += b
        total_sell += s
        total_trades += t
        d += timedelta(days=1)

    net = total_sell - total_buy
    print(json.dumps({"total_buy": total_buy, "total_sell": total_sell, "total_trades": total_trades, "net_pnl": net}, ensure_ascii=False))

if __name__ == '__main__':
    main()
