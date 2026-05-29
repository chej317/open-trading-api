"""
유틸리티 모듈
- 호가단위(tick size) 계산 및 가격 보정
"""
import math

def get_tick_size(price):
    """
    한국 주식시장 호가단위 (2023년 1월 개정 기준)
    - 2,000원 미만: 1원
    - 2,000원 ~ 5,000원 미만: 5원
    - 5,000원 ~ 20,000원 미만: 10원
    - 20,000원 ~ 50,000원 미만: 50원
    - 50,000원 ~ 100,000원 미만: 100원
    - 100,000원 ~ 500,000원 미만: 500원
    - 500,000원 이상: 1,000원
    """
    if price < 2000:
        return 1
    elif price < 5000:
        return 5
    elif price < 20000:
        return 10
    elif price < 50000:
        return 50
    elif price < 100000:
        return 100
    elif price < 500000:
        return 500
    else:
        return 1000

def round_to_tick(price, direction="nearest"):
    """
    가격을 호가단위에 맞춰 보정
    - direction: "up" (올림), "down" (내림), "nearest" (반올림)
    """
    tick = get_tick_size(price)
    if direction == "up":
        return int(math.ceil(price / tick) * tick)
    elif direction == "down":
        return int(math.floor(price / tick) * tick)
    else:
        return int(round(price / tick) * tick)
