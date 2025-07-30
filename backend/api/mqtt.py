from backend import app, socketio, mqtt
from backend.api.thread import *
from flask import json
from backend.db.table.table_band import *
from backend.db.service.query import *
from backend.api.crawling import *
import threading
from logger_config import app_logger
from datetime import timedelta
from sqlalchemy import text
from collections import defaultdict
from backend.sms.send_sms import send_warning_sms
import time
import sys
import math
from pytz import timezone
import queue
import re
import requests
import itertools

sys.setrecursionlimit(10000)  # 재귀 제한 증가

# 캐시 저장을 위한 전역 변수 추가
last_event_cache = defaultdict(dict)
EVENT_COOLDOWN = 0.5  # 중복 처리 방지 시간 (초)

# 우선순위 큐 (priority: 낮을수록 먼저 실행)
mqtt_event_queue = queue.PriorityQueue()
background_done = threading.Event()  # 초기화 완료 이벤트
counter = itertools.count()


def mqttPublish(topic, message):
  mqtt.publish(topic, message)


def getAltitude(pressure, airpressure):  # 기압 - 높이 계산 Dtriple
  try:
      # ***분모 자리에 해면기압 정보 넣을 것!! (ex. 1018) // Dtriple
      p = (pressure / (airpressure * 100))
      b = 1 / 5.255
      alt = 44330 * (1 - p**b)

      return round(alt, 2)
  except:
      pass
def fetch_connected_band_data():
    """현재 연결된 밴드들의 위치 및 정보를 리스트로 반환 (내부 처리용)"""
    app_logger.info("연결된 밴드 데이터만 조회 시작")
    try:
        connected_bands = db.session.query(Bands).filter(
            Bands.connect_state == 1
        ).all()
        
        result = []
        for band in connected_bands:
            result.append({
                "id": band.id,
                "bid": band.bid,
                "latitude": float(band.latitude) if band.latitude is not None else None,
                "longitude": float(band.longitude) if band.longitude is not None else None,
                "name": band.name
            })
        app_logger.info(f"{len(result)}개의 밴드 데이터 반환 완료")
        return result

    except Exception as e:
        app_logger.error(f"밴드 데이터 조회 중 오류 발생: {str(e)}")
        return []
    finally:
        db.session.remove()
        
def haversine(lat1, lon1, lat2, lon2):
    # 지구 반지름 (km)
    R = 6371.0

    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c
    return distance
    
# New CHU MQTT Message Parsing
def handle_gps_data(mqtt_data, extAddress):
    app_logger.debug(f"Processing GPS data: {mqtt_data}")
    try:
        # extAddress를 low 값에 덮어쓰기
        mqtt_data['extAddress']['low'] = extAddress
        
        # 해당 band 조회
        band = db.session.query(Bands).filter_by(bid=extAddress).first()
        if band is None:
            app_logger.warning(f"Band not found for extAddress: {extAddress}")
            return
        
        timestamp = datetime.now(timezone('Asia/Seoul'))
        
        raw_data = mqtt_data['data'].strip()
        
        # 마지막 쉼표 기준으로 timestamp 분리
        gps_str, timestamp_str = raw_data.rsplit(',', 1)
        
        # gps 부분을 쉼표로 분리해서 리스트 생성
        gps_info = [x.strip() for x in gps_str.split(',')]
        
        # timestamp 문자열에서 불필요한 따옴표 제거
        timestamp_str = timestamp_str.strip().strip('"').strip("'")
        
        # gps_info 길이에 따라 처리
        if len(gps_info) == 3:  # 예: 위도, 경도, 고도
            latitude, longitude, altitude = gps_info
            speed = None
            course = None
            sats = None
        elif len(gps_info) == 4:
            latitude, longitude, altitude, speed = gps_info
            course = None
            sats = None
        elif len(gps_info) == 5:
            latitude, longitude, altitude, speed, course = gps_info
            sats = None
        elif len(gps_info) == 6:
            latitude, longitude, altitude, speed, course, sats = gps_info
        else:
            #app_logger.error(f"Invalid GPS data format: {mqtt_data['data']} with gps_info length {len(gps_info)}")
            return
        
        gps_data = {
            'bid': extAddress,
            'latitude': float(latitude),
            'longitude': float(longitude),
            'altitude': float(altitude),
            'timestamp': timestamp_str or timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }
        if speed is not None:
            gps_data['speed'] = float(speed)
        if course is not None:
            gps_data['course'] = float(course)
        if sats is not None:
            gps_data['satellites'] = int(float(sats))
        
        try:
            # DB band 조회 및 업데이트
            band = db.session.query(Bands).filter_by(bid=gps_data['bid']).first()
            if band:
                app_logger.debug(f"업데이트 전 위치 : {band.latitude}, lng={band.longitude}")

                if band.latitude is not None and band.longitude is not None:
                    distance = haversine(band.latitude, band.longitude, gps_data['latitude'], gps_data['longitude'])
                    if distance > 700:
                        app_logger.warning(f"GPS 위치 변화가 너무 큽니다: 약 {distance:.2f}km 차이, 업데이트하지 않습니다.")
                        return  # 업데이트하지 않고 함수 종료

                band.latitude = gps_data['latitude']
                band.longitude = gps_data['longitude']
                db.session.commit()
                app_logger.debug(f"업데이트 후 위치 : {band.latitude}, lng={band.longitude}")
            else:
                app_logger.warning(f"Band not found for bid: {gps_data['bid']}")
                
        except Exception as e:
            app_logger.error(f"Error updating GPS data in DB: {e}")
        finally:
          db.session.remove()
        
        # 프론트엔드에 이벤트 발행
        socketio.emit('ehg4_gps', gps_data, namespace='/admin')
        #app_logger.debug(f"GPS Data emitted: {gps_data}")
        app_logger.info(f"Successfully processed and emitted GPS data for band: {extAddress}")
        
    except Exception as e:
        app_logger.error(f"Unexpected error processing eHG4 GPS data: {str(e)}", exc_info=True)
        db.session.remove()



