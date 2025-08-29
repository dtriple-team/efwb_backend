from functools import lru_cache
import re
print ("module [crawling] loaded")
from urllib.request import urlopen
from bs4 import BeautifulSoup
import requests
import math
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from backend.api.dfs_zone_tree import area_no_map
import urllib.parse
import urllib.request
from logger_config import app_logger
import json
import time

class WeatherState:
    location = None
    warn_types = None
    warn_levels = None
    warn_send_flag = None

def getAirpressure(date) :
    try:
        html = requests.get("https://web.kma.go.kr/weather/observation/currentweather.jsp?auto_man=m&stn=0&type=t99&reg=100&tm="+date+"%3A00&x=25&y=1")  
        
        bsObject = BeautifulSoup(html.text, "html.parser") 
        temp = bsObject.find("table", {"class": "table_develop3"})
        print(temp)
        trtemp = temp.find_all('tr')
        atemp = temp.find_all('a')
        print(trtemp, atemp)
        return trtemp, atemp
    except Exception as e:
        print(e)
        return 0, 0
def searchAirpressure(trtemp, atemp, location):

    at = 0
    for at in range(len(atemp)):
            if atemp[at].text == location:
                break
    tdtemp = trtemp[at+2].find_all('td')
    return  float(tdtemp[len(tdtemp)-1].text)

def get_province_city_from_coords(lat, lng):
    """
    lat, lng 좌표로부터 (province, city, borough) 정보를 반환하는 함수

    1차: Nominatim (OpenStreetMap)
    2차: Kakao API fallback
    """
    # 1차: Nominatim API (OpenStreetMap)
    nominatim_url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lng}&format=json&addressdetails=1"
    nominatim_headers = {
        "User-Agent": "yourapp/1.0 (your@email.com)"
    }

    try:
        response = requests.get(nominatim_url, headers=nominatim_headers, timeout=3)
        if response.status_code == 200:
            data = response.json()
            address = data.get('address', {})

            province = address.get('province') or address.get('state') or address.get('region')
            city = address.get('city') or address.get('county') or address.get('town') or address.get('village') or address.get('municipality')
            borough = address.get('borough')  # borough 별도 추출

            # province가 없지만 city가 있을 경우
            if not province and city:
                province = address.get('state') or address.get('region') or "province가 없음"
                print("[Nominatim] province 없음 → fallback 적용:", province)

            if province and city:
                print("[Nominatim] 요청 성공")
                return province, city, borough
            else:
                print("[Nominatim] 지역 정보 추출 실패: province 또는 city 없음")
        else:
            print(f"[Nominatim] 요청 실패: {response.status_code}")
    except Exception as e:
        print(f"[Nominatim] 오류 발생: {e}")

    # 2차: Kakao API fallback
    kakao_url = f"https://dapi.kakao.com/v2/local/geo/coord2address.json?x={lng}&y={lat}"
    kakao_headers = {
        "Authorization": "KakaoAK 16a6a90d4695b2fe0bc4e86724d3014d"  # 실제 REST API Key로 교체
    }

    try:
        response = requests.get(kakao_url, headers=kakao_headers, timeout=3)
        if response.status_code != 200:
            print(f"[Kakao] 요청 실패: {response.status_code}")
            return None, None, None

        data = response.json()
        documents = data.get("documents", [])
        if not documents:
            print("[Kakao] 지역 정보 없음")
            return None, None, None

        address_info = documents[0].get("address", {})
        province = address_info.get("region_1depth_name")
        city = address_info.get("region_2depth_name")
        borough = None  # Kakao 응답에서 borough는 없음

        if province and city:
            print("[Kakao] 요청 성공")
            return province, city, borough
        else:
            print("[Kakao] 지역 정보 추출 실패: province 또는 city 없음")
            return None, None, None

    except Exception as e:
        print(f"[Kakao] 오류 발생: {e}")
        return None, None, None

