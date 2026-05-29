import os
from datetime import datetime
from .state import load_state, update_state
from .logger import logger
from .config import BUY_OFFSET, SELL_OFFSET, POLLING_INTERVAL

# 수정 이력 파일 및 최적화 기록 폴더 경로
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
OPTIMIZATION_DIR = os.path.join(PROJECT_ROOT, "self_optimization_history")

def log_adaptation(reason, old_params, new_params, performance, history):
    """전략 수정 및 성과 리포트를 별도 폴더에 기록"""
    if not os.path.exists(OPTIMIZATION_DIR):
        os.makedirs(OPTIMIZATION_DIR)
        
    now_str = datetime.now().strftime("%Y%m%d%H%M")
    
    # 1. Performance Report 생성
    perf_file = os.path.join(OPTIMIZATION_DIR, f"performance_report_{now_str}.md")
    perf_content = f"""# 📊 Performance Report ({datetime.now().strftime("%Y-%m-%d %H:%M:%S")})

## 📈 성과 요약
- **총 손익**: {performance.get('total_pnl', 0):,}원
- **승률**: {performance.get('win_rate', 0):.2f}%
- **총 거래 횟수**: {performance.get('trades_count', 0)}회

## 📜 최근 거래 이력 (최근 5건)
| 시간 | 매수가 | 매도가 | 수량 | 손익 |
| :--- | :--- | :--- | :--- | :--- |
"""
    for entry in history[-5:]:
        perf_content += f"| {entry['timestamp']} | {entry['buy_price']:,} | {entry['sell_price']:,} | {entry['qty']} | {entry['pnl']:,} |\n"

    with open(perf_file, "w", encoding="utf-8") as f:
        f.write(perf_content)

    # 2. Code Modification Summary 생성 (파라미터 변경 내역)
    mod_file = os.path.join(OPTIMIZATION_DIR, f"code_modification_summary_{now_str}.md")
    mod_content = f"""# 🛠️ Code Modification Summary ({datetime.now().strftime("%Y-%m-%d %H:%M:%S")})

## 💡 수정 사유
- {reason}

## ⚙️ 파라미터 변경 내역
| 파라미터 | 이전 값 | 변경된 값 |
| :--- | :--- | :--- |
| **BUY_OFFSET** | {old_params.get('buy_offset')} | {new_params.get('buy_offset')} |
| **SELL_OFFSET** | {old_params.get('sell_offset')} | {new_params.get('sell_offset')} |
| **POLLING_INTERVAL** | {old_params.get('polling_interval')} | {new_params.get('polling_interval')} |
| **QUANTITY** | {old_params.get('quantity')} | {new_params.get('quantity')} |

---
*본 수정은 자가 적응형 로직에 의해 자동으로 생성되었습니다.*
"""
    with open(mod_file, "w", encoding="utf-8") as f:
        f.write(mod_content)

    logger.info(f"자가 최적화 기록 완료: {OPTIMIZATION_DIR}")

