import sys
from .auth import get_access_token
from .api_client import KISClient
from .trader import run_trading_loop
from .logger import logger

def main():
    try:
        # 1. 토큰 발급
        access_token = get_access_token()
        if not access_token:
            logger.error("토큰 발급 실패로 프로그램을 종료합니다.")
            sys.exit(1)

        # 2. 클라이언트 초기화
        client = KISClient(access_token)

        # 3. 매매 루프 시작
        run_trading_loop(client)

    except KeyboardInterrupt:
        logger.info("사용자에 의해 프로그램이 중단되었습니다.")
    except Exception as e:
        logger.error(f"프로그램 실행 중 치명적 오류 발생: {e}")
    finally:
        logger.info("프로그램을 종료합니다.")

if __name__ == "__main__":
    main()