def get_province_city_from_coords_Kakao(lat, lng):
    # 2차: Kakao API fallback
    kakao_url = f"https://dapi.kakao.com/v2/local/geo/coord2address.json?x={lng}&y={lat}"
    kakao_headers = {
        "Authorization": "KakaoAK 16a6a90d4695b2fe0bc4e86724d3014d"  # 실제 REST API Key로 교체
    }

    try:
        response = requests.get(kakao_url, headers=kakao_headers, timeout=3)
        if response.status_code != 200:
            print(f"[Kakao] 요청 실패: {response.status_code}")
            return None, None, None

        data = response.json()
        documents = data.get("documents", [])
        if not documents:
            print("[Kakao] 지역 정보 없음")
            return None, None, None

        address_info = documents[0].get("address", {})
        province = address_info.get("region_1depth_name")
        city = address_info.get("region_2depth_name")
        borough = None  # Kakao 응답에서 borough는 없음

        if province and city:
            print("[Kakao] 요청 성공")
            return province, city, borough
        else:
            print("[Kakao] 지역 정보 추출 실패: province 또는 city 없음")
            return None, None, None

    except Exception as e:
        print(f"[Kakao] 오류 발생: {e}")
        return None, None, None

def getWeatherFromCoords(lat, lng):
    province, city, borough = get_province_city_from_coords(lat, lng)

    if not province and not city and not borough:
        return {"error": "주소 추출 실패"}

    # borough 우선, 없으면 city, 없으면 province
    if borough:
        location = f"{province} {city} {borough}"
    elif city:
        location = f"{province} {city}"
    else:
        location = province

    print("추출된 위치:", location)

    WeatherState.location = location

    return get_weather(location, lat, lng)

def latlon_to_xy(lat, lon):
    # 기상청 격자 변환 공식 (Lambert Conformal Conic Projection)
    RE = 6371.00877  # 지구 반경(km)
    GRID = 5.0       # 격자 간격(km)
    SLAT1 = 30.0     # 투영 위도1(degree)
    SLAT2 = 60.0     # 투영 위도2(degree)
    OLON = 126.0     # 기준점 경도(degree)
    OLAT = 38.0      # 기준점 위도(degree)
    XO = 43          # 기준점 X좌표(GRID)
    YO = 136         # 기준점 Y좌표(GRID)

    DEGRAD = math.pi / 180.0

    re = RE / GRID
    slat1 = SLAT1 * DEGRAD
    slat2 = SLAT2 * DEGRAD
    olon = OLON * DEGRAD
    olat = OLAT * DEGRAD

    sn = math.tan(math.pi * 0.25 + slat2 * 0.5) / \
        math.tan(math.pi * 0.25 + slat1 * 0.5)
    sn = math.log(math.cos(slat1) / math.cos(slat2)) / math.log(sn)
    sf = math.tan(math.pi * 0.25 + slat1 * 0.5)
    sf = (sf ** sn) * math.cos(slat1) / sn
    ro = math.tan(math.pi * 0.25 + olat * 0.5)
    ro = re * sf / (ro ** sn)

    ra = math.tan(math.pi * 0.25 + lat * DEGRAD * 0.5)
    ra = re * sf / (ra ** sn)
    theta = lon * DEGRAD - olon
    if theta > math.pi:
        theta -= 2.0 * math.pi
    if theta < -math.pi:
        theta += 2.0 * math.pi
    theta *= sn

    x = ra * math.sin(theta) + XO + 0.5
    y = ro - ra * math.cos(theta) + YO + 0.5

    return int(x), int(y)

def get_fcst_base_datetime(now):
    """현재 시간 기준으로 단기예보 base_time 계산"""
    base_hours = [2, 5, 8, 11, 14, 17, 20, 23]
    for hour in reversed(base_hours):
        base_candidate = now.replace(hour=hour, minute=0, second=0, microsecond=0)
        if now >= base_candidate:
            base_time = base_candidate
            break
    else:
        base_time = (now - timedelta(days=1)).replace(hour=23, minute=0, second=0, microsecond=0)

    base_date = base_time.strftime("%Y%m%d")
    base_time_str = base_time.strftime("%H%M")
    return base_date, base_time_str

def calculate_winter_feels_like(temp_c, wind_mps):
    """기상청 겨율 체감온도 공식 (2022.6.2 이후)"""
    if temp_c > 10 or wind_mps < 1.3:
        return temp_c
    v_kmph = wind_mps * 3.6
    wc = (
        13.12 +
        0.6215 * temp_c -
        11.37 * (v_kmph ** 0.16) +
        0.3965 * temp_c * (v_kmph ** 0.16)
    )
    return round(wc, 1)

