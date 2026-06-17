# 🎓 ECO4126 인공지능과금융공학 기말 프로젝트
> **한국투자증권(KIS) Open API 기반 삼성전자(005930) 자가 적응형 자동매매 시스템**  
> **본 프로젝트는 한국투자증권 Open API를 활용하여 시장 변화에 동적으로 대응하는 자가 적응형(Self-Adapting) 삼성전자 자동매매 프로그램(samsung_auto_trader)을 설계 및 개발한 프로젝트 결과물입니다.**

---

## 🎯 1. 핵심 프로젝트: 삼성전자 자가 적응형 자동매매
본 리포지토리의 주 평가 산출물은 **`samsung_auto_trader/`** 폴더에 구현된 **"실시간 자가 적응형 자동매매 프로그램"**입니다. 
- **금융공학적 핵심**: 고정된 스프레드 주문의 한계를 극복하기 위해 실시간 시장 변동성(분봉/일봉 OHLCV), 미실현 손익률, 과거 승률을 종합 반영한 **Scoring System 기반의 오프셋 자동조정(Self-Improving)**을 채택했습니다.
- **안정성/리스크 관리**: **Anti-Peak(고점 매수 방지) 필터**, **Trailing Stop(수익 보존)**, **Hard Stop-Loss**를 레이어별로 배치하고, 한투 모의투자 서버의 낮은 TPS 환경을 고려한 **보수적 폴링 및 Rate limit 협동 대기**를 설계했습니다.
- **교차 검증 자동화**: 로컬 상태기록(`trade_state.json`)과 한국투자증권 브로커 서버 간의 데이터 정합성을 검증하기 위해 **체결 및 기간 손익 교차 대조 검증 스크립트**를 직접 구현했습니다.

*상세 설계 및 수식은 [samsung_auto_trader/README.md](samsung_auto_trader/README.md)를 참고해 주십시오.*

---

## 🛠️ 2. 리포지토리 폴더 구조

본 저장소는 메인 매매 프로그램과 한국투자증권 Open API를 학습/테스트하기 위한 보조 코드들로 구성되어 있습니다.

```
.
├── samsung_auto_trader/         # ★ 핵심 프로젝트: 삼성전자 자가 적응형 자동매매 프로그램
│   ├── main.py                  # 진입점
│   ├── trader.py                # 매매 루프 엔진
│   ├── evaluator.py             # 자가 적응형 파라미터 최적화 및 리스크 관리
│   ├── api_client.py            # KIS Developers REST API 클라이언트
│   ├── trade_state.json         # 로컬 거래 상태 관리 파일
│   └── verify_kis_*.py          # 로컬-서버 교차 검증 도구 모음
│
├── docs/                        # 개발 컨벤션 가이드
├── examples_llm/                  # KIS API 단일 기능별 테스트 예제 (보조용)
├── examples_user/                 # KIS API 통합 호출 함수 및 예제 (보조용)
├── kis_devlp.yaml               # API 접속 설정 템플릿
├── pyproject.toml               # 의존성 관리 설정
└── uv.lock                      # 의존성 락 파일
```


## 3. 사전 환경설정 안내

### 3.1. Python 환경 요구사항

- **Python 3.11 이상** 필요
- **uv** **패키지 매니저 사용** 권장 (빠르고 간편한 의존성 관리)

### 3.2. uv 설치 방법

- 간편 설정을 위해 uv를 권장합니다

```bash
# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# 설치 확인
uv --version
# uv 0.x.x ... -> 설치 완료
```

### 3.3. 프로젝트 클론 및 환경 설정

```bash
# 저장소 클론
git clone https://github.com/koreainvestment/open-trading-api
cd open-trading-api

# uv를 사용한 의존성 설치 - 한줄로 끝
uv sync
```

### 3.4. KIS Open API 신청 및 설정

