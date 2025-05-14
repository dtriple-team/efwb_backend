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
    tempor = None
    humidity = None
    

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


def get_city_from_coords(lat, lng):
    url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lng}&format=json&addressdetails=1"
    headers = {
        "User-Agent": "yourapp/1.0 (your@email.com)"
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return None

        data = response.json()
        address = data.get('address', {})

        # 우선순위대로 시/군/구 키 확인
        for key in ['city', 'county', 'town', 'village']:
            if key in address:
                return address[key]

        return None
    except Exception as e:
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
    """
    현재 시간 기준으로 단기예보 base_time을 계산한다.
    단기예보는 02, 05, 08, 11, 14, 17, 20, 23시에 갱신되므로
    그 중 가장 가까운 이전 시각을 선택해야 한다.
    """
    base_hours = [2, 5, 8, 11, 14, 17, 20, 23]
    for hour in reversed(base_hours):
        base_candidate = now.replace(hour=hour, minute=0, second=0, microsecond=0)
        if now >= base_candidate:
            base_time = base_candidate
            break
    else:
        # 새벽 0~1시: 전날 23시 사용
        base_time = (now - timedelta(days=1)).replace(hour=23, minute=0, second=0, microsecond=0)

    base_date = base_time.strftime("%Y%m%d")
    base_time_str = base_time.strftime("%H%M")
    return base_date, base_time_str

def get_weather(location, lat, lng):
    nx, ny = latlon_to_xy(lat, lng)
    now = datetime.now(ZoneInfo("Asia/Seoul"))
    one_hour_ago = now - timedelta(hours=1)
    base_time = one_hour_ago.replace(minute=0, second=0, microsecond=0)
    print("now =", now)
    print("base_time =", base_time)
    base_date = base_time.strftime("%Y%m%d")
    base_time_str = base_time.strftime("%H%M")

    
    api_key = "eLg0N+xGcf5+r2k1ElFDVyQ//I70zG8QlgPfaXEtd4rWyKSeVgdd3farac8mgR9E1DzxnxoZwAawwBjZ5sW86w=="  # 여기에 실제 API 키 입력

    # ✅ 초단기 실황 (현재 날씨)
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

    # ✅ 단기 예보 (최저/최고 기온)
    fcst_base_time = now
    if now.hour < 2:
        fcst_base_time -= timedelta(days=1)
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
        # 초단기 실황 요청
        response1 = requests.get(url1, params=params1)
        if response1.status_code == 200:
            print("초단기 실황 응답:")  # 응답 내용 출력 (디버깅 용)
            #print("초단기 실황 응답:", response1.text)  # 응답 내용 출력 (디버깅 용)
        else:
            print(f"초단기 실황 요청 실패. 상태 코드: {response1.status_code}")
            return None

        items1 = response1.json()['response']['body']['items']['item']
        weather_data = {item['category']: item['obsrValue'] for item in items1}

        # 단기 예보 요청 (최저/최고 기온)
        response2 = requests.get(url2, params=params2)
        if response2.status_code == 200:
            print("단기 예보 응답:")  # 응답 내용 출력 (디버깅 용)
            #print("단기 예보 응답:", response2.text)  # 응답 내용 출력 (디버깅 용)
        else:
            print(f"단기 예보 요청 실패. 상태 코드: {response2.status_code}")
            return None

        items2 = response2.json()['response']['body']['items']['item']
        min_temp = next((item['fcstValue'] for item in items2 if item['category'] == 'TMN'), '정보 없음')
        max_temp = next((item['fcstValue'] for item in items2 if item['category'] == 'TMX'), '정보 없음')

        result = {
            "city": location,
            "temp": weather_data.get('T1H', '정보 없음'),
            "status": weather_data.get('PTY', '정보 없음'),
            "min":min_temp,
            "max":max_temp,
            "wind": weather_data.get('WSD', '정보 없음'),
            "wind_strength": weather_data.get('VEC', '정보 없음'),
            "humidity": weather_data.get('REH', '정보 없음'),
        }
        WeatherState.tempor = weather_data.get('T1H', '정보 없음'),
        WeatherState.humidity = weather_data.get('REH', '정보 없음')

        return result

    except Exception as e:
        print(f"날씨 데이터 처리 중 오류 발생: {e}")
        return None
        
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