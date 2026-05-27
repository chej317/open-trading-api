import logging
import os
from datetime import datetime

def setup_logger():
    # 로그 디렉토리 생성
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 로그 파일명 (날짜 포함)
    log_filename = os.path.join(log_dir, f"trader_{datetime.now().strftime('%Y%m%d')}.log")

    # 로거 설정
    logger = logging.getLogger("samsung_auto_trader")
    logger.setLevel(logging.INFO)

    # 포맷터 설정
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # 파일 핸들러 (파일에 기록)
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # 콘솔 핸들러 (화면에 출력)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger

# 싱글톤 패턴으로 로거 제공
logger = setup_logger()
