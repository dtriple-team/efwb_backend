import hashlib
import xml.etree.ElementTree as ET

#해시값 생성
def calc_hash(data):
    encoded_string = data.encode('utf-8')
    hash_value = hashlib.md5(encoded_string).hexdigest()
    return hash_value

#잔여 문자 개수 조회  SOAP XML
def create_soap_request_getRemainCount(sms_id,password):
    envelope = ET.Element("{http://www.w3.org/2003/05/soap-envelope}Envelope")
    body = ET.SubElement(envelope, "{http://www.w3.org/2003/05/soap-envelope}Body")
    method = ET.SubElement(body, "GetRemainCount", xmlns="http://webservice.youiwe.co.kr/")
    
    child_sms_id = ET.SubElement(method, "smsID")
    child_sms_id.text = sms_id
    child_hash_value = ET.SubElement(method, "hashValue")
    child_hash_value.text = calc_hash(sms_id+password)
    return ET.tostring(envelope, encoding='utf-8')

#주간 전송 제한량 조회  SOAP XML
def create_soap_request_getWeeklyLimit(sms_id,password):
    envelope = ET.Element("{http://www.w3.org/2003/05/soap-envelope}Envelope")
    body = ET.SubElement(envelope, "{http://www.w3.org/2003/05/soap-envelope}Body")
    method = ET.SubElement(body, "GetWeeklyLimit", xmlns="http://webservice.youiwe.co.kr/")
    
    child_sms_id = ET.SubElement(method, "smsID")
    child_sms_id.text = sms_id
    child_hash_value = ET.SubElement(method, "hashValue")
    child_hash_value.text = calc_hash(sms_id+password)
    return ET.tostring(envelope, encoding='utf-8')

#문자 잔여 기간 조회  SOAP XML
def create_soap_request_getRemainDay (sms_id,password):
    envelope = ET.Element("{http://www.w3.org/2003/05/soap-envelope}Envelope")
    body = ET.SubElement(envelope, "{http://www.w3.org/2003/05/soap-envelope}Body")
    method = ET.SubElement(body, "GetRemainDay", xmlns="http://webservice.youiwe.co.kr/")
    
    child_sms_id = ET.SubElement(method, "smsID")
    child_sms_id.text = sms_id
    child_hash_value = ET.SubElement(method, "hashValue")
    child_hash_value.text = calc_hash(sms_id+password)
    return ET.tostring(envelope, encoding='utf-8')


#SMS 전송  SOAP XML
def create_soap_request_sendSMS(sms_id, password, snd_number, rcv_number, sms_content):
    envelope = ET.Element("{http://www.w3.org/2003/05/soap-envelope}Envelope")
    body = ET.SubElement(envelope, "{http://www.w3.org/2003/05/soap-envelope}Body")
    method = ET.SubElement(body, "SendSMS", xmlns="http://webservice.youiwe.co.kr/")

    child_sms_id = ET.SubElement(method, "smsID")
    child_sms_id.text = sms_id
    child_hash_value = ET.SubElement(method, "hashValue")
    child_hash_value.text = calc_hash(sms_id + password+rcv_number)
    child_snd_number = ET.SubElement(method, "senderPhone")
    child_snd_number.text = snd_number
    child_rcv_number = ET.SubElement(method, "receivePhone")
    child_rcv_number.text = rcv_number
    child_sms_content = ET.SubElement(method, "smsContent")
    child_sms_content.text = sms_content
    return ET.tostring(envelope, encoding='utf-8')

#SMS 전송 예약  SOAP XML
def create_soap_request_sendSMSReserve(sms_id, password, snd_number, rcv_number, sms_content,reserve_date,reserve_time,userdefine):
    envelope = ET.Element("{http://www.w3.org/2003/05/soap-envelope}Envelope")
    body = ET.SubElement(envelope, "{http://www.w3.org/2003/05/soap-envelope}Body")
    method = ET.SubElement(body, "SendSMSReserve", xmlns="http://webservice.youiwe.co.kr/")

    child_sms_id = ET.SubElement(method, "smsID")
    child_sms_id.text = sms_id
    child_hash_value = ET.SubElement(method, "hashValue")
    child_hash_value.text = calc_hash(sms_id + password+rcv_number)
    child_snd_number = ET.SubElement(method, "senderPhone")
    child_snd_number.text = snd_number
    child_rcv_number = ET.SubElement(method, "receivePhone")
    child_rcv_number.text = rcv_number
    child_sms_content = ET.SubElement(method, "smsContent")
    child_sms_content.text = sms_content
    child_reserve_date = ET.SubElement(method, "reserveDate")
    child_reserve_date.text = reserve_date
    child_reserve_time = ET.SubElement(method, "reserveTime")
    child_reserve_time.text = reserve_time
    child_userdefine = ET.SubElement(method, "userDefine")
    child_userdefine.text = userdefine
    return ET.tostring(envelope, encoding='utf-8')

#SMS 예약 전송 취소 SOAP XML 
def create_soap_request_ReserveCancle(sms_id, password, userdefine, canclemode):
    envelope = ET.Element("{http://www.w3.org/2003/05/soap-envelope}Envelope")
    body = ET.SubElement(envelope, "{http://www.w3.org/2003/05/soap-envelope}Body")
    method = ET.SubElement(body, "ReserveCancle", xmlns="http://webservice.youiwe.co.kr/")

    child_sms_id = ET.SubElement(method, "smsID")
    child_sms_id.text = sms_id
    child_hash_value = ET.SubElement(method, "hashValue")
    child_hash_value.text = calc_hash(sms_id + password+userdefine)
    child_userdefine = ET.SubElement(method, "searchValue")
    child_userdefine.text = userdefine
    child_canclemode = ET.SubElement(method, "mode")
    child_canclemode.text = canclemode
    return ET.tostring(envelope, encoding='utf-8')