# 📊 삼성전자(005930) 자가 적응형 자동매매 — 프로젝트 README (상세)

한줄 요약

- 삼성전자(005930)를 대상으로 한국투자증권(Open API, 모의환경) REST만 사용해 동작하는 보수적 폴링 기반 자동매매 엔진. 핵심은 "Self‑Improving"(자가 최적화)으로 운영 중 파라미터를 자동 조정합니다.

목표와 제약

- 목표: 모의환경에서 안정적으로 지정가(현재가 ± offset) 매수/매도 반복, 운영 로그·성과를 로컬에 기록하고 브로커(한투) 서버와 교차검증 가능하도록 도구 제공.
- 제약: 모의투자 전용, REST 폴링만 사용(웹소켓 사용 금지), 당일 발급 토큰 재사용, API rate limit 준수.

주요 기능

1. 기본 거래 로직
   - 현재가 조회 → 매수 지정가(현재가 - BUY_OFFSET)와 매도 지정가(현재가 + SELL_OFFSET) 동시 제출
   - 주문 후 잔고/보유 확인으로 체결 검사(폴링 방식, 보수적 간격)

2. Self‑Improving (자가 최적화)
   - evaluator.py가 거래 성과(history, win rate, total pnl), 미실현손익, 단기 변동성(분봉/일봉 기반)을 종합해 점수를 매김
   - 점수에 따라 BUY_OFFSET/SELL_OFFSET, POLLING_INTERVAL 등 파라미터를 동적으로 조정
   - 파라미터 변경 내역과 성과 리포트는 self_optimization_history/에 저장
   - 변경 쿨다운과 안전 장치(최대/최소 오프셋, 손절/익절 규칙)로 과도한 적응을 방지

3. 안전·운영성
   - 토큰을 token_cache.json에 저장해 당일 재사용
   - trade_state.json에 상태(보유·주문·성과·적용 파라미터) 영속화
   - 보수적 폴링과 호출 대기(기본 60s, 내부 TR마다 rate-limit 보호)
   - 모든 주요 이벤트(토큰 재사용/갱신, 주문 요청, 체결/미체결, 오류)를 파일/콘솔 로깅

4. 검증 도구
   - verify_kis_*.py 스크립트로 KIS 모의서버에서 계좌/체결/기간별 손익을 조회해 로컬 기록과 교차검증
   - 단, 일부 TR은 모의서버에서 제한되므로 실패 케이스를 대비한 폴백 로직 포함

운영 중 계좌 변경(중요)

- 프로젝트 운영 도중 환경변수(GH_ACCOUNT)를 변경해 다른 모의계좌(예: '한투 모의투자 상시대회' 재참여)에 연결한 이력을 기록합니다.
- 변경 시 다음을 권장:
  1. 실행 전 `.env`와 `trade_state.json`의 CAN_ACCOUNT(프로그램이 실제 사용 중인 계좌) 값을 확인
  2. 계좌가 변경되면 로컬 상태와 브로커 기록(verify 스크립트)을 대조하여 불일치 여부 확인
  3. 필요 시 `trade_state.json`을 백업한 뒤 재초기화하거나 수작업으로 ODNO/보유량을 동기화
- README 및 로그는 계좌 변경 사실을 명확히 기록하도록 설계되어 있습니다.

설치 및 빠른 시작

1) 의존성 설치

```bash
pip install -r samsung_auto_trader/requirements.txt
```

2) 환경변수 설정 (`.env` 권장)

```env
GH_APPKEY="your_demo_appkey"
GH_APPSECRET="your_demo_appsecret"
GH_ACCOUNT="50012345"        # 계좌 앞 8자리 또는 8+2 포맷
GH_ACCOUNT_PRDT_CD="01"     # (모의투자 기본값: 01)
```

3) 프로그램 실행

```bash
# 프로젝트 루트에서
python -m samsung_auto_trader.main
```

운영·검증 스크립트

- 로컬 누적 손익 확인
  - python -m samsung_auto_trader.sum_state_pnl
- 당일 체결 내역 대조 (모의)
  - python -m samsung_auto_trader.verify_kis_daily_ccld
- 기간별 손익 대조
  - python -m samsung_auto_trader.verify_kis_period_profit

로그·아티팩트 위치

- token_cache.json — 토큰 캐시
- trade_state.json — 상태 및 거래 기록
- self_optimization_history/ — 자동 생성되는 성과 리포트 및 파라미터 변경 로그
- conversation_history/ — 세션/검증 관련 대화 기록(자동 보관)

안전 및 한계

- 모의투자 전용: 실전 전환 시 엔드포인트·TR_ID·리스크 파라미터 재검증 필수
- Rate limit: 모의서버는 TPS가 낮음 — 대량 조회 시 verify 스크립트는 지연(2–3s 이상)·재시도 정책 적용
- 일부 TR은 모의서버에서 사용 불가(EGW02006) 또는 제한적 결과 반환 가능 — verify 도구는 실패 케이스를 로깅
- 민감정보(.env)는 절대 커밋 금지

개발·기여 안내

- 간단한 버그·개선 제안은 이슈로 남겨주세요. 코드 수정 시에는 작은 단위로 PR을 만들어 테스트와 로그를 포함해 주시기 바랍니다.

문의

- 프로젝트 내 `conversation_history/`에 검증 기록과 대화 로그가 저장되어 있습니다. 검증 요청·교차확인 필요 시 해당 파일을 공유해 주세요.

---

작성일: 2026-06-17
