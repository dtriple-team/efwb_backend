print ("module [crawling] loaded")
from urllib.request import urlopen
from bs4 import BeautifulSoup
import requests

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
            "temp": tempor.text.replace(" 현재 온도", "").replace(" ", ""),
            "status": status.text,
            "min":min.text.replace("최저기온", ""),
            "max":max.text.replace("최고기온", ""),
            "finedust": temp[0].text,
            "ultrafinedust":temp[0].text,
            "forecast": forecast,
            "wind":wind[2].text,
            "wind_strength":wind_strength[2].text
        }
        print(result)
        return result
    except Exception as e:
        result={"temp": 0}
        print("weather error ",e)
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