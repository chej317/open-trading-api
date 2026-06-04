from datetime import datetime
import json
import os
from .config import SYMBOL
from .logger import logger

# 실행 경로에 관계없이 같은 위치에 저장되도록 절대 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE_DIR, "trade_state.json")

def save_state(state_data):
    """현재 매매 상태를 파일에 저장"""
    try:
        # 날짜 기록 추가
        state_data["last_update_date"] = datetime.now().strftime("%Y-%m-%d")
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state_data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logger.error(f"상태 저장 중 오류 발생: {e}")

def load_state():
    """파일에서 매매 상태를 로드하고, 날짜가 바뀌었으면 세션 데이터 리셋"""
    today = datetime.now().strftime("%Y-%m-%d")
    
    default_state = {
        "symbol": SYMBOL,
        "last_order_id": None,
        "last_order_type": None, # 'BUY' or 'SELL'
        "last_order_time": None, # 주문 시간 (ISO format)
        "last_order_qty": 0,     # 주문 수량
        "target_price": 0,
        "status": "IDLE", # IDLE, BUYING, SELLING, HOLDING
        "history": [], # 매매 이력
        "performance": {
            "total_pnl": 0,
            "win_rate": 0,
            "trades_count": 0
        },
        "adapted_params": {
            "buy_offset": None,
            "sell_offset": None,
            "polling_interval": None,
            "quantity": 1
        },
        "session_metrics": {
            "recent_high": 0,
            "daily_open": 0
        },
        "unrealized_metrics": {
            "current_pnl": 0,
            "current_ratio": 0,
            "max_ratio": 0
        },
        "last_update_date": today,
        "last_adapt_time": None
    }

    if not os.path.exists(STATE_FILE):
        return default_state
    
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            state = json.load(f)
            
            # 필드 누락 방지를 위한 기본값 보합 (Merge)
            for key, val in default_state.items():
                if key not in state:
                    state[key] = val
                elif isinstance(val, dict):
                    # 2계층 딕셔너리까지 머지
                    for sub_key, sub_val in val.items():
                        if sub_key not in state[key]:
                            state[key][sub_key] = sub_val

            # [3번 이슈] 날짜가 바뀌었으면 세션 데이터 리셋 (Daily Reset)
            if state.get("last_update_date") != today:
                logger.info(f"📅 날짜 변경 감지 ({state.get('last_update_date')} -> {today}). 세션 데이터를 초기화합니다.")
                state["session_metrics"] = default_state["session_metrics"]
                state["unrealized_metrics"] = default_state["unrealized_metrics"]
                state["last_update_date"] = today
                # adapted_params는 유지할지 여부에 따라 결정 가능하나, 
                # 전략적 연속성을 위해 일단 유지하고 세션 지표만 초기화함.

            return state
    except Exception as e:
        logger.error(f"상태 로드 중 오류 발생: {e}")
        return None

def update_state(status=None, order_id=None, order_type=None, order_time=None, order_qty=None, target_price=None, history_entry=None, performance=None, adapted_params=None, session_metrics=None, unrealized_metrics=None, last_adapt_time=None):
    """특정 필드만 업데이트하고 저장 (Nested Dict 지원)"""
    state = load_state()
    if not state:
        return

    if status: state["status"] = status
    if order_id is not None: state["last_order_id"] = order_id
    if order_type: state["last_order_type"] = order_type
    if order_time: state["last_order_time"] = order_time
    if order_qty is not None: state["last_order_qty"] = order_qty
    if target_price: state["target_price"] = target_price
    if history_entry: state["history"].append(history_entry)
    
    # 딕셔너리 필드는 덮어쓰지 않고 업데이트 (Merge)
    if performance: state["performance"].update(performance)
    if adapted_params: state["adapted_params"].update(adapted_params)
    if session_metrics: state["session_metrics"].update(session_metrics)
    if unrealized_metrics: state["unrealized_metrics"].update(unrealized_metrics)
    
    if last_adapt_time: state["last_adapt_time"] = last_adapt_time
    
    save_state(state)
