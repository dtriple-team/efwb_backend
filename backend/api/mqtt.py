from backend import app, socketio, mqtt
from backend.api.thread import *
from flask import json
from backend.db.table.table_band import *
from backend.db.service.query import *
from backend.api.crawling import *
from threading import Lock
from logger_config import app_logger
from datetime import timedelta
from backend.sms.send_sms import send_warning_sms


mqtt_thread = None
gw_thread = None
event_thread = None

num = 0
thread_lock = Lock()


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

# New CHU MQTT Message Parsing
def handle_gps_data(mqtt_data, extAddress):
    app_logger.debug(f"Processing GPS data: {mqtt_data}")
    try:
        # Extract the extAddress
        mqtt_data['extAddress']['low'] = extAddress
        # Find the corresponding band
        band = db.session.query(Bands).filter_by(bid=extAddress).first()
        
        if band is None:
            app_logger.warning(f"Band not found for extAddress: {extAddress}")
            return
        
        timestamp = datetime.datetime.now(timezone('Asia/Seoul'))
        
        gps_info = mqtt_data['data'].split(',')
        
        # GPS 데이터 형식에 따라 다르게 처리
        if len(gps_info) == 4:
            base_station_count, latitude, longitude, _ = gps_info
            gps_data = {
                'bid': extAddress,
                'base_station_count': int(base_station_count),
                'latitude': float(latitude),
                'longitude': float(longitude),
                'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S')
            }
        elif len(gps_info) == 7:
            latitude, longitude, altitude, speed, course, sats, _ = gps_info
            gps_data = {
                'bid': extAddress,
                'latitude': float(latitude),
                'longitude': float(longitude),
                'altitude': float(altitude),
                'speed': float(speed),
                'course': float(course),
                'satellites': int(float(sats)),
                'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S')
            }
        else:
            app_logger.error(f"Invalid GPS data format: {mqtt_data['data']}")
            return
        
        # Emit the GPS data to the frontend
        socketio.emit('ehg4_gps', gps_data, namespace='/receiver')
        app_logger.debug(f"GPS Data : {gps_data}")
        app_logger.info(f"Successfully processed and emitted GPS data for band: {extAddress}")
        
    except Exception as e:
        app_logger.error(f"Unexpected error processing eHG4 GPS data: {str(e)}", exc_info=True)

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
    socketio.emit('ehg4_data', data, namespace='/receiver')
    app_logger.info(f"Successfully emitted real-time data for band: {data['bid']}")
      
  except SQLAlchemyError as e:
    db.session.rollback()
    app_logger.error(f"Database error while saving sensor data for band {data['bid']}: {str(e)}")
  except Exception as e:
    app_logger.error(f"Unexpected error processing eHG4 data for band {data['bid']}: {str(e)}")