# def handle_gps_data(mqtt_data, extAddress):
#     app_logger.debug(f"Processing GPS data: {mqtt_data}")
#     try:
#         # Extract the extAddress
#         mqtt_data['extAddress']['low'] = extAddress
#         # Find the corresponding band
#         band = db.session.query(Bands).filter_by(bid=extAddress).first()
        
#         if band is None:
#             app_logger.warning(f"Band not found for extAddress: {extAddress}")
#             return
        
#         timestamp = datetime.now(timezone('Asia/Seoul'))
        
#         gps_info = mqtt_data['data'].split(',')
        
#         # GPS 데이터 형식에 따라 다르게 처리
#         if len(gps_info) == 4:
#             latitude, longitude, altitude, speed = gps_info
#             gps_data = {
#                 'bid': extAddress,
#                 'latitude': float(latitude),
#                 'longitude': float(longitude),
#                 'altitude': float(altitude),
#                 'speed': float(speed),
#                 'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S')
#             }
#         elif len(gps_info) == 5:
#             latitude, longitude, altitude, speed, course = gps_info
#             gps_data = {
#                 'bid': extAddress,
#                 'latitude': float(latitude),
#                 'longitude': float(longitude),
#                 'altitude': float(altitude),
#                 'speed': float(speed),
#                 'course': float(course),
#                 'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S')
#             }
#         elif len(gps_info) == 6:
#             latitude, longitude, altitude, speed, course, sats = gps_info
#             gps_data = {
#                 'bid': extAddress,
#                 'latitude': float(latitude),
#                 'longitude': float(longitude),
#                 'altitude': float(altitude),
#                 'speed': float(speed),
#                 'course': float(course),
#                 'satellites': int(float(sats)),
#                 'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S')
#             }
#         else:
#             app_logger.error(f"Invalid GPS data format: {mqtt_data['data']}")
#             return
          
#         try:
#             # gps_data 확인
#             print(f"GPS 데이터 확인: {gps_data}")
            
#             # band 조회 결과 확인
#             band = db.session.query(Bands).filter_by(bid=gps_data['bid']).first()
#             print(f"조회된 band: {band.bid if band else 'Not Found'}")
            
#             if band:
#                 print(f"업데이트 전 위치: lat={band.latitude}, lng={band.longitude}")
#                 band.latitude = gps_data['latitude']
#                 band.longitude = gps_data['longitude']
#                 db.session.commit()
#                 db.session.remove()
#                 print(f"업데이트 후 위치: lat={band.latitude}, lng={band.longitude}")
#             else:
#                 print(f"해당 bid를 가진 band를 찾을 수 없음: {gps_data['bid']}")
                
#         except Exception as e:
#             print(f"GPS 데이터 DB 업데이트 중 에러 발생: {e}")
        
