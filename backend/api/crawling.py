from functools import lru_cache
import re
print ("module [crawling] loaded")
from urllib.request import urlopen
from bs4 import BeautifulSoup
import requests
import math
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

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

def get_province_from_coords(lat, lng):
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

            for key in ['province']:
                if key in address:
                    print(f"[openstreetmap] 요청 성공")
                    return address[key]
            
            # province가 없으면 실패 처리
            print("[Nominatim] 지역 정보 추출 실패: province 없음")
        else:
            print(f"[Nominatim] 요청 실패: {response.status_code}")
    except Exception as e:
        print(f"[Nominatim] 오류 발생: {e}")

    # 2차: Kakao API fallback
    kakao_url = f"https://dapi.kakao.com/v2/local/geo/coord2address.json?x={lng}&y={lat}"
    kakao_headers = {
        "Authorization": "akaoAK 16a6a90d4695b2fe0bc4e86724d3014d"
    }

    try:
        response = requests.get(kakao_url, headers=kakao_headers, timeout=3)
        if response.status_code != 200:
            print(f"[Kakao] 요청 실패: {response.status_code}")
            return {"error": "지역 정보 조회 실패 (Kakao)"}

        data = response.json()
        documents = data.get("documents", [])
        if not documents:
            print("[Kakao] 지역 정보 없음")
            return {"error": "지역 정보 없음 (Kakao)"}

        address_info = documents[0].get("address", {})
        province = address_info.get("region_1depth_name")
        print(f"[Kakao] 요청 성공")
        return province if province else {"error": "지역 정보 추출 실패 (Kakao)"}

    except Exception as e:
        print(f"[Kakao] 오류 발생: {e}")
        return {"error": "예외 발생 (Kakao)"}

def get_city_from_coords(lat, lng):
    # 1차: Nominatim (OpenStreetMap) API
    nominatim_url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lng}&format=json&addressdetails=1"
    nominatim_headers = {
        "User-Agent": "yourapp/1.0 (your@email.com)"
    }

    try:
        response = requests.get(nominatim_url, headers=nominatim_headers, timeout=3)
        if response.status_code == 200:
            data = response.json()
            address = data.get('address', {})

            for key in ['city', 'county', 'town', 'village']:
                if key in address:
                    print(f"[openstreetmap] 요청 성공")
                    return address[key]
        # 실패 시 Kakao API로 넘어감
    except Exception as e:
        pass  # 조용히 무시하고 Kakao로 넘어감

    # 2차: Kakao API
    kakao_url = f"https://dapi.kakao.com/v2/local/geo/coord2address.json?x={lng}&y={lat}"
    kakao_headers = {
        "Authorization": "KakaoAK 16a6a90d4695b2fe0bc4e86724d3014d"
    }

    try:
        response = requests.get(kakao_url, headers=kakao_headers, timeout=3)
        if response.status_code != 200:
            print(f"[Kakao] 요청 실패: {response.status_code}")
            return None

        data = response.json()
        documents = data.get("documents", [])
        if not documents:
            return None

        address_info = documents[0].get("address", {})
        print(f"[Kakao] 요청 성공")
        return address_info.get("region_2depth_name")

    except Exception as e:
        print(f"[Kakao] 오류 발생: {e}")
        return None

def getWeatherFromCoords(lat, lng):
    location = get_city_from_coords(lat, lng)

    if not location:
        return {"error": "주소 추출 실패"}

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
    one_hour_ago = now - timedelta(minutes=20)
    base_time = one_hour_ago.replace(minute=0, second=0, microsecond=0)
    base_date = base_time.strftime("%Y%m%d")
    base_time_str = base_time.strftime("%H%M")

    api_key = "eLg0N+xGcf5+r2k1ElFDVyQ//I70zG8QlgPfaXEtd4rWyKSeVgdd3farac8mgR9E1DzxnxoZwAawwBjZ5sW86w=="  # 실제 키 입력

    # 초단기 실황
    url1 = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst"
    params1 = {
        'serviceKey': api_key,
        'numOfRows': '100',
        'pageNo': '1',
        'dataType': 'JSON',
        'base_date': base_date,
        'base_time': base_time_str,
        'nx': nx,
        'ny': ny
    }

    # 단기예보
    now = datetime.now() - timedelta(minutes=20)
    if now.hour < 2:
        now -= timedelta(days=1)

    fcst_base_date, fcst_base_time_str = get_fcst_base_datetime(now)

    url2 = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"
    params2 = {
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
        response1 = requests.get(url1, params=params1)
        if response1.status_code != 200:
            print(f"초단기 실황 요청 실패. 상태 코드: {response1.status_code}")
            return None

        items1 = response1.json()['response']['body']['items']['item']
        weather_data = {item['category']: item['obsrValue'] for item in items1}

        response2 = requests.get(url2, params=params2)
        if response2.status_code != 200:
            print(f"단기 예보 요청 실패. 상태 코드: {response2.status_code}")
            return None

        items2 = response2.json()['response']['body']['items']['item']
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

        # 체감온도 계산
        feels_like = kma_official_feels_like(temp, humidity, wind)

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
        print(f"날씨 데이터 처리 중 오류 발생: {e}")
        return None

# 주의보, 경고, 체감온도      
def get_warn_weather(lat, lng):
    # 현재 시간 정보 설정
    now = datetime.now(ZoneInfo("Asia/Seoul"))
    base_date = now.strftime("%Y%m%d")
    
    # 지역에 따른 stnId 매핑
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
        "제주특별자치도": "184"
    }

    try:
        region = get_province_from_coords(lat, lng)
        if not region:
            return {"error": "지역 정보 조회 실패"}

        stnId = REGION_TO_STNID.get(region, "108")  # 기본값: 전국

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
            return {"error": "기상특보 조회 실패"}

        result = response.json()
        
        # 응답 코드 확인
        if 'response' in result:
            header = result['response'].get('header', {})
            result_code = header.get('resultCode')
            result_msg = header.get('resultMsg')

            # 에러 코드에 따른 처리
            if result_code != '00':  # 정상 코드가 아닌 경우
                error_messages = {
                    '01': "어플리케이션 에러",
                    '02': "데이터베이스 에러",
                    '03': "데이터 없음",
                    '04': "HTTP 에러",
                    '05': "서비스 연결 실패",
                    '10': "잘못된 요청 파라미터",
                    '11': "필수 요청 파라미터 누락",
                    '12': "해당 오픈API 서비스 없음",
                    '20': "서비스 접근 거부",
                    '21': "일시적으로 사용할 수 없는 서비스 키",
                    '22': "서비스 요청제한횟수 초과",
                    '30': "등록되지 않은 서비스키",
                    '31': "기한만료된 서비스키",
                    '32': "등록되지 않은 IP",
                    '33': "서명되지 않은 호출",
                    '99': "기타 에러"
                }
                if result_code == "03":
                    WeatherState.warn_send_flag = 2
                error_msg = error_messages.get(result_code, "알 수 없는 에러")
                return {
                    "error": f"기상청 API 오류 ({result_code}): {error_msg}",
                    "detail": result_msg
                }

            # 정상 응답이지만 데이터가 없는 경우
            if 'body' not in result['response'] or not result['response']['body'].get('items'):
                return {
                    "region": region,
                    "warnings": [],
                    "message": "현재 발효 중인 기상특보가 없습니다."
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

        
        return {"error": "기상특보 데이터 형식 오류"}

    except Exception as e:
        print(f"기상특보 조회 중 오류 발생: {e}")
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