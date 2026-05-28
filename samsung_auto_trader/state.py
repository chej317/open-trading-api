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
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state_data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logger.error(f"상태 저장 중 오류 발생: {e}")

def load_state():
    """파일에서 매매 상태를 로드"""
    if not os.path.exists(STATE_FILE):
        return {
            "symbol": SYMBOL,
            "last_order_id": None,
            "last_order_type": None, # 'BUY' or 'SELL'
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
            }
        }
    
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            state = json.load(f)
            # 필드 누락 방지를 위한 기본값 보전
            defaults = {
                "history": [],
                "performance": {"total_pnl": 0, "win_rate": 0, "trades_count": 0},
                "adapted_params": {"buy_offset": None, "sell_offset": None, "polling_interval": None, "quantity": 1},
                "session_metrics": {"recent_high": 0, "daily_open": 0},
                "unrealized_metrics": {"current_pnl": 0, "current_ratio": 0, "max_ratio": 0}
            }
            for key, val in defaults.items():
                if key not in state:
                    state[key] = val
            return state
    except Exception as e:
        logger.error(f"상태 로드 중 오류 발생: {e}")
        return None

def update_state(status=None, order_id=None, order_type=None, target_price=None, history_entry=None, performance=None, adapted_params=None, session_metrics=None, unrealized_metrics=None):
    """특정 필드만 업데이트하고 저장"""
    state = load_state()
    if not state:
        return

    if status: state["status"] = status
    if order_id is not None: state["last_order_id"] = order_id
    if order_type: state["last_order_type"] = order_type
    if target_price: state["target_price"] = target_price
    if history_entry: state["history"].append(history_entry)
    if performance: state["performance"].update(performance)
    if adapted_params: state["adapted_params"].update(adapted_params)
    if session_metrics: state["session_metrics"].update(session_metrics)
    if unrealized_metrics: state["unrealized_metrics"].update(unrealized_metrics)
    
    save_state(state)
