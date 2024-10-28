from backend import app, socketio, mqtt
from backend.api.thread import *
from flask import json
from backend.db.table.table_band import *
from backend.db.service.query import *
from backend.api.crawling import *
from threading import Lock
from backend.sms.send_sms import send_warning_sms
from logger_config import app_logger


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
        
        gps_info = mqtt_data['data'].split(',')
        if len(gps_info) != 7:
            app_logger.error(f"Invalid GPS data format: {mqtt_data['data']}")
            return
        
        latitude, longitude, altitude, speed, course, sats, timestamp = gps_info
        
        # Create a GPS data object
        gps_data = {
          'bid': extAddress,
          'latitude': float(latitude),
          'longitude': float(longitude),
          'altitude': float(altitude),
          'speed': float(speed),
          'course': float(course),
          'satellites': int(float(sats)),
          'timestamp': timestamp
        }
        
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
      
    gatewayDev = db.session.query(Gateways.airpressure).\
      filter(Gateways.pid == mqtt_data['pid']).first()
    
    if gatewayDev is not None:
      sensorDev = db.session.query(WalkRunCount).\
        filter(WalkRunCount.FK_bid == dev.id).\
        filter(func.date(WalkRunCount.datetime) == func.date(datetime.datetime.now(timezone('Asia/Seoul')))).first()
      db.session.flush()

    try:
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
      print("****** error ********")
      print(e)
  else:
    insertBandData(extAddress)
    band = selectBandBid(extAddress)
    gw = selectGatewayPid(mqtt_data['pid'])
    if band is not None and gw is not None:
      insertGatewaysBands(gw.id, band.id)
      insertUsersBands(1, band.id)


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
#       d = datetime.datetime.now(timezone('Asia/Seoul'))
#       urldate = str(d.year)+"."+str(d.month) + \
#         "."+str(d.day)+"."+str(d.hour)
#       trtemp, atemp = getAirpressure(urldate)
#       if trtemp != 0:
#         updateGatewaysAirpressure(dev.id, searchAirpressure(trtemp, atemp, dev.location))
#       socketio.emit('gateway_connect', panid, namespace='/receiver')
#   except:
#       pass

@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
  print("handle mqtt msg start")
  global mqtt_thread, gw_thread, event_thread, num, thread_lock
  
  if message.topic == '/efwb/post/sync':
    num += 1
    with thread_lock:
      try: 
        if mqtt_thread is None: 
          mqtt_data = json.loads(message.payload.decode())
            
          extAddress = hex( int(str(mqtt_data['extAddress']['high'])+str(mqtt_data['extAddress']['low'])))
            
          mqtt_thread = socketio.start_background_task(handle_sync_data(mqtt_data, extAddress))
            
      except json.JSONDecodeError as e:
        logging.error(f"JSON Decode Error in sync message: {str(e)}")
        logging.debug(f"Problematic payload: {message.payload}")
      except (KeyError, ValueError) as e:
        logging.error(f"Data processing error in sync message: {str(e)}")
      except Exception as e:
        logging.error(f"Unexpected error in sync message: {str(e)}")
      finally:
        mqtt_thread = None
            
              
  elif message.topic == '/DT/eHG4/GPS/Location':
    with thread_lock:
      if mqtt_thread is None: 
        try:
          mqtt_data = json.loads(message.payload.decode())
            
          extAddress = hex( int(str(mqtt_data['extAddress']['high'])+str(mqtt_data['extAddress']['low'])))
          
          mqtt_thread = socketio.start_background_task(handle_gps_data(mqtt_data, extAddress))

        except json.JSONDecodeError as e:
          logging.error(f"JSON Decode Error in sync message: {str(e)}")
          logging.debug(f"Problematic payload: {message.payload}")
        except (KeyError, ValueError) as e:
          logging.error(f"Data processing error in sync message: {str(e)}")
        except Exception as e:
          logging.error(f"Unexpected error in sync message: {str(e)}")
        finally:
          mqtt_thread = None
              
  elif message.topic == '/efwb/post/connectcheck':
    with thread_lock:
      try: 
        if gw_thread is None:
          gw_thread = socketio.start_background_task(handle_gateway_state(json.loads(message.payload)))
      except json.JSONDecodeError as e:
        logging.error(f"JSON Decode Error in connectcheck message: {str(e)}")
      except Exception as e:
        logging.error(f"Error in connectcheck message: {str(e)}")
      finally:
        gw_thread = None

  elif message.topic == '/efwb/post/async':
    with thread_lock:
      if event_thread is None:
        
        event_data = json.loads(message.payload.decode())
        
        extAddress = hex(int(str(event_data['extAddress']['high'])+str(event_data['extAddress']['low'])))
        
        dev = db.session.query(Bands).filter_by(bid=extAddress).first()
        try: 
          if dev is not None:
            insertEvent(
              dev.id, event_data['type'], event_data['value'])
            
            send_warning_sms(
              dev_name=dev.name,
              warning_type=event_data['type'],
              value=event_data['value']
            )
            app_logger.info("Next warning.")
            
            event_socket = {
              "type": event_data['type'],
              "value": event_data['value'],
              "bid": dev.bid,
              "name": dev.name
            }
            socketio.emit('efwbasync', event_socket,namespace='/receiver')
            app_logger.debug(f"sync data = {event_socket}")
            app_logger.info(f"Successfully processed and emitted warning data for band: {extAddress}")
        except json.JSONDecodeError as e:
          logging.error(f"JSON Decode Error in async message: {str(e)}")
        except (KeyError, ValueError) as e:
          logging.error(f"Data processing error in async message: {str(e)}")
        except Exception as e:
          logging.error(f"Unexpected error in async message: {str(e)}")
        finally:
          event_thread = None
