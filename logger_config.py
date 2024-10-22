import logging
from logging.handlers import RotatingFileHandler
import json
from datetime import datetime
from pytz import timezone


class JsonFormatter(logging.Formatter):
    def format(self, record):
        seoul_tz = timezone('Asia/Seoul')
        timestamp = datetime.fromtimestamp(record.created, seoul_tz)
        formatted_timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]  # 소수점 셋째자리까지 표시
        
        log_record = {
            'timestamp': formatted_timestamp,
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'funcName': record.funcName,
            'lineNo': record.lineno
        }
        if record.exc_info:
            log_record['exception'] = self.formatException(record.exc_info)
        return json.dumps(log_record)

def setup_logger(name, log_file, level=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_format = logging.Formatter('%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    console_handler.setFormatter(console_format)

    # File Handler with Rotation
    file_handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(JsonFormatter())

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger

# 전역 로거 생성
app_logger = setup_logger('app_logger', 'server_log.json', logging.DEBUG)

# 로깅 레벨 설정 예:
# logging.DEBUG     # 모든 레벨의 로그 메시지를 출력
# logging.INFO      # INFO 레벨 이상의 로그 메시지를 출력
# logging.WARNING   # WARNING 레벨 이상의 로그 메시지를 출력
# logging.ERROR     # ERROR 레벨 이상의 로그 메시지를 출력
# logging.CRITICAL  # CRITICAL 레벨의 로그 메시지만 출력