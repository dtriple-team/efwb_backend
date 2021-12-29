from backend import app, socketio, mqtt, thread_lock
from backend.api.thread import *
from flask import make_response, jsonify, request, json
from backend.db.table.table_band import *
from backend.db.service.query import *
from backend.api.socket import *

mqtt_thread = None
gw_thread = None

def mqttPublish(topic, message):
    mqtt.publish(topic, message)
def getAltitude(pressure, airpressure): # 기압 - 높이 계산 Dtriple
  try:
    p = (pressure / (airpressure * 100)); # ***분모 자리에 해면기압 정보 넣을 것!! (ex. 1018) // Dtriple
    b = 1 / 5.255
    alt = 44330 * (1 - p**b)
 
    return round(alt,2)
  except:
    pass
def handle_sync_data(mqtt_data, extAddress):
  # print("start handle_sync_data")
  # global spo2BandData
  # startTime = datetime.datetime.now()
  dev = db.session.query(Bands).filter_by(bid = extAddress).first()
  
  if dev is not None:
    # print("dev")
    gatewayDev = db.session.query(Gateways.airpressure).\
      filter(Gateways.id == GatewaysBands.FK_pid).\
        filter(GatewaysBands.FK_bid == dev.id).first()
    # print("gatewayDev")    
    sensorDev = db.session.query(WalkRunCount).\
      filter(WalkRunCount.FK_bid == dev.id).\
         filter(func.date(WalkRunCount.datetime)==func.date(datetime.datetime.now(timezone('Asia/Seoul')))).first()
    # print("sensorDev")  
    db.session.flush()
    # print("get db", datetime.datetime.now() - startTime)
    # startTime = datetime.datetime.now()
    try :
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
      if sensorDev is not None :
        if sensorDev.walk_steps>bandData['walk_steps']  :
          tempwalk = bandData['walk_steps'] - sensorDev.temp_walk_steps

          if tempwalk>0:
            mqtt_data['bandData']['walk_steps'] = sensorDev.walk_steps + tempwalk
          
          elif tempwalk<0:
            mqtt_data['bandData']['walk_steps'] = sensorDev.walk_steps + bandData['walk_steps']

          else : 
            mqtt_data['bandData']['walk_steps'] = sensorDev.walk_steps

        elif sensorDev.walk_steps==bandData['walk_steps']:
            mqtt_data['bandData']['walk_steps'] = sensorDev.walk_steps
      # print("walk_steps") 
      data.walk_steps = mqtt_data['bandData']['walk_steps']
      data.temp_walk_steps = temp_walk_steps
      
      walkRunCount = WalkRunCount()
      walkRunCount.FK_bid = dev.id
      walkRunCount.walk_steps = mqtt_data['bandData']['walk_steps']
      walkRunCount.temp_walk_steps = temp_walk_steps

      temp_walk_steps = bandData['run_steps']
      if sensorDev is not None :
        if sensorDev.run_steps>bandData['run_steps']  :
          tempwalk = bandData['run_steps']-sensorDev.temp_run_steps
          if tempwalk>0:
            mqtt_data['bandData']['run_steps'] = sensorDev.run_steps + tempwalk
            
          elif tempwalk<0:
            mqtt_data['bandData']['run_steps'] = sensorDev.run_steps + bandData['run_steps']

          else : 
            mqtt_data['bandData']['run_steps'] = sensorDev.run_steps


        elif sensorDev.run_steps==bandData['run_steps']:
            mqtt_data['bandData']['run_steps'] = sensorDev.run_steps
      
      # print("run_steps") 
      data.run_steps = mqtt_data['bandData']['run_steps']
      data.temp_run_steps = temp_walk_steps

      walkRunCount.run_steps =  mqtt_data['bandData']['run_steps']
      walkRunCount.temp_run_steps = temp_walk_steps
      walkRunCount.datetime = datetime.datetime.now(timezone('Asia/Seoul'))
      sensorDev = db.session.query(WalkRunCount).\
        filter(WalkRunCount.FK_bid == dev.id).first()
      if sensorDev is not None :
        db.session.query(WalkRunCount).\
          filter(WalkRunCount.FK_bid == dev.id).\
            update(dict(walk_steps = walkRunCount.walk_steps,
              temp_walk_steps = walkRunCount.temp_walk_steps,
                run_steps = walkRunCount.run_steps, 
                  temp_run_steps = walkRunCount.temp_run_steps,
                  datetime=walkRunCount.datetime))
        db.session.commit()
        db.session.flush()
      else :
        db.session.add(walkRunCount)
        db.session.commit()
        db.session.flush()
      # print("work - db", datetime.datetime.now() - startTime)
      # startTime = datetime.datetime.now()
      data.x = bandData['x']
      data.y = bandData['y']
      data.z = bandData['z']
      data.t = bandData['t'] 
      if gatewayDev is not None:
        if mqtt_data['bandData']['h'] != 0:
          mqtt_data['bandData']['h'] = getAltitude(mqtt_data['bandData']['h'], gatewayDev.airpressure)
          data.h = mqtt_data['bandData']['h']
        else:
          data.h = mqtt_data['bandData']['h']
      else:
        data.h = mqtt_data['bandData']['h']
      # print("getAltitude") 
      data.rssi = mqtt_data['rssi']   
      data.datetime = datetime.datetime.now(timezone('Asia/Seoul'))
      db.session.add(data)
      db.session.commit()     
      db.session.flush()
      socketio.emit('efwbsync', mqtt_data, namespace='/receiver')
      # print("close handle_sync_data")
      # print("고도값 - DB - socket",datetime.datetime.now() - startTime)
    except Exception as e :
      print("****** error ********")
      print(e)

def handle_gateway_state(panid):
  print("handle_gateway_state", panid)
  try:
    dev = selectGatewayPid(panid['panid'])
    if dev is not None:
      if dev.connect_state == 0:
        updateGatewaysConnect(dev.id, True)
      else :
        updateGatewaysConnectCheck(dev.id)
    socketio.emit('gateway_connect', panid, namespace='/receiver')
  except:
    pass

@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    print("mqtt connect")

@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
  global mqtt_thread
  global gw_thread, work
  if message.topic == '/efwb/post/sync':
      with thread_lock:
          if mqtt_thread is None:
            mqtt_data = json.loads(message.payload.decode())
            extAddress = hex(int(str(mqtt_data['extAddress']['high'])+str(mqtt_data['extAddress']['low'])))
            mqtt_thread = socketio.start_background_task(handle_sync_data( mqtt_data,extAddress))
            mqtt_thread = None
  elif message.topic == '/efwb/post/connectcheck' :
      with thread_lock:
        if gw_thread is None:
          gw_thread = socketio.start_background_task(handle_gateway_state(json.loads(message.payload)))
          gw_thread = None
     
  elif message.topic == '/efwb/post/async' :
    event_data = json.loads(message.payload.decode())
    extAddress = hex(int(str(event_data['extAddress']['high'])+str(event_data['extAddress']['low'])))
    dev = db.session.query(Bands).filter_by(bid = extAddress).first()
    insertEvent(dev.id, event_data['type'], event_data['value'])
    event_socket = {
      "type" : event_data['type'],
      "value" : event_data['value'],
      "bid" : dev.bid
    }
    socket_emit('efwbasync', event_socket)