#         # Emit the GPS data to the frontend
#         socketio.emit('ehg4_gps', gps_data, namespace='/admin')
#         app_logger.debug(f"GPS Data : {gps_data}")
#         app_logger.info(f"Successfully processed and emitted GPS data for band: {extAddress}")
        
#     except Exception as e:
#         app_logger.error(f"Unexpected error processing eHG4 GPS data: {str(e)}", exc_info=True)

def handle_ehg4_data(data, b_id):
  
  app_logger.debug(f"Processing GPS data: {b_id}")
  
  try:
    band = db.session.query(Bands).filter_by(bid=b_id).first()
    
    if band is None:
      app_logger.info(f"An unregistered band: {b_id}. Attempting to insert into database.")
      insert_success = insertBandData(b_id)
      if not insert_success:
        app_logger.error(f"Failed to insert new band: {b_id}")
        return  # 밴드 삽입 실패 시 함수 종료
      
      band = selectBandBid(b_id)
      if band is None:
        app_logger.error(f"Band insertion succeeded but unable to retrieve: {data['bid']}")
        return  # 밴드 조회 실패 시 함수 종료
      
    altitude = getAltitude(data['pres'])
    data['bid'] = b_id
    
    sensor_data = SensorData(
      FK_bid=band.id,
      hr=data['hr'],
      spo2=data['spo2'],
      motionFlag=data['motionFlag'],
      scdState=data['scdState'],
      activity=data['activity'],
      walk_steps=data['walk_steps'],
      run_steps=data['run_steps'],
      temperature=data['temperature'],
      altitude=altitude,
      battery_level=data['battery_level'],
      rssi_lte=data['rssi_lte']
    )
    # print(sensor_data)
      
    db.session.add(sensor_data)
    db.session.commit()
    app_logger.info(f"Successfully saved sensor data to database for band: {data['bid']}")
    
    # 실시간 데이터 전송
    socketio.emit('ehg4_data', data, namespace='/admin')
    app_logger.info(f"Successfully emitted real-time data for band: {data['bid']}")
      
  except SQLAlchemyError as e:
    db.session.rollback()
    app_logger.error(f"Database error while saving sensor data for band {data['bid']}: {str(e)}")
  except Exception as e:
    app_logger.error(f"Unexpected error processing eHG4 data for band {data['bid']}: {str(e)}")
    db.session.remove()
  finally:
    db.session.remove()



