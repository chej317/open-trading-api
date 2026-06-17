import json
from samsung_auto_trader.config import CAN_ACCOUNT, ACCOUNT_PRODUCT_CODE, SYMBOL
from samsung_auto_trader.auth import get_access_token
from samsung_auto_trader.api_client import KISClient


def main():
    token = get_access_token()
    if not token:
        print(json.dumps({"error": "token_issue"}, ensure_ascii=False))
        return

    client = KISClient(token)

    params = {
        "CANO": CAN_ACCOUNT,
        "ACNT_PRDT_CD": ACCOUNT_PRODUCT_CODE,
        "INQR_STRT_DT": "20260526",
        "INQR_END_DT": "20260617",
        "SLL_BUY_DVSN_CD": "00",  # 전체
        "PDNO": SYMBOL,
        "CCLD_DVSN": "00",  # 전체(체결/미체결)
        "INQR_DVSN": "00",
        "INQR_DVSN_3": "00",
        "EXCG_ID_DVSN_CD": "KRX"
    }

    print(json.dumps({"info": "calling inquire-daily-ccld", "params": {k: (v if k not in ['CANO','ACNT_PRDT_CD'] else 'REDACTED') for k,v in params.items()}}, ensure_ascii=False))

    res = client.get("/uapi/domestic-stock/v1/trading/inquire-daily-ccld", "VTTC0081R", params=params)

    if not res:
        print(json.dumps({"error": "no_response"}, ensure_ascii=False))
        return

    print(json.dumps({"response_keys": list(res.keys())}, ensure_ascii=False))

    # print sizes
    try:
        out1 = res.get('output1', [])
        out2 = res.get('output2', [])
        print(json.dumps({"output1_count": len(out1), "output2_count": len(out2)}, ensure_ascii=False))
        # Show first 5 rows of output1
        for i, item in enumerate(out1[:5]):
            print(json.dumps({"row": i, "data": item}, ensure_ascii=False, indent=2))
        # Show output2 (summary) safely
        if isinstance(out2, list):
            for i, item in enumerate(out2[:5]):
                print(json.dumps({"out2_row": i, "data": item}, ensure_ascii=False, indent=2))
        else:
            print(json.dumps({"output2": out2}, ensure_ascii=False, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}))

if __name__ == '__main__':
    main()
