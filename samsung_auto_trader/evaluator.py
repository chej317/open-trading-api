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

def calculate_atr(prices, high_prices, low_prices, period=15):
    """최근 N분간의 ATR(Average True Range) 계산"""
    if len(prices) < period + 1:
        return None
    
    tr_list = []
    for i in range(len(prices) - period, len(prices)):
        high = high_prices[i]
        low = low_prices[i]
        prev_close = prices[i-1]
        
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        tr_list.append(tr)
        
    return sum(tr_list) / period

def evaluate_and_adapt(price_data=None, client=None, symbol=None):
    """
    종합 점수제(Scoring System) 기반의 자가 적응형 전략 평가 및 수정
    """
    state = load_state()
    history = state.get("history", [])
    performance = state.get("performance", {})
    unrealized = state.get("unrealized_metrics", {})
    
    # 쿨다운 체크
    now = datetime.now()
    last_adapt_str = state.get("last_adapt_time")
    if last_adapt_str:
        last_adapt = datetime.strptime(last_adapt_str, "%Y-%m-%d %H:%M:%S")
        if (now - last_adapt).total_seconds() < 1200: # 20분으로 단축 (반응성 강화)
            return

    old_params = state.get("adapted_params", {}).copy()
    if old_params.get("buy_offset") is None: old_params["buy_offset"] = BUY_OFFSET
    if old_params.get("sell_offset") is None: old_params["sell_offset"] = SELL_OFFSET
    
    # ---------------------------------------------------------
    # 가중치 점수 산정 (Positive: 오프셋 확대/보수적, Negative: 오프셋 축소/공격적)
    # ---------------------------------------------------------
    total_score = 0
    reasons = []

    # 1. 미실현 손익 요인 (무게중심: 리스크 관리)
    current_ratio = unrealized.get("current_ratio", 0)
    if current_ratio <= -2.0:
        total_score += 20
        reasons.append(f"미실현 손실({current_ratio}%)")
    elif current_ratio >= 1.5:
        total_score -= 10
        reasons.append(f"수익권 진입({current_ratio}%)")

    # 2. 실시간 ATR 변동성 요인 (최근 15분)
    if client and symbol:
        from .market_data import get_minute_ohlcv
        # ATR 계산을 위해 OHLC 데이터를 위해 추가 API 호출이 필요할 수 있으나, 
        # 여기서는 단순화를 위해 현재가 기반 변동폭을 사용하거나 market_data를 확장합니다.
        # 일단은 기존 price_data를 활용한 단기 변동성으로 점수화
        if price_data:
            curr_price = price_data["price"]
            # 임시로 고저차 활용 (향후 ATR로 정교화 가능)
            vol = (price_data["high"] - price_data["low"]) / curr_price if curr_price > 0 else 0
            if vol > 0.02: # 변동성 큼
                total_score += 15
                reasons.append(f"시장 변동성 확대({vol:.1%})")
            elif vol < 0.005: # 매우 정적인 시장
                total_score -= 15
                reasons.append(f"시장 정체({vol:.1%})")

    # 3. 과거 승률/성과 요인 (최근 5회 기준)
    if len(history) >= 3:
        win_rate = performance.get("win_rate", 0)
        total_pnl = performance.get("total_pnl", 0)
        if total_pnl < 0:
            total_score += 15
            reasons.append("누적 손실 발생")
        elif win_rate > 70:
            total_score -= 10
            reasons.append("우수한 승률 유지")

    # ---------------------------------------------------------
    # 최종 파라미터 결정
    # ---------------------------------------------------------
    new_params = old_params.copy()
    
    # 점수 1점당 오프셋 50원 단위 조정 (예시)
    offset_adjustment = total_score * 50
    
    new_params["buy_offset"] = max(1000, min(10000, BUY_OFFSET + offset_adjustment))
    new_params["sell_offset"] = max(1000, min(10000, SELL_OFFSET + (offset_adjustment // 2)))

    if reasons and new_params != old_params:
        reason_str = ", ".join(reasons)
        update_state(
            adapted_params=new_params,
            last_adapt_time=now.strftime("%Y-%m-%d %H:%M:%S")
        )
        log_adaptation(f"종합 점수 기반 조정: {reason_str} (합계 점수: {total_score})", 
                       old_params, new_params, performance, history)

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

def calculate_ma(prices, period=20):
    """이동평균 계산"""
    if len(prices) < period:
        return None
    return sum(prices[-period:]) / period

def calculate_rsi(prices, period=14):
    """RSI(상대강도지표) 계산"""
    if len(prices) < period + 1:
        return None
    
    deltas = [prices[i+1] - prices[i] for i in range(len(prices)-1)]
    gains = [d if d > 0 else 0 for d in deltas]
    losses = [-d if d < 0 else 0 for d in deltas]
    
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    
    if avg_loss == 0:
        return 100
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def check_anti_peak(client, symbol, current_price):
    """
    이격도 및 RSI 기반 고점 매수 방지 로직 (분봉/일봉 복합)
    단기 및 거시 과열 상태일 경우 매수 오프셋을 강화하여 관망 유도.
    """
    extra_offset = 0
    warning_msgs = []
    
    from .market_data import get_minute_ohlcv, get_daily_ohlcv
    
    # 1. 단기 과열 체크 (분봉 기준)
    min_prices = get_minute_ohlcv(client, symbol, count=30)
    if min_prices:
        ma20_min = calculate_ma(min_prices, 20)
        disparity_min = (current_price / ma20_min * 100) if ma20_min else 100
        rsi_min = calculate_rsi(min_prices, 14)
        
        if rsi_min and rsi_min >= 70:
            extra_offset += 1500
            warning_msgs.append(f"분봉 RSI 과매수({rsi_min:.1f})")
        if disparity_min > 101.5:
            extra_offset += 1000
            warning_msgs.append(f"분봉 이격도 과열({disparity_min:.1f}%)")

    # 2. 거시 과열 체크 (일봉 기준 - 20일 이평선 및 일일 RSI)
    daily_prices = get_daily_ohlcv(client, symbol, count=35)
    if daily_prices:
        ma20_daily = calculate_ma(daily_prices, 20)
        disparity_daily = (current_price / ma20_daily * 100) if ma20_daily else 100
        rsi_daily = calculate_rsi(daily_prices, 14)
        
        # 일봉 기준 강력한 고점 시그널 (20일선 대비 5% 이상 상방 이격 또는 RSI 70 이상)
        if rsi_daily and rsi_daily >= 70:
            extra_offset += 3000
            warning_msgs.append(f"일봉 RSI 과매수({rsi_daily:.1f})")
        
        if disparity_daily > 105.0:
            extra_offset += 5000 # 강력한 오프셋 추가
            warning_msgs.append(f"20일선 이격도 과다({disparity_daily:.1f}%)")
        elif disparity_daily > 103.0:
            extra_offset += 2000
            warning_msgs.append(f"20일선 이격도 주의({disparity_daily:.1f}%)")

    if extra_offset > 0:
        logger.warning(f"⚠️ 종합 고점 매수 방지 작동: {', '.join(warning_msgs)}. 총 오프셋 +{extra_offset}원 추가.")
    
    return extra_offset