def calculate_stull_tw(temp_c, rh):
    """Stull 공식 기반 습구온도 Tw 계산"""
    rh_sqrt = math.sqrt(rh + 8.313659)
    tw = (
        temp_c * math.atan(0.151977 * rh_sqrt) +
        math.atan(temp_c + rh) -
        math.atan(rh - 1.67633) +
        0.00391838 * (rh ** 1.5) * math.atan(0.023101 * rh) -
        4.686035
    )
    return tw

def calculate_summer_feels_like(temp_c, rh):
    """기상청 여름 체감온도 공식 (2022.6.2 이후)"""
    tw = calculate_stull_tw(temp_c, rh)
    fl = (
        -0.2442 +
        0.55399 * tw +
        0.45535 * temp_c -
        0.0022 * (tw ** 2) +
        0.00278 * tw * temp_c +
        3.0
    )
    return round(fl, 1)

def calculate_discomfort_index(temp_c, humidity):
    return round(0.81 * temp_c + 0.01 * humidity * (0.99 * temp_c - 14.3) + 46.3, 1)

def kma_official_feels_like(temp_c, humidity=None, wind_mps=None):
    """기상청 공식 체감온도 계산기"""
    if temp_c <= 10 and wind_mps is not None:
        return calculate_winter_feels_like(temp_c, wind_mps)
    else:
        return calculate_summer_feels_like(temp_c, humidity)

