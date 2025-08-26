import http.client
from backend.sms.utils import *

#전송 요청 실행
def send_soap_request(sms_id, password, snd_number, rcv_number, sms_content, option,reserve_date,reserve_time,userdefine,canclemode):
    try:
        conn = http.client.HTTPConnection("webservice.youiwe.co.kr")
        if option == 1:
            soap_request = create_soap_request_getRemainCount(sms_id, password)
        elif option == 2:
            soap_request = create_soap_request_getRemainDay(sms_id, password)
        elif option == 3:
            soap_request = create_soap_request_getWeeklyLimit(sms_id, password)
        elif option == 4:
            soap_request = create_soap_request_sendSMS(sms_id, password, snd_number, rcv_number, sms_content)
        elif option == 5:
            soap_request = create_soap_request_sendSMSReserve(sms_id, password, snd_number, rcv_number, sms_content,reserve_date,reserve_time,userdefine)
            print(sms_id, password, snd_number, rcv_number, sms_content,reserve_date,reserve_time,userdefine)
        elif option == 6:
            soap_request = create_soap_request_ReserveCancle(sms_id, password,userdefine,canclemode)
        else:
            print("잘못된 옵션입니다.")
            return

        content_length = len(soap_request)
        headers = {
            'Content-Type': 'application/soap+xml; charset=utf-8',
            'Content-Length': str(content_length)
        }

        conn.request("POST", "/SMS.v.6/ServiceSMS.asmx", soap_request, headers)
        response = conn.getresponse()

        # 응답 XML 파싱
        response_data = response.read()
        
        try:
            response_xml = ET.fromstring(response_data)
            for elem in response_xml.iter():
                if elem.tag.endswith('Result'):
                    if elem.text.startswith('-'):
                        print("에러 코드:", elem.text)
                    else:
                        if option ==1 :
                            print("잔여량:", elem.text)
                        elif option ==2 :
                            print("잔여기간/잔여량:", elem.text)    
                        elif option ==3 :
                            print("주간 제한량 | URL 제한량 | 1주간 발송량 | URL 발송량:", elem.text)   
                        elif option ==4 :
                            print("전송된 문자:", elem.text)   
                        elif option ==5 :
                            print("예약 성공문자:", elem.text)   
                        elif option ==6 :
                            print("취소 성공문자:", elem.text)       
                    
        except ET.ParseError as e:
            print("XML 파싱 오류:", e)

    except http.client.HTTPException as e:
        print("HTTP 요청 오류:", e)
    except Exception as e:
        print("예기치 않은 오류:", e)
    finally:
        conn.close()
