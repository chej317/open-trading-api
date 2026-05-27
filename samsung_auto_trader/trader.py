import time
from datetime import datetime
from .config import SYMBOL, BUY_OFFSET, SELL_OFFSET, POLLING_INTERVAL, START_TIME, END_TIME
from .market_data import get_current_price
from .account import get_balance, get_stock_holding
from .orders import buy_limit_order, sell_limit_order
from .state import load_state, update_state
from .logger import logger

def is_trading_time():
    now = datetime.now()
    start = datetime.strptime(f"{now.strftime('%Y-%m-%d')} {START_TIME}", "%Y-%m-%d %H:%M")
    end = datetime.strptime(f"{now.strftime('%Y-%m-%d')} {END_TIME}", "%Y-%m-%d %H:%M")
    return start <= now <= end

def run_trading_loop(client):
    logger.info("삼성전자 자동매매 프로그램을 시작합니다.")
    
    # 영속성 상태 로드
    state = load_state()
    logger.info(f"이전 상태 로드 완료: {state['status']} (목표가: {state['target_price']}원)")
    
    while True:
        # 1. 거래 시간 확인
        if not is_trading_time():
            now_str = datetime.now().strftime('%H:%M:%S')
            if now_str > END_TIME:
                logger.info(f"현재 시간 {now_str}, 장 종료 시간이 지났습니다. 프로그램을 종료합니다.")
                break
            else:
                logger.info(f"현재 시간 {now_str}, 아직 거래 시간이 아닙니다 ({START_TIME} ~ {END_TIME}). 대기 중...")
                time.sleep(60)
                continue

        try:
            # 2. 현재가 및 잔고 확인
            current_price = get_current_price(client, SYMBOL)
            if not current_price:
                time.sleep(10)
                continue
            
            # API 호출 간격 조정을 위한 짧은 대기 (모의투자 초당 거래건수 제한 EGW00201 방지)
            time.sleep(1)
                
            cash, holdings = get_balance(client)
            hldg_qty, ord_psbl_qty, avg_price = get_stock_holding(holdings, SYMBOL)

            # 3. 매매 판단 (상태 기반)
            if hldg_qty == 0:
                # 미보유 시 상태 초기화 및 매수 판단
                if state["status"] != "IDLE" and state["status"] != "BUYING":
                    logger.info("보유 수량 없음 확인: 상태를 IDLE로 전환합니다.")
                    update_state(status="IDLE", order_id=None, order_type=None, target_price=0)
                    state = load_state()

                # 매수 주문 (현재가 - 2000원)
                buy_price = current_price - BUY_OFFSET
                if cash >= buy_price:
                    logger.info(f"매수 조건 충족: 현재가({current_price}) - {BUY_OFFSET} = {buy_price}원")
                    ord_no = buy_limit_order(client, SYMBOL, 1, buy_price)
                    if ord_no:
                        update_state(status="BUYING", order_id=ord_no, order_type="BUY", target_price=buy_price)
                        state = load_state()
                else:
                    logger.warning(f"예수금 부족으로 매수 불가 (예수금: {cash}원, 필요: {buy_price}원)")
            
            elif ord_psbl_qty > 0:
                # 보유 중이고 매도 가능 수량이 있을 때 매도 주문
                # 목표가 설정: (현재가 + 2000)와 (매입 평단가 + 2000) 중 더 큰 값을 선택
                target_sell_price = max(current_price + SELL_OFFSET, avg_price + SELL_OFFSET)
                
                logger.info(f"매도 조건 충족: 평단가({avg_price:,.0f}), 현재가({current_price:,.0f}) -> 목표가({target_sell_price:,.0f}원)")
                ord_no = sell_limit_order(client, SYMBOL, ord_psbl_qty, int(target_sell_price))
                if ord_no:
                    update_state(status="SELLING", order_id=ord_no, order_type="SELL", target_price=int(target_sell_price))
                    state = load_state()
            
            else:
                # 보유는 하고 있으나 매도 가능 수량이 0인 경우 (이미 주문이 나간 상태)
                if state["status"] != "SELLING":
                    logger.info("매도 주문 진행 중 확인: 상태를 SELLING으로 업데이트합니다.")
                    update_state(status="SELLING")
                    state = load_state()
                logger.info(f"이미 모든 보유 수량에 대해 매도 주문({state.get('last_order_id')})이 진행 중입니다.")

            # 4. 체결 확인을 위한 간접 대기
            logger.info(f"{POLLING_INTERVAL}초 후 다음 확인을 진행합니다. (현재 상태: {state['status']})")
            time.sleep(POLLING_INTERVAL)

        except Exception as e:
            logger.error(f"루프 실행 중 예상치 못한 오류 발생: {e}")
            time.sleep(30)