def get_weather(location, lat, lng):
    nx, ny = latlon_to_xy(lat, lng)
    now = datetime.now(ZoneInfo("Asia/Seoul"))
    one_hour_ago = now - timedelta(minutes=60)
    base_time = one_hour_ago.replace(minute=0, second=0, microsecond=0)
    base_date = base_time.strftime("%Y%m%d")
    base_time_str = base_time.strftime("%H%M")

    app_logger.warning(f"Ultra-short-term base_date: {base_date}")
    app_logger.warning(f"Ultra-short-term base_time_str: {base_time_str}")

    # API keys
    api_key = "eLg0N+xGcf5+r2k1ElFDVyQ//I70zG8QlgPfaXEtd4rWyKSeVgdd3farac8mgR9E1DzxnxoZwAawwBjZ5sW86w=="  # Public data portal
    authKey = "io4LOFUlTXmOCzhVJe15Mg"  # KMA API Hub

    ultra_url_KMA_API_Hub = "https://apihub.kma.go.kr/api/typ02/openApi/VilageFcstInfoService_2.0/getUltraSrtNcst"
    ultra_url_Public_Data_Portal = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst"

    # Ultra-short-term (KMA API Hub first)
    params_ultra_auth = {
        'pageNo': '1',
        'numOfRows': '1000',
        'dataType': 'JSON',
        'base_date': base_date,
        'base_time': base_time_str,
        'nx': nx,
        'ny': ny,
        'authKey': authKey
    }

    # Ultra-short-term (Public Data Portal fallback)
    params_ultra_service = {
        'serviceKey': api_key,
        'pageNo': '1',
        'numOfRows': '1000',
        'dataType': 'JSON',
        'base_date': base_date,
        'base_time': base_time_str,
        'nx': nx,
        'ny': ny
    }

    # Short-term forecast
    now = datetime.now(ZoneInfo("Asia/Seoul")) - timedelta(minutes=60)
    if now.hour < 2:
        now -= timedelta(days=1)
    fcst_base_date, fcst_base_time_str = get_fcst_base_datetime(now)

    # app_logger.warning(f"Short-term forecast base_date: {fcst_base_date}")
    # app_logger.warning(f"Short-term forecast base_time_str: {fcst_base_time_str}")

    url_fcst = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"
    params_fcst = {
        'serviceKey': api_key,
        'numOfRows': '1000',
        'pageNo': '1',
        'dataType': 'JSON',
        'base_date': fcst_base_date,
        'base_time': fcst_base_time_str,
        'nx': nx,
        'ny': ny
    }

    try:
        # [1] Ultra-short-term request (KMA API Hub first)
        response = requests.get(ultra_url_KMA_API_Hub, params=params_ultra_auth)
        if response.status_code != 200 or not response.text.strip():
            app_logger.warning(f"[Ultra] KMA API Hub failed. Status: {response.status_code}, retrying Public Data Portal API")
            response = requests.get(ultra_url_Public_Data_Portal, params=params_ultra_service)

        # Validate response
        if response.status_code != 200 or not response.text.strip():
            app_logger.error("Ultra-short-term request failed.")
            return None

        try:
            ultra_data = response.json()
        except json.JSONDecodeError:
            app_logger.error(f"Ultra-short-term JSON parsing failed: {response.text[:200]}")
            return None

        if ultra_data['response']['header']['resultCode'] != '00':
            app_logger.error(f"Ultra-short-term API error: {ultra_data['response']['header']['resultMsg']}")
            return None

        items1 = ultra_data['response']['body']['items']['item']
        weather_data = {item['category']: item['obsrValue'] for item in items1}

        # [2] Short-term forecast request
        response2 = requests.get(url_fcst, params=params_fcst)
        if response2.status_code != 200 or not response2.text.strip():
            app_logger.error("Short-term forecast request failed.")
            return None

        try:
            data2 = response2.json()
        except json.JSONDecodeError:
            app_logger.error(f"Short-term forecast JSON parsing failed: {response2.text[:200]}")
            return None

        if data2['response']['header']['resultCode'] != '00':
            app_logger.error(f"Short-term forecast API error: {data2['response']['header']['resultMsg']}")
            return None

        items2 = data2['response']['body']['items']['item']
        min_temp = next((item['fcstValue'] for item in items2 if item['category'] == 'TMN'), '정보 없음')
        max_temp = next((item['fcstValue'] for item in items2 if item['category'] == 'TMX'), '정보 없음')

        try:
            min_temp = int(float(min_temp))
        except (ValueError, TypeError):
            min_temp = '정보 없음'
        try:
            max_temp = int(float(max_temp))
        except (ValueError, TypeError):
            max_temp = '정보 없음'

        temp = float(weather_data.get('T1H', 0))
        wind = float(weather_data.get('WSD', 0))
        humidity = float(weather_data.get('REH', 0))

        # Feels-like temperature
        province, city, borough = get_province_city_from_coords(lat, lng)
        now = datetime.now(ZoneInfo("Asia/Seoul"))
        if 5 <= now.month <= 9:
            feels_like = fetch_uv_index_by_province_city(province, city, borough)
        else:
            feels_like = kma_official_feels_like(temp, humidity, wind)

        if feels_like is None or feels_like == 0:
            feels_like = 99.00
        else:
            try:
                feels_like = float(feels_like)
            except (ValueError, TypeError):
                feels_like = 99.00

        result = {
            "city": location,
            "temp": temp,
            "status": weather_data.get('PTY', '정보 없음'),
            "min": min_temp,
            "max": max_temp,
            "wind": wind,
            "wind_strength": weather_data.get('VEC', '정보 없음'),
            "humidity": humidity,
            "feels_like": feels_like
        }
        return result

    except Exception as e:
        app_logger.error(f"Error while processing weather data: {e}", exc_info=True)
        return None


def normalize(text):
    """
    문자열에서 공백을 제거하고 소문자로 변환
    """
    if not text:
        return ''
    return re.sub(r'\s+', '', text).lower()

def get_area_no_by_province_city(province, city, borough):
    province_norm = normalize(province)
    city_norm = normalize(city)
    borough_norm = normalize(borough)

     # 1. city 포함 여부 (예: "구미시")
    for area_no, (prov, ct) in area_no_map.items():
        if city_norm and city_norm in normalize(ct):
            return area_no

     # 2. borough 포함 여부 (예: "수성구")
    for area_no, (prov, ct) in area_no_map.items():
        if borough_norm and borough_norm in normalize(ct):
            return area_no

     # 3. province 포함 여부 (예: "경상북도")
    for area_no, (prov, _) in area_no_map.items():
        if province_norm and province_norm in normalize(prov):
            return area_no

    return None