def handle_sync_data(mqtt_data, extAddress):

  app_logger.info(f"handle_sync_data called with extAddress={extAddress}")

  dev = db.session.query(Bands).filter_by(bid=extAddress).first()
  if dev is not None:
    try:
      # 밴드 연결 상태 업데이트
      dev.connect_state = 1  # 1: connected
      dev.connect_time = datetime.now(timezone('Asia/Seoul'))
      db.session.commit()
      
      # gatewayDev = db.session.query(Gateways.airpressure).\
      #   filter(Gateways.pid == mqtt_data['pid']).first()
      
      # if gatewayDev is not None:
      sensorDev = db.session.query(WalkRunCount).\
        filter(WalkRunCount.FK_bid == dev.id).\
        filter(func.date(WalkRunCount.datetime) == func.date(datetime.now(timezone('Asia/Seoul')))).first()
      db.session.commit()

      mqtt_data['extAddress']['high'] = extAddress
      bandData = mqtt_data['bandData']
      data = SensorData()
      data.FK_bid = dev.id
      # data.start_byte = bandData['start_byte']
      # data.sample_count = bandData['sample_count']
      # data.fall_detect = bandData['fall_detect']
      data.battery_level = bandData['battery_level']
      # data.hrConfidence = bandData['hrConfidence']
      # data.spo2Confidence = bandData['spo2Confidence']
      data.hr = bandData['hr']
      data.spo2 = bandData['spo2']
      data.motionFlag = bandData['motionFlag']
      data.scdState = bandData['scdState']
      data.activity = bandData['activity']

      temp_walk_steps = bandData['walk_steps']
      if sensorDev is not None:
        if sensorDev.walk_steps > bandData['walk_steps']:
          tempwalk = bandData['walk_steps'] - \
            sensorDev.temp_walk_steps

          if tempwalk > 0:
            mqtt_data['bandData']['walk_steps'] = sensorDev.walk_steps + tempwalk

          elif tempwalk < 0:
            mqtt_data['bandData']['walk_steps'] = sensorDev.walk_steps + \
              bandData['walk_steps']

          else:
            mqtt_data['bandData']['walk_steps'] = sensorDev.walk_steps

        elif sensorDev.walk_steps == bandData['walk_steps']:
          mqtt_data['bandData']['walk_steps'] = sensorDev.walk_steps
      data.walk_steps = mqtt_data['bandData']['walk_steps']
      data.temp_walk_steps = temp_walk_steps

      walkRunCount = WalkRunCount()
      walkRunCount.FK_bid = dev.id
      walkRunCount.walk_steps = mqtt_data['bandData']['walk_steps']
      walkRunCount.temp_walk_steps = temp_walk_steps

      temp_walk_steps = bandData['run_steps']
      if sensorDev is not None:
        if sensorDev.run_steps > bandData['run_steps']:
          tempwalk = bandData['run_steps'] - \
              sensorDev.temp_run_steps
          if tempwalk > 0:
              mqtt_data['bandData']['run_steps'] = sensorDev.run_steps + tempwalk

          elif tempwalk < 0:
            mqtt_data['bandData']['run_steps'] = sensorDev.run_steps + \
              bandData['run_steps']

          else:
            mqtt_data['bandData']['run_steps'] = sensorDev.run_steps

        elif sensorDev.run_steps == bandData['run_steps']:
          mqtt_data['bandData']['run_steps'] = sensorDev.run_steps

      data.run_steps = mqtt_data['bandData']['run_steps']
      data.temp_run_steps = temp_walk_steps

      walkRunCount.run_steps = mqtt_data['bandData']['run_steps']
      walkRunCount.temp_run_steps = temp_walk_steps
      walkRunCount.datetime = datetime.now(
          timezone('Asia/Seoul'))
      sensorDev = db.session.query(WalkRunCount).\
          filter(WalkRunCount.FK_bid == dev.id).first()
      if sensorDev is not None:
        db.session.query(WalkRunCount).\
          filter(WalkRunCount.FK_bid == dev.id).\
          update(dict(walk_steps=walkRunCount.walk_steps,
                      temp_walk_steps=walkRunCount.temp_walk_steps,
                      run_steps=walkRunCount.run_steps,
                      temp_run_steps=walkRunCount.temp_run_steps,
                      datetime=walkRunCount.datetime))
        db.session.commit()
      else:
        db.session.add(walkRunCount)
        db.session.commit()
      # data.x = bandData['x']
      # data.y = bandData['y']
      # data.z = bandData['z']
      # data.t = bandData['t']
      # data.h = bandData['h']
      data.move_activity = bandData['move_activity']
      data.move_cumulative_activity = bandData['move_cumulative_activity']
      data.heart_activity = bandData['heart_activity']
      data.skin_temp = bandData['skin_temp']

      data.sum_Kcal_acc = bandData.get('sum_Kcal_acc', 0)
      data.ssHr_dayMin = bandData.get('ssHr_dayMin', 255)
      data.ssHr_dayMax = bandData.get('ssHr_dayMax', 0)
      data.temperature_dayMin = bandData.get('temperature_dayMin', 255)
      data.temperature_dayMax = bandData.get('temperature_dayMax', 0)

      data.rssi = mqtt_data['rssi']
      data.datetime = datetime.now(timezone('Asia/Seoul'))
      db.session.add(data)
      db.session.commit()
      
      # Emit the sync data to the frontend
      app_logger.info(f"Emitting sync data: {mqtt_data} to namespace '/admin'")
      socketio.emit('efwbsync', mqtt_data, namespace='/admin')
      # app_logger.debug(f"sync data = {mqtt_data}")
      app_logger.info(f"Successfully processed and emitted sync data for band: {extAddress}")

    except Exception as e:
      db.session.rollback()
      app_logger.error(f"Error up dating band connection status: {str(e)}")
      print("****** error ********")
      print(e)
    finally:
      db.session.remove()
  else:
    insertBandData(extAddress)
    band = selectBandBid(extAddress)
    # gw = selectGatewayPid(mqtt_data['pid'])
    # if band is not None and gw is not None:
    #   insertGatewaysBands(gw.id, band.id)
    #   insertUsersBands(1, band.id)

