import time
from datetime import datetime
from .config import SYMBOL, BUY_OFFSET, SELL_OFFSET, POLLING_INTERVAL, START_TIME, END_TIME
from .market_data import get_current_price
from .account import get_balance, get_stock_holding
from .orders import buy_limit_order, sell_limit_order
from .state import load_state, update_state
from .evaluator import evaluate_and_adapt, check_anti_peak, evaluate_unrealized_risk
from .utils import round_to_tick
from .logger import logger

def is_trading_time():
    now = datetime.now()
    start = datetime.strptime(f"{now.strftime('%Y-%m-%d')} {START_TIME}", "%Y-%m-%d %H:%M")
    end = datetime.strptime(f"{now.strftime('%Y-%m-%d')} {END_TIME}", "%Y-%m-%d %H:%M")
    return start <= now <= end

def run_trading_loop(client):
    logger.info("삼성전자 자동매매 프로그램을 시작합니다. (자가 적응형 로직 활성화)")
    
    # 영속성 상태 로드
    state = load_state()
    logger.info(f"이전 상태 로드 완료: {state['status']} (목표가: {state['target_price']}원)")
    
    while True:
        try:
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

            # 적응형 파라미터 로드
            state = load_state()
            if not state:
                logger.error("상태 파일을 로드할 수 없습니다. 10초 후 재시도합니다.")
                time.sleep(10)
                continue

            adapted = state.get("adapted_params", {})
            current_buy_offset = adapted.get("buy_offset") or BUY_OFFSET
            current_sell_offset = adapted.get("sell_offset") or SELL_OFFSET
            current_polling = adapted.get("polling_interval") or POLLING_INTERVAL
            current_qty = adapted.get("quantity") or 1

            # 2. 현재가 및 잔고 확인
            current_price = get_current_price(client, SYMBOL)
            if not current_price:
                logger.warning(f"[{SYMBOL}] 현재가를 가져오는데 실패했습니다. 10초 후 재시도합니다.")
                time.sleep(10)
                continue
            
            # API 호출 간격 조정을 위한 짧은 대기
            time.sleep(1)
                
            cash, holdings = get_balance(client)
            hldg_qty, ord_psbl_qty, avg_price = get_stock_holding(holdings, SYMBOL)

            # 미실현 리스크 평가 (손절 및 수익보존)
            risk_action = evaluate_unrealized_risk(current_price, avg_price, hldg_qty)

            # 3. 매매 판단 (상태 기반)
            if hldg_qty == 0:
                # 매수 전 '물림 방지' 체크
                extra_offset = check_anti_peak(current_price)
                
                # 매도 주문이 체결된 경우 상태 전환
                if state["status"] not in ["IDLE", "BUYING"]:
                    update_state(unrealized_metrics={"max_ratio": 0})
                    if state["status"] == "SELLING" and state.get("last_order_type") == "SELL":
                        logger.info("매도 주문 완료 확인: 상태를 IDLE로 전환합니다.")
                    update_state(status="IDLE", order_id=None, order_type=None, target_price=0)
                    state = load_state()

                # 매수 로직
                if state["status"] == "BUYING":
                    logger.info(f"이미 매수 주문({state.get('last_order_id')})이 진행 중입니다. 체결을 기다립니다.")
                else:
                    buy_price = round_to_tick(current_price - (current_buy_offset + extra_offset), direction="down")
                    if cash >= buy_price * current_qty:
                        logger.info(f"매수 조건 충족: 현재가({current_price}) - 오프셋({current_buy_offset}+{extra_offset}) = {buy_price}원 (보수적 하향 보정)")
                        ord_no = buy_limit_order(client, SYMBOL, current_qty, buy_price)
                        if ord_no:
                            update_state(status="BUYING", order_id=ord_no, order_type="BUY", target_price=buy_price)
                            state = load_state()
                    else:
                        logger.warning(f"예수금 부족으로 매수 불가 (예수금: {cash}원, 필요: {buy_price * current_qty}원)")
            
            elif ord_psbl_qty > 0:
                # 보유 중이고 매수 완료 시 히스토리 기록
                if state["status"] == "BUYING":
                    logger.info(f"매수 체결 확인 (평단가: {avg_price:,.0f}원). 히스토리에 기록합니다.")
                    update_state(status="HOLDING")
                    state = load_state()

                # 매도 로직
                if state["status"] == "SELLING":
                    logger.info(f"이미 매도 주문({state.get('last_order_id')})이 진행 중입니다. 체결을 기다립니다.")
                else:
                    # 목표가 설정 (일반 익절 vs 리스크 대응)
                    if risk_action:
                        # 리스크 대응 시에는 체결 우선을 위해 '내림' 보정하여 공격적 매도
                        target_sell_price = round_to_tick(current_price, direction="down")
                        reason = "손절(STOP_LOSS)" if risk_action == "STOP_LOSS" else "수익보존(PROFIT_PROTECTION)"
                        logger.info(f"🔥 {reason} 실행: 현재가 근처({target_sell_price:,.0f}원)로 즉시 매도 주문 (공격적 하향 보정)")
                    else:
                        # 일반 매도 시에는 수익 극대화를 위해 '올림' 보정
                        target_sell_price = round_to_tick(max(current_price + current_sell_offset, avg_price + current_sell_offset), direction="up")
                        logger.info(f"매도 조건 충족: 평단가({avg_price:,.0f}), 현재가({current_price:,.0f}) -> 목표가({target_sell_price:,.0f}원) (보수적 상향 보정)")
                    
                    ord_no = sell_limit_order(client, SYMBOL, ord_psbl_qty, target_sell_price)
                    if ord_no:
                        # 매도 주문 시점에 히스토리에 매수-매도 세트 기록 (평가용)
                        pnl = (int(target_sell_price) - avg_price) * ord_psbl_qty
                        history_entry = {
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "buy_price": avg_price,
                            "sell_price": int(target_sell_price),
                            "qty": ord_psbl_qty,
                            "pnl": pnl
                        }
                        
                        # 성과 지표 업데이트
                        perf = state.get("performance", {})
                        new_trades_count = perf.get("trades_count", 0) + 1
                        new_total_pnl = perf.get("total_pnl", 0) + pnl
                        wins = len([h for h in state.get("history", []) if h['pnl'] > 0]) + (1 if pnl > 0 else 0)
                        new_win_rate = (wins / new_trades_count) * 100
                        
                        update_state(
                            status="SELLING", 
                            order_id=ord_no, 
                            order_type="SELL", 
                            target_price=int(target_sell_price),
                            history_entry=history_entry,
                            performance={
                                "total_pnl": new_total_pnl,
                                "trades_count": new_trades_count,
                                "win_rate": new_win_rate
                            }
                        )
                        
                        # 매도 주문 후 성과 평가 및 전략 수정 트리거
                        evaluate_and_adapt()
                        state = load_state()
            
            else:
                # 보유 수량은 있으나 매도 가능 수량이 0인 경우 = 이미 매도 주문 중
                if state["status"] != "SELLING":
                    update_state(status="SELLING")
                    state = load_state()
                logger.info(f"보유 수량({hldg_qty})에 대해 매도 주문({state.get('last_order_id')})이 진행 중입니다.")

            # 4. 다음 루프 대기
            logger.info(f"{current_polling}초 후 다음 확인을 진행합니다. (현재 상태: {state['status']})")
            time.sleep(current_polling)

        except Exception as e:
            logger.error(f"루프 실행 중 예상치 못한 오류 발생: {e}")
            import traceback
            logger.error(traceback.format_exc())
            time.sleep(30)