def fetch_uv_index_by_province_city(province, city, borough):
    area_no = get_area_no_by_province_city(province, city, borough)
    if not area_no:
        app_logger.error(f"Region not found: {province} {city}")
        return None

    now = datetime.now(ZoneInfo("Asia/Seoul"))

    for hour_back in [3, 6, 9]:
        # 3시간 단위로 내림
        rounded_hour = now.replace(minute=0, second=0, microsecond=0)
        rounded_hour -= timedelta(hours=now.hour % 3 + hour_back)
        time_str = rounded_hour.strftime('%Y%m%d%H')

        base_url = 'http://apis.data.go.kr/1360000/LivingWthrIdxServiceV4/getSenTaIdxV4'
        request_code = "A44"
        service_key = "eLg0N+xGcf5+r2k1ElFDVyQ//I70zG8QlgPfaXEtd4rWyKSeVgdd3farac8mgR9E1DzxnxoZwAawwBjZ5sW86w=="

        params = {
            'serviceKey': service_key,
            'pageNo': '1',
            'numOfRows': '10',
            'dataType': 'JSON',
            'areaNo': area_no,
            'time': time_str,
            'requestCode': request_code
        }

        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            result = response.json()

            app_logger.info(f"[{province} {city}] (AreaNo: {area_no}, {request_code}, time: {time_str}) call success")

            items = result.get('response', {}).get('body', {}).get('items', {}).get('item', [])
            if not items:
                app_logger.error(f"[{province} {city}] item is empty (time: {time_str})")
                continue  # 다음 시간으로 시도

            item = items[0]
            forecast_base_str = item.get('date')
            if not forecast_base_str:
                app_logger.error(f"[{province} {city}] There is no forecast time")
                continue

            forecast_base = datetime.strptime(forecast_base_str, "%Y%m%d%H").replace(tzinfo=ZoneInfo("Asia/Seoul"))
            delta_hours = int((now - forecast_base).total_seconds() / 3600)
            hn_key = f"h{delta_hours}"

            feels_like = item.get(hn_key)
            if feels_like is not None:
                feels_like_val = float(feels_like)
                app_logger.info(f"[{province} {city}] Current perceived temperature({hn_key}): {feels_like_val}°C")
                return feels_like_val
            else:
                app_logger.error(f"[{province} {city}] {hn_key} no value")

        except requests.exceptions.HTTPError as http_err:
            app_logger.error(f"[{province} {city}] HTTP error occurred: {http_err}")
        except Exception as e:
            app_logger.error(f"[{province} {city}] call failed: {e}")

    # 모든 시도 실패
    return None


