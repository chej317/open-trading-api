import json
from datetime import datetime

from samsung_auto_trader.config import CAN_ACCOUNT, ACCOUNT_PRODUCT_CODE, SYMBOL
from samsung_auto_trader.auth import get_access_token
from samsung_auto_trader.api_client import KISClient
from samsung_auto_trader.logger import logger


def main():
    token = get_access_token()
    if not token:
        print(json.dumps({"error": "token_issue"}, ensure_ascii=False))
        return

    client = KISClient(token)

    # 기간: FINAL_PERFORMANCE_REPORT의 운영기간
    start_date = "20260526"
    end_date = "20260617"

    params = {
        "CANO": CAN_ACCOUNT,
        "ACNT_PRDT_CD": ACCOUNT_PRODUCT_CODE,
        "INQR_STRT_DT": start_date,
        "INQR_END_DT": end_date,
        "SORT_DVSN": "00",
        "INQR_DVSN": "00",
        "CBLC_DVSN": "00",
        "PDNO": SYMBOL
    }

    print(json.dumps({"info": "calling inquire-period-profit", "params": {k: (v if k not in ['CANO','ACNT_PRDT_CD'] else 'REDACTED') for k,v in params.items()}}, ensure_ascii=False))

    res = client.get("/uapi/domestic-stock/v1/trading/inquire-period-profit", "TTTC8708R", params=params)

    if not res:
        print(json.dumps({"error": "no_response"}, ensure_ascii=False))
        return

    # Mask possible sensitive fields
    def mask(obj):
        if isinstance(obj, dict):
            return {k: ("REDACTED" if k in ("CANO","ACNT_PRDT_CD","auth") else mask(v)) for k,v in obj.items()}
        if isinstance(obj, list):
            return [mask(x) for x in obj]
        return obj

    safe_res = mask(res)
    print(json.dumps({"response": safe_res}, ensure_ascii=False, indent=2))

    # Try to extract summary from output2 if present
    try:
        out2 = res.get('output2')
        if out2 and isinstance(out2, list):
            summary = out2[0]
            print(json.dumps({"summary_output2": summary}, ensure_ascii=False, indent=2))
    except Exception:
        pass


if __name__ == '__main__':
    main()