def evaluate_and_adapt():
    """매매 성과를 평가하고 파라미터를 조정"""
    state = load_state()
    history = state.get("history", [])
    performance = state.get("performance", {})
    
    # 최소 3회 이상의 매매 이력이 있을 때 평가 시작
    if len(history) < 3:
        return

    old_params = state.get("adapted_params", {}).copy()
    # None인 경우 기본값으로 채움
    if old_params.get("buy_offset") is None: old_params["buy_offset"] = BUY_OFFSET
    if old_params.get("sell_offset") is None: old_params["sell_offset"] = SELL_OFFSET
    if old_params.get("polling_interval") is None: old_params["polling_interval"] = POLLING_INTERVAL
    if old_params.get("quantity") is None: old_params["quantity"] = 1
    
    new_params = old_params.copy()
    reason = "정기 성과 평가 기반 조정"
    
    win_rate = performance.get("win_rate", 0)
    total_pnl = performance.get("total_pnl", 0)
    
    # 1. 승률이 높고 수익이 났을 때: 익절 목표가 상향
    if win_rate > 70 and total_pnl > 0:
        new_params["sell_offset"] = min(old_params["sell_offset"] + 500, 10000)
        reason = "승률 우수: 익절 목표가 상향 (수익 극대화)"
    
    # 2. 손실이 발생했을 때: 더 싸게 사고(BUY_OFFSET 증가), 보수적으로 매도
    elif total_pnl < 0:
        new_params["buy_offset"] = min(old_params["buy_offset"] + 500, 10000)
        new_params["sell_offset"] = max(old_params["sell_offset"] - 500, 1000)
        reason = "손실 발생: 보수적 대응으로 전환 (매수 타점 하향 및 빠른 익절)"

    # 변경 사항이 있을 경우 저장 및 로깅
    if new_params != old_params:
        update_state(adapted_params=new_params)
        log_adaptation(reason, old_params, new_params, performance, history)

def evaluate_unrealized_risk(current_price, avg_price, qty):
    """
    미실현 손익을 기반으로 리스크를 평가하고 즉각적인 조치를 제안.
    - 하드 손절 (Stop-Loss)
    - 수익 보존 (Trailing Profit Protection)
    """
    if qty <= 0 or avg_price <= 0:
        update_state(unrealized_metrics={"current_pnl": 0, "current_ratio": 0, "max_ratio": 0})
        return None

    pnl = (current_price - avg_price) * qty
    ratio = (pnl / (avg_price * qty)) * 100
    
    state = load_state()
    metrics = state.get("unrealized_metrics", {})
    max_ratio = max(metrics.get("max_ratio", 0), ratio)
    
    update_state(unrealized_metrics={
        "current_pnl": int(pnl),
        "current_ratio": round(ratio, 2),
        "max_ratio": round(max_ratio, 2)
    })
    
    logger.info(f"미실현 손익: {int(pnl):,}원 ({ratio:.2f}%), 최고 수익률: {max_ratio:.2f}%")

    # 1. 하드 손절 (Stop-Loss): -3% 도달 시
    STOP_LOSS_THRESHOLD = -3.0
    if ratio <= STOP_LOSS_THRESHOLD:
        logger.warning(f"🚨 하드 손절 조건 충족 ({ratio:.2f}%). 즉시 매도 프로세스 진입.")
        return "STOP_LOSS"

    # 2. 수익 보존 (Trailing Protection): 1% 이상 수익권 도달 후 고점 대비 0.5% 하락 시
    if max_ratio >= 1.0 and (max_ratio - ratio) >= 0.5:
        logger.warning(f"💰 수익 보존 조건 충족 (고점 {max_ratio:.2f}% -> 현재 {ratio:.2f}%). 이익 확정 권장.")
        return "PROFIT_PROTECTION"

    return None

def check_anti_peak(current_price):
    """
    '물리지 않도록' 하기 위한 고점 매수 방지 로직.
    현재가가 최근 고점 대비 너무 높거나 급등한 상태라면 매수 유보 또는 오프셋 강화.
    """
    state = load_state()
    metrics = state.get("session_metrics", {})
    recent_high = metrics.get("recent_high", 0)
    
    # 최근 고점 업데이트
    if current_price > recent_high:
        update_state(session_metrics={"recent_high": current_price})
        return 0 # 고점 갱신 중일 때는 정상 오프셋 사용

    # 고점 대비 하락 폭 확인
    drop_from_high = (recent_high - current_price) / recent_high if recent_high > 0 else 0
    
    # 고점 대비 0.5% 이내로 너무 근접해 있다면 '물릴' 위험이 있다고 판단
    if drop_from_high < 0.005:
        logger.warning(f"고점 근접 경고 (고점: {recent_high}, 현재가: {current_price}). 매수 오프셋 일시 강화.")
        return 1000 # 추가 오프셋 부과
        
    return 0