# 주의보, 경고, 체감온도      
def get_warn_weather(lat, lng):
    # 현재 시간 (서울 기준)
    now = datetime.now(ZoneInfo("Asia/Seoul"))

    # 45분 기준으로 base_time 계산
    if now.minute <= 45:
        one_hour_ago = now - timedelta(hours=1)
        base_time = one_hour_ago.replace(minute=30, second=0, microsecond=0)
    else:
        base_time = now.replace(minute=30, second=0, microsecond=0)

    # 날짜 계산: 00:45 이전이면 전날 날짜 사용
    if now.hour == 0 and now.minute <= 45:
        base_date = (now - timedelta(days=1)).strftime("%Y%m%d")
    else:
        base_date = base_time.strftime("%Y%m%d")
    
    # 지역에 따른 stnId 매핑
    REGION_NAME_NORMALIZE = {
    "서울": "서울특별시",
    "부산": "부산광역시",
    "대구": "대구광역시",
    "인천": "인천광역시",
    "광주": "광주광역시",
    "대전": "대전광역시",
    "울산": "울산광역시",
    "세종": "세종특별시",
    "경기": "경기도",
    "강원": "강원도",
    "충북": "충청북도",
    "충남": "충청남도",
    "전북": "전라북도",
    "전남": "전라남도",
    "경북": "경상북도",
    "경남": "경상남도",
    "제주": "제주특별자치도",
    "전북특별자치도": "전라북도"  # 예외 대응
    }

    REGION_TO_STNID = {
        "서울특별시": "109",
        "서울": "109",
        "인천": "109",
        "경기도": "109",
        "부산": "159",
        "부산광역시": "159",
        "울산": "159",
        "울산광역시": "159",
        "경상남도": "159",
        "대구": "143",
        "대구광역시": "143",
        "경상북도": "143",  # 108 전국 테스트
        "광주": "156",
        "광주광역시": "156",
        "전라남도": "156",
        "전라북도": "146",
        "대전": "133",
        "대전광역시": "133",
        "세종특별시": "133",
        "세종": "133",
        "충청남도": "133",
        "충청북도": "131",
        "강원도": "105",
        "제주도": "184",
        "제주특별자치도": "184",
    }

    try:
        region = get_province_city_from_coords_Kakao(lat, lng)
        if not region:
            return {"error": "Local information search failed"}

        region_key = region[0] if isinstance(region, tuple) else region
        normalized_region = REGION_NAME_NORMALIZE.get(region_key, region_key)

        stnId = REGION_TO_STNID.get(normalized_region, "108")

        #print(f"[DEBUG] 선택된 지역 키: '{region_key}' → '{normalized_region}', stnId: '{stnId}'")

        # 기상특보 API 호출
        warn_url = 'http://apis.data.go.kr/1360000/WthrWrnInfoService/getWthrWrnMsg'
        api_key = "eLg0N+xGcf5+r2k1ElFDVyQ//I70zG8QlgPfaXEtd4rWyKSeVgdd3farac8mgR9E1DzxnxoZwAawwBjZ5sW86w=="
        
        params = {
            'serviceKey': api_key,
            'pageNo': '1',
            'numOfRows': '10',
            'dataType': 'JSON',
            'stnId': stnId,
            'fromTmFc': base_date,
            'toTmFc': base_date
        }

        response = requests.get(warn_url, params=params)
        
        if response.status_code != 200:
            WeatherState.warn_send_flag = 2
            return {"error": "Failed to check weather report"}

        result = response.json()
        
        # 응답 코드 확인
        if 'response' in result:
            header = result['response'].get('header', {})
            result_code = header.get('resultCode')
            result_msg = header.get('resultMsg')

            # 에러 코드에 따른 처리
            if result_code != '00':  # 정상 코드가 아닌 경우
                error_messages = {
                    '01': "Application Error",
                    '02': "Database Error",
                    '03': "No Data",
                    '04': "HTTP Error",
                    '05': "Service Connection Failed",
                    '10': "Invalid Request Parameter",
                    '11': "Missing Required Request Parameter",
                    '12': "No Such OpenAPI Service",
                    '20': "Service Access Denied",
                    '21': "Temporarily Unavailable Service Key",
                    '22': "Exceeded Service Request Limit",
                    '30': "Unregistered Service Key",
                    '31': "Expired Service Key",
                    '32': "Unregistered IP",
                    '33': "Unsigned Call",
                    '99': "Other Error"
                }
                if result_code == "03":
                    WeatherState.warn_send_flag = 2
                error_msg = error_messages.get(result_code, "unknown error")
                WeatherState.warn_send_flag = 2
                return {
                    "error": f"Meteorological Service API error ({result_code}): {error_msg}",
                    "detail": result_msg
                }

            # 정상 응답이지만 데이터가 없는 경우
            if 'body' not in result['response'] or not result['response']['body'].get('items'):
                WeatherState.warn_send_flag = 2
                return {
                    "region": region,
                    "warnings": [],
                    "message": "There are currently no weather warnings in effect."
                }

            # 정상 데이터 처리
            items = result['response']['body'].get('items', {}).get('item', [])
            
            # 경보 타입을 번호로 매핑하는 딕셔너리
            warn_type_to_number = {
                "강풍": 1,
                "호우": 2,
                "한파": 3,
                "건조": 4,
                "폭풍해일": 5,
                "풍랑": 6,
                "태풍": 7,
                "대설": 8,
                "황사": 9,
                "폭염": 12
            }

            # 경보 수준 → 숫자 매핑
            warn_level_to_number = {
                "주의보": 0,
                "경보": 1
            }
            
            active_warnings = set() # 활성화된 경보 번호와 수준을 저장할 set

            for item in items:
                if item.get('t1'):
                    warn_parts = item['t1'].split()
                    if len(warn_parts) >= 1:
                        warn_text = warn_parts[0]

                        # 경보 수준 텍스트 추출 및 숫자 매핑
                        level_str = "경보" if "경보" in warn_text else "주의보"
                        warn_level = warn_level_to_number[level_str]

                        # 경보 타입 매핑
                        for warn_type in warn_type_to_number:
                            if warn_type in warn_text:
                                warn_number = warn_type_to_number[warn_type]
                                active_warnings.add((warn_number, warn_level))
                                WeatherState.warn_types = warn_number
                                WeatherState.warn_levels = warn_level

                                WeatherState.warn_send_flag = 1
                                break

            # set을 list로 변환하여 반환
            return list(active_warnings)

        
        return {"error": "Weather report data format error"}

    except Exception as e:
        app_logger.error(f"An error occurred while checking weather reports: {e}")
        WeatherState.warn_send_flag = 0
        return []

