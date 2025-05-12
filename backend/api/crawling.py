from functools import lru_cache
import re
print ("module [crawling] loaded")
from urllib.request import urlopen
from bs4 import BeautifulSoup
import requests


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
    return getWeather(location)


def getWeather(location):
    try:
        html = requests.get(
            'https://search.naver.com/search.naver?where=nexearch&sm=top_hty&fbm=1&ie=utf8&query='+location+' 날씨')
        soup = BeautifulSoup(html.text, 'html.parser')

        temp = soup.find("body")
        tempor = temp.find("div", {"class":"temperature_text"})
        status = temp.find("span", {"class": "weather before_slash"})

        min = temp.find("span", {"class": "lowest"})
        max = temp.find("span", {"class": "highest"})
        fore = temp.find_all("li",{"class": "_li"})
        
        wind = temp.find_all("dt", {"class": "term"})
        wind_strength = temp.find_all("dd", {"class": "desc"})

        sort_items = soup.find_all("div", class_="sort")

        humidity = next(
            (item.find("dd", class_="desc").text.strip()
             for item in sort_items
             if item.find("dt", class_="term") and "습도" in item.find("dt", class_="term").text),
            None
        )
        forecast = []
        
        for fo in range(4):
            if fore[fo*2].find("dt", {"class": "time"}).text == "내일":
                forecast.append({"time":"00시", "value":fore[fo*2].find("span", {"class": "num"}).text})
            else :
                forecast.append({"time":fore[fo*2].find("dt", {"class": "time"}).text, "value":fore[fo*2].find("span", {"class": "num"}).text})
        html = requests.get(
            'https://search.naver.com/search.naver?where=nexearch&sm=top_hty&fbm=1&ie=utf8&query='+location+" 미세먼지")
        soup = BeautifulSoup(html.text, 'html.parser')

        temp = soup.find("div", {"class": "air_nextday_city"})
        temp = temp.find_all("dd", {"class": "lvl"})
        
        result = {
            "city": location,
            "temp": tempor.text.replace(" 현재 온도", "").replace(" ", ""),
            "status": status.text,
            "min":min.text.replace("최저기온", ""),
            "max":max.text.replace("최고기온", ""),
            "finedust": temp[0].text,
            "ultrafinedust":temp[0].text,
            "forecast": forecast,
            "wind":wind[2].text,
            "wind_strength":wind_strength[2].text,
            "humidity": humidity
        }
        
        WeatherState.tempor = tempor.text.replace(
            " 현재 온도", "").replace(" ", "")
        WeatherState.humidity = humidity.replace('%', '').strip()
        return result
    except Exception as e:
        result={"temp": 0}
        return result
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