def handle_sync_data(mqtt_data, extAddress):
  dev = db.session.query(Bands).filter_by(bid=extAddress).first()
  if dev is not None:
    try:
      # 밴드 연결 상태 업데이트
      dev.connect_state = 1  # 1: connected
      dev.connect_time = datetime.datetime.now(timezone('Asia/Seoul'))
      db.session.commit()
      
      gatewayDev = db.session.query(Gateways.airpressure).\
        filter(Gateways.pid == mqtt_data['pid']).first()
      
      if gatewayDev is not None:
        sensorDev = db.session.query(WalkRunCount).\
          filter(WalkRunCount.FK_bid == dev.id).\
          filter(func.date(WalkRunCount.datetime) == func.date(datetime.datetime.now(timezone('Asia/Seoul')))).first()
        db.session.flush()

      mqtt_data['extAddress']['high'] = extAddress
      bandData = mqtt_data['bandData']
      data = SensorData()
      data.FK_bid = dev.id
      data.start_byte = bandData['start_byte']
      data.sample_count = bandData['sample_count']
      data.fall_detect = bandData['fall_detect']
      data.battery_level = bandData['battery_level']
      data.hrConfidence = bandData['hrConfidence']
      data.spo2Confidence = bandData['spo2Confidence']
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
      walkRunCount.datetime = datetime.datetime.now(
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
        db.session.flush()
      else:
        db.session.add(walkRunCount)
        db.session.commit()
        db.session.flush()
      data.x = bandData['x']
      data.y = bandData['y']
      data.z = bandData['z']
      data.t = bandData['t']
      data.h = bandData['h']
      # if gatewayDev is not None:
      #     if mqtt_data['bandData']['h'] != 0:
      #         mqtt_data['bandData']['h'] = getAltitude(
      #             mqtt_data['bandData']['h'], gatewayDev.airpressure)
      #         data.h = mqtt_data['bandData']['h']
      #     else:
      #         data.h = mqtt_data['bandData']['h']
      # else:
      #     data.h = mqtt_data['bandData']['h']
      data.rssi = mqtt_data['rssi']
      data.datetime = datetime.datetime.now(timezone('Asia/Seoul'))
      db.session.add(data)
      db.session.commit()
      db.session.flush()
      
      socketio.emit('efwbsync', mqtt_data, namespace='/receiver')
      app_logger.debug(f"sync data = {mqtt_data}")
      app_logger.info(f"Successfully processed and emitted sync data for band: {extAddress}")
      
    except Exception as e:
      db.session.rollback()
      app_logger.error(f"Error updating band connection status: {str(e)}")
      print("****** error ********")
      print(e)
  else:
    insertBandData(extAddress)
    band = selectBandBid(extAddress)
    gw = selectGatewayPid(mqtt_data['pid'])
    if band is not None and gw is not None:
      insertGatewaysBands(gw.id, band.id)
      insertUsersBands(1, band.id)

def check_disconnected_bands():
    with app.app_context():
        try:
            connected_bands = db.session.query(Bands).filter_by(connect_state=1).all()
            current_time = datetime.datetime.now(timezone('Asia/Seoul'))
            
            for band in connected_bands:
                # connect_time에 timezone 정보 추가
                if band.connect_time:
                    band_connect_time = band.connect_time
                    if band_connect_time.tzinfo is None:
                        band_connect_time = timezone('Asia/Seoul').localize(band_connect_time)
                    
                    if (current_time - band_connect_time) > timedelta(minutes=1):
                        band.connect_state = 0
                        band.disconnect_time = current_time
                        
                        disconnect_event = {
                            "bid": band.bid,
                            "name": band.name,
                            "disconnect_time": band.disconnect_time.strftime("%Y-%m-%d %H:%M:%S")
                        }
                        socketio.emit('band_disconnect', disconnect_event, namespace='/receiver')
                
            db.session.commit()
            app_logger.info("Successfully checked and updated disconnected bands")
            
        except Exception as e:
            db.session.rollback()
            app_logger.error(f"Error checking disconnected bands: {str(e)}")

# 백그라운드 스케줄러 설정
def start_disconnect_checker():
    """5분마다 연결 해제 상태를 체크하는 스케줄러 시작"""
    while True:
        check_disconnected_bands()                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           
        socketio.sleep(150)  # 2분 30초
    
def handle_gateway_state(panid):
  print("handle_gateway_state", panid)
  try:
    dev = selectGatewayPid(panid['panid'])
    if dev is not None:
      if dev.ip != panid['ip']:                                                                                                                                                                                                                                                                                               
        updateGatewaysIP(dev.id, panid['ip'])
      if dev.connect_state == 0:
        updateGatewaysConnect(dev.id, True)
      else:
        updateGatewaysConnectCheck(dev.id)
    else:
      insertGateway(panid)
      dev = selectGatewayPid(panid['panid'])
      d = datetime.datetime.now(timezone('Asia/Seoul'))
      urldate = str(d.year)+"."+str(d.month) + \
        "."+str(d.day)+"."+str(d.hour)
      trtemp, atemp = getAirpressure(urldate)
      if trtemp != 0:
        updateGatewaysAirpressure(dev.id, searchAirpressure(trtemp, atemp, dev.location))
      socketio.emit('gateway_connect', panid, namespace='/receiver')
  except:
      pass

@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):

  global mqtt_thread, gw_thread, event_thread, num, thread_lock
  
  if message.topic == '/efwb/post/sync':
    num += 1
    with thread_lock:
      if mqtt_thread is None: 
        mqtt_data = json.loads(message.payload.decode())
          
        extAddress = hex( int(str(mqtt_data['extAddress']['high'])+str(mqtt_data['extAddress']['low'])))
          
        mqtt_thread = socketio.start_background_task(handle_sync_data(mqtt_data, extAddress))
          
        mqtt_thread = None
            
              
  elif message.topic == '/DT/eHG4/GPS/Location':
    with thread_lock:
      if mqtt_thread is None: 
        # print(mqtt_data)
        mqtt_data = json.loads(message.payload.decode())
            
        extAddress = hex( int(str(mqtt_data['extAddress']['high'])+str(mqtt_data['extAddress']['low'])))
        
        mqtt_thread = socketio.start_background_task(handle_gps_data(mqtt_data, extAddress))

        mqtt_thread = None
              
  elif message.topic == '/efwb/post/connectcheck':
    with thread_lock:
      if gw_thread is None:
        gw_thread = socketio.start_background_task(handle_gateway_state(json.loads(message.payload)))
        gw_thread = None

  elif message.topic == '/efwb/post/async':
    with thread_lock:
      if event_thread is None:
        event_data = json.loads(message.payload.decode())
        extAddress = hex(int(str(event_data['extAddress']['high'])+str(event_data['extAddress']['low'])))
        
        dev = db.session.query(Bands).filter_by(bid=extAddress).first()
        
        if dev is not None:
          insertEvent(
            dev.id, event_data['type'], event_data['value'])
          
          send_warning_sms(
              dev_name=dev.name,
              warning_type=event_data['type'],
              value=event_data['value']
            )
          
          event_socket = {
            "type": event_data['type'],
            "value": event_data['value'],
            "bid": dev.bid,
            "name": dev.name
          }
          socketio.emit('efwbasync', event_socket,namespace='/receiver')
          app_logger.info(f"Successfully processed and emitted async event for band {dev.bid}: type={event_data['type']}, value={event_data['value']}")
          
        else:
          app_logger.warning(f"Band not found for extAddress: {extAddress}")
        event_thread = None