def check_disconnected_bands():
    with app.app_context():
        try:
            connected_bands = db.session.query(Bands).filter_by(connect_state=1).all()
            current_time = datetime.now(timezone('Asia/Seoul'))
            
            for band in connected_bands:
                # connect_time에 timezone 정보 추가
                if band.connect_time:
                    band_connect_time = band.connect_time
                    if band_connect_time.tzinfo is None:
                        band_connect_time = timezone('Asia/Seoul').localize(band_connect_time)
                    
                    if (current_time - band_connect_time) > timedelta(minutes=30):
                        band.connect_state = 0
                        band.disconnect_time = current_time
                        
                        disconnect_event = {
                            "bid": band.bid,
                            "name": band.name,
                            "disconnect_time": band.disconnect_time.strftime("%Y-%m-%d %H:%M:%S")
                        }
                        socketio.emit('band_disconnect', disconnect_event, namespace='/admin')
                
            db.session.commit()
            app_logger.info("Successfully checked and updated disconnected bands")
            
        except Exception as e:
            db.session.rollback()
            app_logger.error(f"Error checking disconnected bands: {str(e)}")
        finally:
          db.session.remove()

# 백그라운드 스케줄러 설정
def start_disconnect_checker():
    """5분마다 연결 해제 상태를 체크하는 스케줄러 시작"""
    while True:
        check_disconnected_bands()                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           
        socketio.sleep(60*30)  # 30분
    
# def handle_gateway_state(panid):
#   print("handle_gateway_state", panid)
#   try:
#     dev = selectGatewayPid(panid['panid'])
#     if dev is not None:
#       if dev.ip != panid['ip']:                                                                                                                                                                                                                                                                                               
#         updateGatewaysIP(dev.id, panid['ip'])
#       if dev.connect_state == 0:
#         updateGatewaysConnect(dev.id, True)
#       else:
#         updateGatewaysConnectCheck(dev.id)
#     else:
#       insertGateway(panid)
#       dev = selectGatewayPid(panid['panid'])
#       d = datetime.now(timezone('Asia/Seoul'))
#       urldate = str(d.year)+"."+str(d.month) + \
#         "."+str(d.day)+"."+str(d.hour)
#       trtemp, atemp = getAirpressure(urldate)
#       if trtemp != 0:
#         updateGatewaysAirpressure(dev.id, searchAirpressure(trtemp, atemp, dev.location))
#       socketio.emit('gateway_connect', panid, namespace='/admin')
#   except:
#       pass
def publish_weather_and_warn_mqtt_by_bid(extAddress):
    """특정 밴드(bid)에 대해 현재 날씨 및 특보 정보를 MQTT로 전송"""
    try:
        # 밴드 정보 조회 및 연결 상태 업데이트
        dev = db.session.query(Bands).filter_by(bid=extAddress).first()
        if not dev:
            app_logger.warning(f"[DB] Band {extAddress} not found.")
            return

        dev.connect_state = 1  # 1: connected
        dev.connect_time = datetime.now(timezone('Asia/Seoul'))
        db.session.commit()

        # 재조회 (연결 상태 확인 포함)
        dev = db.session.query(Bands).filter(Bands.bid == extAddress, Bands.connect_state == 1).first()
        if not dev:
            app_logger.warning(f"[MQTT] Band {extAddress} not found or not connected.")
            return

        # 위치 정보 확인
        lat, lng = dev.latitude, dev.longitude
        if lat is None or lng is None:
            app_logger.warning(f"[MQTT] Band {extAddress} has missing location info.")
            return

        # 날씨 정보 조회 및 MQTT 전송
        weather = getWeatherFromCoords(lat, lng)
        if not weather or "error" in weather:
            app_logger.warning(f"[MQTT] Weather fetch failed for Band {extAddress}: {weather}")
        else:
            try:
                temp = int(float(weather["temp"]) * 100)
                feels_like = int(float(weather["feels_like"]) * 100)
                humidity = int(float(weather["humidity"]))

                topic = "/DT/eHG4/naas/Status/BandSet"
                message = f"#XMQTTSUBMSG : 0,{extAddress},{temp},{feels_like},{humidity}"
                mqtt.publish(topic, message)
                app_logger.info(f"[MQTT] Sent weather to {topic}: {message}")
            except Exception as e:
                app_logger.error(f"[MQTT] Failed to publish weather for Band {extAddress}: {e}")

        # 특보 정보 조회 및 MQTT 전송
        get_warn_weather(lat, lng)
        topic = "/DT/eHG4/naas/Status/BandSet"
        if WeatherState.warn_send_flag == 1:
            warn_msg = f"#XMQTTSUBMSG : 1,{extAddress},{WeatherState.warn_types},{WeatherState.warn_levels}"
        elif WeatherState.warn_send_flag == 2:
            warn_msg = f"#XMQTTSUBMSG : 1,{extAddress},99,99"
        else:
            warn_msg = None  # 특보 없음

        if warn_msg:
            try:
                mqtt.publish(topic, warn_msg)
                socketio.sleep(1.0)
                app_logger.info(f"[MQTT] Sent warning to {topic}: {warn_msg}")
            except Exception as e:
                app_logger.error(f"[MQTT] Publish warning failed for {extAddress}: {e}")

        # 밴드별 특보 DB 업데이트
        try:
            dev_list = db.session.query(Bands).filter(Bands.connect_state == 1).all()
            for band in dev_list:
                try:
                    warn_level = float(WeatherState.warn_levels)
                except (TypeError, ValueError):
                    warn_level = None

                if WeatherState.warn_types == 12:  # 폭염
                    band.heat_warn = warn_level
                    band.cold_warn = None
                elif WeatherState.warn_types == 3:  # 한파
                    band.heat_warn = None
                    band.cold_warn = warn_level
                else:  # 특보 없음
                    band.heat_warn = None
                    band.cold_warn = None

            db.session.commit()
            app_logger.info("[DB] Updated warning levels successfully.")
        except Exception as e:
            db.session.rollback()
            app_logger.error(f"[DB] Failed to update warning levels: {e}")

    except Exception as e:
        db.session.rollback()
        app_logger.error(f"[DB] Failed to process band {extAddress}: {e}")
    finally:
        db.session.remove()