🍀 [서비스 신청 안내 바로가기](https://apiportal.koreainvestment.com/about-howto)
1. 한국투자증권 **계좌 개설 및 ID 연결**
2. 한국투자증권 홈페이지 or 앱에서 **Open API 서비스 신청**
3. **앱키(App Key)**, **앱시크릿(App Secret)** 발급
4. **모의투자** 및 **실전투자** 앱키 각각 준비

### 3.5. kis_devlp.yaml 설정

- 본인의 계정 설정을 위해 `kis_devlp.yaml` 파일을 수정합니다.
- 기본 경로는 `~/KIS/config/kis_devlp.yaml`입니다. 폴더가 없으면 생성해 주세요.
- 프로젝트 루트의 `kis_devlp.yaml`을 `~/KIS/config/`로 복사한 뒤 수정하는 것을 권장합니다.
- 경로를 변경하고 싶다면 `kis_auth.py`의 `config_root` 값을 수정하면 됩니다.

```bash
# 설정 폴더 생성 및 파일 복사
mkdir -p ~/KIS/config
cp kis_devlp.yaml ~/KIS/config/
```

1. `~/KIS/config/kis_devlp.yaml` 파일 열기
2. **앱키와 앱시크릿** 정보 입력
3. **HTS ID** 정보 입력
4. **계좌번호** 정보 입력 (앞 8자리와 뒤 2자리 구분)
5. **저장** 후 닫기

```yaml
# 실전투자
my_app: "여기에 실전투자 앱키 입력"
my_sec: "여기에 실전투자 앱시크릿 입력"

# 모의투자
paper_app: "여기에 모의투자 앱키 입력"
paper_sec: "여기에 모의투자 앱시크릿 입력"

# HTS ID(KIS Developers 고객 ID) - 체결통보, 나의 조건 목록 확인 등에 사용됩니다.
my_htsid: "사용자 HTS ID"

# 계좌번호 앞 8자리
my_acct_stock: "증권계좌 8자리"
my_acct_future: "선물옵션계좌 8자리"
my_paper_stock: "모의투자 증권계좌 8자리"
my_paper_future: "모의투자 선물옵션계좌 8자리"

# 계좌번호 뒤 2자리
my_prod: "01" # 종합계좌
# my_prod: "03" # 국내선물옵션 계좌
# my_prod: "08" # 해외선물옵션 계좌
# my_prod: "22" # 개인연금 계좌
# my_prod: "29" # 퇴직연금 계좌

# User-Agent(기본값 사용 권장, 변경 불필요)
my_agent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
```

## 4. 프로그램 실행 및 검증 방법

### 4.1. 환경 변수 설정 (.env)
프로젝트 루트 경로에 `.env` 파일을 생성하고 아래 정보를 기입합니다:
```env
GH_APPKEY="발급받은_모의투자_AppKey"
GH_APPSECRET="발급받은_모의투자_AppSecret"
GH_ACCOUNT="모의투자_계좌번호_8자리"
GH_ACCOUNT_PRDT_CD="01"
```

### 4.2. 실행 방법
```bash
# 의존성 패키지 설치
pip install -r samsung_auto_trader/requirements.txt

# 자가 적응형 자동매매 프로그램 실행
python -m samsung_auto_trader.main
```

### 4.3. 사후 검증 도구 구동
로컬 거래 상태(`trade_state.json`)와 KIS 실제 서버 데이터를 교차 검증하기 위해 아래 도구들을 사용할 수 있습니다:
```bash
# 로컬 누적 손익 확인
python -m samsung_auto_trader.sum_state_pnl

# 당일 KIS 서버 체결 내역 대조 검증
python -m samsung_auto_trader.verify_kis_daily_ccld

# 기간별 KIS 서버 실손익 대조 검증
python -m samsung_auto_trader.verify_kis_period_profit
```

---

## 5. 문제 해결 가이드 (FAQ)

- **초당 거래건수 초과 (`EGW00201`)**
  - KIS 모의투자 서버는 초당 호출수(TPS) 제한이 매우 낮습니다. 우리 프로그램은 기본 루프 대기(60초) 및 에러 시 쿨타임(2~3초)을 통해 TPS를 보수적으로 자동 조절하지만, 수동 검증 스크립트를 연속 실행할 경우 일시적으로 발생할 수 있습니다. 수 초 대기 후 재실행해 주십시오.
- **계좌 정보 불일치 오류**
  - 중간에 모의투자 계좌를 다른 대회나 계정으로 변경했을 경우 `trade_state.json` 내의 계좌 필드(`"CAN_ACCOUNT"`)와 `.env` 파일의 `GH_ACCOUNT`가 다를 수 있습니다. 이 경우 기존 `trade_state.json`을 삭제하거나 백업한 뒤 다시 프로그램을 실행하면 정상 구동됩니다.
- **프로그램 로컬 수익과 실제 KIS 계좌 잔고상 수익의 불일치**
  - 세금/수수료 누락, 한투 서버의 이동평균법 평단가 조정 방식 차이, 모의체결 서버 지연 등에 따른 실무적 괴리입니다. 또한 모의투자 환경에서는 API 안정성 및 호출 제한(TPS) 이슈로 교차 검증 스크립트 실행이 제한될 수 있습니다. 자세한 원인 분석 및 해결 방안은 [samsung_auto_trader/README.md](samsung_auto_trader/README.md#7-실무적-한계-및-교차-검증상의-이슈-limitations--verification-issues)를 참고해 주십시오.


