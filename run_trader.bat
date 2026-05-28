@echo off
:: 프로젝트 경로로 이동
cd /d "C:\Users\witpo\OneDrive\바탕 화면\YONSEI\26-1\ECO4126 인공지능과금융공학\open-trading-api"

:: 가상환경 활성화
call .venv\Scripts\activate

:: 프로그램 실행
echo Starting Samsung Auto Trader...
python -m samsung_auto_trader.main