# def getWeather(location):
#     try:
#         html = requests.get(
#             'https://search.naver.com/search.naver?where=nexearch&sm=top_hty&fbm=1&ie=utf8&query='+location+' 날씨')
#         soup = BeautifulSoup(html.text, 'html.parser')

#         temp = soup.find("body")
#         tempor = temp.find("div", {"class":"temperature_text"})
#         status = temp.find("span", {"class": "weather before_slash"})

#         min = temp.find("span", {"class": "lowest"})
#         max = temp.find("span", {"class": "highest"})
#         fore = temp.find_all("li",{"class": "_li"})
        
#         wind = temp.find_all("dt", {"class": "term"})
#         wind_strength = temp.find_all("dd", {"class": "desc"})

#         sort_items = soup.find_all("div", class_="sort")

#         humidity = next(
#             (item.find("dd", class_="desc").text.strip()
#              for item in sort_items
#              if item.find("dt", class_="term") and "습도" in item.find("dt", class_="term").text),
#             None
#         )
#         forecast = []
        
#         for fo in range(4):
#             if fore[fo*2].find("dt", {"class": "time"}).text == "내일":
#                 forecast.append({"time":"00시", "value":fore[fo*2].find("span", {"class": "num"}).text})
#             else :
#                 forecast.append({"time":fore[fo*2].find("dt", {"class": "time"}).text, "value":fore[fo*2].find("span", {"class": "num"}).text})
#         html = requests.get(
#             'https://search.naver.com/search.naver?where=nexearch&sm=top_hty&fbm=1&ie=utf8&query='+location+" 미세먼지")
#         soup = BeautifulSoup(html.text, 'html.parser')

#         temp = soup.find("div", {"class": "air_nextday_city"})
#         temp = temp.find_all("dd", {"class": "lvl"})
        
#         result = {
#             "city": location,
#             "temp": tempor.text.replace(" 현재 온도", "").replace(" ", ""),
#             "status": status.text,
#             "min":min.text.replace("최저기온", ""),
#             "max":max.text.replace("최고기온", ""),
#             "finedust": temp[0].text,
#             "ultrafinedust":temp[0].text,
#             "forecast": forecast,
#             "wind":wind[2].text,
#             "wind_strength":wind_strength[2].text,
#             "humidity": humidity
#         }
        
#         WeatherState.tempor = tempor.text.replace(
#             " 현재 온도", "").replace(" ", "")
#         WeatherState.humidity = humidity.replace('%', '').strip()
#         return result
#     except Exception as e:
#         result={"temp": 0}
#         return result

# def getWeather(location):
#     try:
#         html = requests.get(
#             'https://search.naver.com/search.naver?where=nexearch&sm=top_hty&fbm=1&ie=utf8&query='+location+' 날씨')
#         soup = BeautifulSoup(html.text, 'html.parser')

#         temp = soup.find("body")
#         status = temp.find("p", {"class":"cast_txt"})
#         tempor = temp.find("span", {"class":"todaytemp"})
#         wind = temp.find_all("span", {"class": "num"})

#         result = {
#             "temp": str(tempor.text)+"℃",
#             "status": str(status.text).split(", ")[0],
#             "humidity":wind[1].text+"%",
#             "uv":wind[2].text,
#             "wind":wind[0].text+"m/s",
#         }
#         return result
#     except:
#         result={"temp": 0}
#         return result