def start_publish_weather_mqtt_to_bands():
    """30분마다 밴드별로 현재 날씨 정보를 MQTT로 전송"""
    while True:
        band_data_list = fetch_connected_band_data()

        for band in band_data_list:
            bid = band['bid']
            lat = band.get('latitude')
            lng = band.get('longitude')

            if lat is None or lng is None:
                app_logger.warning(f"Band {bid} 위치 정보 없음")
                continue

            # 밴드별 날씨 정보 조회
            weather = getWeatherFromCoords(lat, lng)
            if not weather:
                app_logger.warning(f"Band {bid} 날씨 정보 조회 실패")
                continue

            try:
                # 값 추출
                temp_val = weather.get("temp")
                feels_val = weather.get("feels_like")
                humidity_val = weather.get("humidity")

                temp = int(float(temp_val) * 100)
                feels_like = int(float(feels_val) * 100)
                humidity = int(float(humidity_val))

                # 메시지 구성
                topic = "/DT/eHG4/naas/Status/BandSet"
                message = f"#XMQTTSUBMSG : 0,{bid},{temp},{feels_like},{humidity}"

                # MQTT 전송
                mqtt.publish(topic, message)
                app_logger.info(f"[MQTT] Sent weather to {topic}: {message}")
                socketio.sleep(1.0)

            except Exception as e:
                db.session.rollback()
                app_logger.error(f"[MQTT] Failed to publish for band {bid}: {e}")
            finally:
                db.session.remove()

        socketio.sleep(60*6)  # 기존 30분 간격

def start_weather_warning_mqtt_publish_checker():
    """3분마다 기상특보가 있는지 체크해서 밴드별로 MQTT 전송 및 DB 갱신"""
    while True:
        band_data_list = fetch_connected_band_data()

        # 밴드별로 특보 조회 및 MQTT 전송
        for band in band_data_list:
            bid = band['bid']
            lat = band.get('latitude')
            lng = band.get('longitude')

            # lat, lng 먼저 체크
            if lat is None or lng is None:
                app_logger.warning(f"Band {bid} 위치 정보 없음")
                continue

            get_warn_weather(lat, lng)

            topic = "/DT/eHG4/naas/Status/BandSet"
            if WeatherState.warn_send_flag == 1:
                message = f"#XMQTTSUBMSG : 1,{bid},{WeatherState.warn_types},{WeatherState.warn_levels}"
            elif WeatherState.warn_send_flag == 2:
                message = f"#XMQTTSUBMSG : 1,{bid},99,99"
            else:
                continue  # 특보 없으면 건너뜀

            try:
                mqtt.publish(topic, message)
                socketio.sleep(1.0)
                app_logger.info(f"[MQTT] Sent to {topic}: {message}")
            except Exception as e:
                app_logger.error(f"[MQTT] Publish failed for {bid}: {e}")

        # 밴드별 특보 DB 업데이트
        try:
            dev_list = db.session.query(Bands).filter(Bands.connect_state == 1).all()
            for dev in dev_list:
                try:
                    warn_level = float(WeatherState.warn_levels)
                except (TypeError, ValueError):
                    warn_level = None

                if WeatherState.warn_types == 12:
                    dev.heat_warn = warn_level
                    dev.cold_warn = None
                elif WeatherState.warn_types == 3:
                    dev.heat_warn = None
                    dev.cold_warn = warn_level
                else:
                    dev.heat_warn = None
                    dev.cold_warn = None

            db.session.commit()
            app_logger.info("[DB] Updated warning levels successfully.")
        except Exception as e:
            db.session.rollback()
            app_logger.error(f"[DB] Failed to update warning levels: {e}")
        finally:
            db.session.remove()

        socketio.sleep(60*10)  # 기존은 20분 간격으로 체크

