from datetime import datetime
from pytz import timezone
from backend.sms.soap_request import *
from logger_config import app_logger


def get_warning_info(warning_type):
    warnings = {
        0: {"type": "낙상", "severity": "위험"},
        1: {"type": "배터리 용량 부족", "severity": "경고"},
        2: {"type": "배터리 용량 주의", "severity": "알림"},
        3: {"type": "미착용", "severity": "알림"},
        4: {"type": "심박수 이상", "severity": "위험"},
        5: {"type": "수신 감도 낮음", "severity": "알림"}
    }
    return warnings.get(warning_type, {"type": "알 수 없음", "severity": "알 수 없음"})

def format_warning_message(name, warning_type):
    """경고 메시지 포맷 생성"""
    warning_info = get_warning_info(warning_type)
    return f"[{warning_info['severity']}] {name}님 {warning_info['type']} 발생했습니다."

def should_send_sms(warning_type, value):
    """SMS 전송 여부 결정 로직"""
    # 특정 조건에 따라 SMS 전송 여부 결정
    # 예: 높은 위험도의 경고만 전송
    warning_info = get_warning_info(warning_type)
    return warning_info['severity'] in ['높음']

def send_warning_sms(dev_name, warning_type, value):
    """경고 SMS 전송 함수"""
    try:
        if not should_send_sms(warning_type, value):
            return False
            
        message = format_warning_message(dev_name, warning_type)
        current_time = datetime.now(timezone('Asia/Seoul')).strftime('%Y-%m-%d %H:%M:%S')
        
        # SMS 전송 로직
        sms_id = "stscs"  
        password = "rhrorakswhr"  

        #문자 전송 예약시에 사용(option 5 에서 필수)
        reserve_date="20241008"# YYYYMMDD 형식
        reserve_time="162000"# hhmmss 형식
        
        #사용할 옵션값:
        #1 : getRemainCount,  2 : getRemainDay, 3 : getWeeklyLimit, 4 : sendSMS, 5: sendSMSReserve, 6: cancleReserve
        option =4
        
        #문자 전송 예약,예약 취소시 필수(option 5,6에서 필수)
        userdefine="abc" # 사용자가 예약을 취소할경우 식별하기 위한 값, 임의로 설정
        
        canclemode="1"#예약 취소시 모드값, 현재는 항상 1

        #문자 전송, 전송 예약시 사용(option 4,5 에서 필수)
        snd_number="0312816900" #발송 번호 ( 발송등록된 번호만 사용 가능)
        rcv_number="01089959054" #다수에게 발송시 , 로 연결하여 입력 ex) 01011112222,01022223333
        
        send_soap_request(sms_id, password, snd_number, rcv_number, message, option, reserve_date, reserve_time, userdefine, canclemode)
        
        # 로그 기록
        app_logger.info(f"[{current_time}] SMS 전송: {message}")
        return True
        
    except Exception as e:
        app_logger.info(f"SMS 전송 실패: {str(e)}")
        return False

# MQTT handler에서 사용 예시
"""
if dev is not None:
    # 기존 이벤트 처리 로직
    insertEvent(dev.id, event_data['type'], event_data['value'])
    
    # SMS 전송 처리
    send_warning_sms(
        dev_name=dev.name,
        warning_type=event_data['type'],
        value=event_data['value']
    )
"""