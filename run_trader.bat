@echo off
:: 프로젝트 경로로 이동
cd /d "C:\Users\witpo\OneDrive\바탕 화면\YONSEI\26-1\ECO4126 인공지능과금융공학\open-trading-api"

:: 가상환경이 있다면 활성화 (필요 시 주석 해제)
:: call .venv\Scripts\activate

:: 프로그램 실행
echo Starting Samsung Auto Trader...
python -m samsung_auto_trader.main

:: 오류 발생 시 창이 바로 닫히지 않도록 대기
if %errorlevel% neq 0 pause