def publish_info_mqtt_by_bid(extAddress):
    """특정 밴드(bid)에 대해 초기 정보를 MQTT로 전송"""
    try:
        # Bands 테이블에서 bid로 밴드 정보 찾기
        dev = db.session.query(Bands).filter_by(bid=extAddress).first()
        if not dev:
            app_logger.warning(f"[MQTT] Band {extAddress} not found.")
            return

        # 연결 상태 업데이트
        dev.connect_state = 1  # connected
        dev.connect_time = datetime.now(timezone('Asia/Seoul'))
        db.session.commit()

        # 최신 SensorData 1건 조회
        latest_data = (
            db.session.query(SensorData)
            .filter_by(FK_bid=dev.id)
            .order_by(SensorData.datetime.desc())
            .first()
        )

        if not latest_data:
            app_logger.warning(f"[MQTT] No sensor data found for band ID {dev.id}")
            return

        # 오늘 날짜 기준 (KST)
        kst = timezone('Asia/Seoul')
        now = datetime.now(kst)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        # ✅ 타임존 정확히 붙이기 (localize 사용) → KST → UTC 보정
        latest_datetime = kst.localize(latest_data.datetime)

        # 🔍 디버깅 출력
        app_logger.debug(f"[MQTT] extAddress: {extAddress}")
        app_logger.debug(f"[MQTT] latest_data.datetime (original): {latest_data.datetime}")
        app_logger.debug(f"[MQTT] latest_datetime (converted): {latest_datetime}")
        app_logger.debug(f"[MQTT] today_start: {today_start}")

        if latest_datetime >= today_start:
            # 오늘 데이터이면 그대로 사용
            sum_Kcal_acc = latest_data.sum_Kcal_acc
            ssHr_dayMin = latest_data.ssHr_dayMin
            ssHr_dayMax = latest_data.ssHr_dayMax
            temperature_dayMin = latest_data.temperature_dayMin
            temperature_dayMax = latest_data.temperature_dayMax
        else:
            # 전날 데이터일 경우 초기화 값으로 대체
            sum_Kcal_acc = 0
            ssHr_dayMin = 255
            ssHr_dayMax = 0
            temperature_dayMin = 255
            temperature_dayMax = 0

        # MQTT 메시지 발행
        topic = "/DT/eHG4/naas/Status/BandSet"
        message = (
            f"#XMQTTSUB2MSG : 0,{extAddress},"
            f"{sum_Kcal_acc},{ssHr_dayMin},{ssHr_dayMax},{temperature_dayMin},{temperature_dayMax}"
        )

        mqtt.publish(topic, message)
        app_logger.info(f"[MQTT] Sent weather to {topic}: {message}")

    except Exception as e:
        db.session.rollback()
        app_logger.error(f"[MQTT] Failed to publish for Band {extAddress}: {e}")
    finally:
            db.session.remove()

# 워커 스레드 정의
def mqtt_event_worker():
    print("MQTT/Event 워커 대기 중...")
    background_done.wait()  # 백그라운드 완료까지 대기
    print("백그라운드 완료 → 메시지 처리 시작")

    while True:
        try:
            priority, _, job = mqtt_event_queue.get()
            job()
        except Exception as e:
            app_logger.error(f"[MQTT/Event Worker] Error while executing job: {e}", exc_info=True)
        finally:
            mqtt_event_queue.task_done()

# 워커 실행
threading.Thread(target=mqtt_event_worker, daemon=True).start()

# 메시지 핸들러
@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    try:
        topic = message.topic
        payload = message.payload.decode().strip()

        def enqueue(priority, job):
            mqtt_event_queue.put((priority, next(counter), job))
            app_logger.info(f"[MQTT Message Queued] Priority={priority}, Job={job.__name__ if hasattr(job,'__name__') else 'anonymous'}")

        # 일반 MQTT 메시지 → 우선순위 1
        if topic == '/DT/eHG4/naas/post/sync':
            def job():
                mqtt_data = json.loads(payload)
                extAddress = int(
                    format(mqtt_data['extAddress']['high'], 'x') +
                    format(mqtt_data['extAddress']['low'], 'x'), 16
                )
                handle_sync_data(mqtt_data=mqtt_data, extAddress=extAddress)
            enqueue(1, job)

        elif topic == '/DT/eHG4/naas/GPS/Location':
            def job():
                fixed_payload = re.sub(
                    r'("data"\s*:\s*".*?,\d+\.\d+,)"(20\d{2}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})""',
                    r'\1\2"', payload
                )
                mqtt_data = json.loads(fixed_payload)
                extAddress = int(
                    format(mqtt_data['extAddress']['high'], 'x') +
                    format(mqtt_data['extAddress']['low'], 'x'), 16
                )
                handle_gps_data(mqtt_data=mqtt_data, extAddress=extAddress)
            enqueue(1, job)

        elif topic == '/DT/eHG4/naas/WEATHER/GET':
            def job():
                mqtt_data = json.loads(payload)
                extAddress = int(
                    format(mqtt_data['extAddress']['high'], 'x') +
                    format(mqtt_data['extAddress']['low'], 'x'), 16
                )
                publish_weather_and_warn_mqtt_by_bid(extAddress)
            enqueue(1, job)

        elif topic == '/DT/eHG4/naas/INFO/GET':
            def job():
                mqtt_data = json.loads(payload)
                extAddress = int(
                    format(mqtt_data['extAddress']['high'], 'x') +
                    format(mqtt_data['extAddress']['low'], 'x'), 16
                )
                publish_info_mqtt_by_bid(extAddress)
            enqueue(1, job)

        elif topic == '/DT/eHG4/naas/post/connectcheck':
            enqueue(1, lambda: None)  # 현재 미사용

        # 이벤트 메시지 → 우선순위 0
        elif topic == '/DT/eHG4/naas/post/async':
            def job():
                event_data = json.loads(payload)
                extAddress = int(
                    format(event_data['extAddress']['high'], 'x') +
                    format(event_data['extAddress']['low'], 'x'), 16
                )

                # 중복 이벤트 체크
                cache_key = f"{extAddress}_{event_data['type']}_{event_data['value']}"
                current_time = time.time()
                if cache_key in last_event_cache and current_time - last_event_cache[cache_key] < EVENT_COOLDOWN:
                    app_logger.debug(f"Skipping duplicate event: {cache_key}")
                    return
                last_event_cache[cache_key] = current_time

                dev = db.session.query(Bands).filter_by(bid=extAddress).first()
                if dev:
                    insertEvent(dev.id, event_data['type'], event_data['value'], datetime.now(ZoneInfo('Asia/Seoul')))

                    user = db.session.query(Users).join(UsersBands).join(Bands).filter(Bands.id == dev.id).first()
                    if user and user.phone:
                        send_warning_sms(
                            dev_name=dev.name,
                            warning_type=event_data['type'],
                            value=event_data['value'],
                            rcv_number=user.phone
                        )
                    else:
                        app_logger.warning(f"No user found for band: {dev.bid}")

                    try:
                        response = requests.get("https://hdwitheye.mycafe24.com/api/v1/hook")
                        if response.status_code == 200:
                            print("Webhook 호출 성공")
                        else:
                            print(f"Webhook 호출 실패: {response.status_code}")
                    except Exception as e:
                        print(f"Webhook 호출 중 오류 발생: {e}")

                    event_socket = {
                        "type": event_data['type'],
                        "value": event_data['value'],
                        "bid": dev.bid,
                        "name": dev.name
                    }
                    socketio.emit('efwbasync', event_socket, namespace='/admin')
                    app_logger.info(f"Processed async event for band {dev.bid}: type={event_data['type']}, value={event_data['value']}")
                    db.session.remove()
                else:
                    app_logger.warning(f"Band not found for extAddress: {extAddress}")
            enqueue(0, job)  # 이벤트는 우선순위 0

    except Exception as e:
        app_logger.error(f"Error in MQTT message handler: {str(e)}", exc_info=True)
