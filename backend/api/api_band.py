# -*- coding: utf-8 -*-
print("module [backend.api_band] loaded")


import hashlib
from re import L
import requests
import time
import platform
import subprocess
from sqlalchemy.sql.elements import Null
from ping3 import ping
import threading
from threading import Lock
from backend import app, socketio, mqtt, login_manager
from flask import make_response, jsonify, request, json, send_from_directory
from flask_socketio import send, emit
from flask_restless import ProcessingException
from flask_restful import reqparse
from datetime import datetime
from Crypto.Cipher import AES
from functools import wraps
#client = mqtt.Client()
# from api.api_common import *
from backend.db.table_band import *
from sqlalchemy import func, case, or_, Interval
from sqlalchemy.sql.expression import text

from datetime import date
import os
from urllib.request import urlopen
from bs4 import BeautifulSoup


spo2BandData = {}
gatewayData = {}
start = False
gateway_thread = None
mqtt_thread = None
thread_lock = Lock()

mqtt.subscribe('/efwb/post/sync')
mqtt.subscribe('/efwb/post/connectcheck')
def bandLog(g):
  try:
    print("bandLog Start") 
    dev = db.session.query(Bands).\
            filter(Bands.connect_state == 1).\
            filter(Bands.id == GatewaysBands.FK_bid).\
            filter(GatewaysBands.FK_pid == g.id).all()
    if dev :
      for b in dev:
        Bands.query.filter_by(id = b.id).update(dict(
          disconnect_time=datetime.datetime.now(timezone('Asia/Seoul'))
          , connect_state = 0))
        bandlog = BandLog()
        bandlog.FK_bid = b.id
        bandlog.type = 0
        db.session.add(bandlog)
        db.session.commit()
        db.session.flush()
        db.session.close()
        # socketio.emit()
  except:
    pass

def gatewayLog(g, check):
  print("gatewayLog Start")
  gatewayLog = GatewayLog()
  gatewayLog.FK_pid = g.id

  if check:
    gatewayLog.type = 1
    db.session.add(gatewayLog)          
    Gateways.query.filter_by(id=g.id).update(dict(connect_state=1, connect_time = datetime.datetime.now(timezone('Asia/Seoul'))))
    db.session.commit()
    db.session.flush()
    db.session.close()
  else :
    gatewayLog.type = 0
    db.session.add(gatewayLog)
    Gateways.query.filter_by(id=g.id).update(dict(connect_state=0, disconnect_time =  datetime.datetime.now(timezone('Asia/Seoul'))))    
    db.session.commit()
    db.session.flush()
    db.session.close()
    bandLog(g)

  

# def gatewayCheck():
#   while True:
#     socketio.sleep(180)
#     print("gatewayCheck start")
#     try:
#       gateways = Gateways.query.all()
#       for g in gateways:
#         if pingTest(g.ip) :
#           print(g.id, "ping Test pass")
#           if serverTest(g.ip) is not None :
#             print(g.id, "server Test pass")
#             if g.connect_state == 0:
#               gatewayLog(g, True)
#           else :
#             print(g.id, "server Test no pass")
#             if g.connect_state == 1:
#               gatewayLog(g, False)
#             else :
#               dev = GatewayLog.query.filter_by(FK_pid=g.id).first()
#               if dev is None:
#                 gatewayLog(g, False)
#         else :
#           print(g.id, "ping Test no pass")
#           if g.connect_state == 1:
#             gatewayLog(g, False)
#           else :
#             dev = GatewayLog.query.filter_by(FK_pid=g.id).first()

#             if dev is None:
#               gatewayLog(g, False)
#       print("Close Gateway Check ")

#     except Exception as e:
#       print(e)

#   # threading.Timer(300, gatewayCheck).start()

def gatewayCheck():
  print("gatewayCheck start")
  try:
    gateways = db.session.query(Gateways).all()
    db.session.flush()
    db.session.close()
    for g in gateways:
      time1 = g.connect_check_time
      time2 = datetime.datetime.now()
      if (time2-time1).seconds > 180:
        if g.connect_state == 1:
            gatewayLog(g, False)
        else:
          dev = GatewayLog.query.filter_by(FK_pid=g.id).first()
          db.session.flush()
          db.session.close()
          if dev is None:
            gatewayLog(g, False)
        
    print("Close Gateway Check ")

  except Exception as e:
    print(e)
  threading.Timer(180, gatewayCheck).start()

# def gatewayCheckThread():
#   global gateway_thread
#   with thread_lock:
#     if gateway_thread is None:
#       gateway_thread = socketio.start_background_task(gatewayCheck)


def pingTest(hostName):
  resp = ping(hostName)

  if resp == False:
    return False
  else:
    return True


def serverTest(hostName):
  try:
    url = "http://"+hostName+":1310/servertest"

    payload={}
    headers = {}

    response = requests.request("GET", url, headers=headers, data=payload)
    result=response.text
    return result
  except Exception as e:
    print(e) 
    return None

@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    print("mqtt connect")


def event_db_save(id, type, value) :
  db_event = Events()
  db_event.FK_bid = id
  db_event.type = type
  db_event.value = value
  db_event.datetime = datetime.datetime.now()
  db.session.add(db_event)
  db.session.commit()
  db.session.flush()  

def get_event(id, type):
  eventDev = db.session.query(Events).filter_by(FK_bid=id).filter_by(type=type).order_by(Events.id.desc()).first()

  if eventDev is None:
    if type == 3 :
      sensorDev = db.session.query(func.count(SensorData.id).label('count')).\
      filter(SensorData.FK_bid==id).\
      filter(SensorData.datetime>func.date_add(func.now(), text('interval -30 second'))).\
        filter(or_(SensorData.scdState== 0, SensorData.scdState==1)).first()
      if sensorDev is not None and sensorDev.count > 10:
        return True
    else :
      return True
  else:
    time1 = eventDev.datetime
    time2 = datetime.datetime.now()
    if (time2-time1).seconds > 30 :
      if type == 3 :
        sensorDev = db.session.query(func.count(SensorData.id).label('count')).\
        filter(SensorData.FK_bid==id).\
        filter(SensorData.datetime>func.date_add(func.now(), text('interval -30 second'))).\
          filter(or_(SensorData.scdState== 0, SensorData.scdState==1)).first()
        if sensorDev is not None and sensorDev.count > 10:
          return True
      else:
        return True
  return False
def event_socket_emit(dev, type, value):

  event = get_event(dev.id, type)
  if event:
    
    event_db_save(dev.id, type, value)
    event_socket = {
    "type" : type,
    "value" : value,
    "bid" : dev.bid
    }
  
    socketio.emit('efwbasync', event_socket, namespace='/receiver')

def eventHandler(mqtt_data, dev):
  if mqtt_data['bandData']['fall_detect'] == 1 :
    
    event_socket_emit(dev, 0, mqtt_data['bandData']['fall_detect'])

  if mqtt_data['rssi'] < -80 :
    
    event_socket_emit(dev, 1, mqtt_data['rssi'])

  if mqtt_data['bandData']['battery_level'] < 10 :
    
    event_socket_emit(dev, 2, mqtt_data['bandData']['battery_level'] )

  if mqtt_data['bandData']['scdState'] == 0 or mqtt_data['bandData']['scdState'] == 1:
   
    event_socket_emit(dev, 3, mqtt_data['bandData']['scdState'])
  if mqtt_data['active'] == 'false':
    event_db_save(dev.id, 4, 0)
    event_scoket = {
      "type" : 4,
      "value" : mqtt_data['active'],
      "bid" : dev.bid
    }
    socketio.emit('efwbasync', event_scoket, namespace='/receiver')
def getAirpressure():
  print("getAltitud start")
  dev = db.session.query(Gateways).all()
  for g in dev:
  
    d = datetime.datetime.now(timezone('Asia/Seoul'))
    urldate = str(d.year)+"."+str(d.month)+"."+str(d.day)+"."+str(d.hour)
    try:
      html = urlopen("https://web.kma.go.kr/weather/observation/currentweather.jsp?auto_man=m&stn=0&type=t99&reg=100&tm="+urldate+"%3A00&x=25&y=1")  

      bsObject = BeautifulSoup(html, "html.parser") 
      temp = bsObject.find("table", {"class": "table_develop3"})
      trtemp = temp.find_all('tr')
      atemp = temp.find_all('a')

      for a in range(len(atemp)):
          if atemp[a].text == g.location:
              break
      tdtemp = trtemp[a+2].find_all('td')
      
      db.session.query(Gateways).filter_by(id = g.id).update((dict(airpressure=float(tdtemp[len(tdtemp)-1].text))))
      db.session.commit()
    except:
      pass
  threading.Timer(3600, getAirpressure).start()
def getAltitude(pressure, airpressure): # 기압 - 높이 계산 Dtriple

  p = (pressure / (airpressure * 100)); # ***분모 자리에 해면기압 정보 넣을 것!! (ex. 1018) // Dtriple
  b = 1 / 5.255
  alt = 44330 * (1 - p**b)
 
  return round(alt,2)

def handle_sync_data(mqtt_data, extAddress):
  global spo2BandData
  dev = db.session.query(Bands).filter_by(bid = extAddress).first()
  
  if dev is not None:
    print("handle start")
    gatewayDev = db.session.query(Gateways.airpressure).\
      filter(Gateways.id == GatewaysBands.FK_pid).\
        filter(GatewaysBands.FK_bid == dev.id).first()
    sensorDev = db.session.query(SensorData).\
      filter(SensorData.FK_bid == dev.id).\
      filter(func.date(SensorData.datetime)==func.date(datetime.datetime.now(timezone('Asia/Seoul')))).\
        order_by(SensorData.walk_steps.desc()).first()
    
    try :
      mqtt_data['extAddress']['high'] = extAddress
      if mqtt_data['extAddress']['low'] not in spo2BandData :
        spo2BandData[mqtt_data['extAddress']['low']] = 0
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

      if bandData['spo2'] == 0 :
          data.spo2 = 0
          mqtt_data['bandData']['spo2'] = 0
          spo2BandData[mqtt_data['extAddress']['low']] = 0
      elif bandData['spo2']<=1000 and bandData['spo2']>=400:
        data.spo2 = bandData['spo2']
        spo2BandData[mqtt_data['extAddress']['low']] = bandData['spo2']
      else :
        if spo2BandData[mqtt_data['extAddress']['low']]<=1000 and spo2BandData[mqtt_data['extAddress']['low']]>=400:
          data.spo2 = spo2BandData[mqtt_data['extAddress']['low']]
          mqtt_data['bandData']['spo2'] = spo2BandData[mqtt_data['extAddress']['low']]
        else :
          data.spo2 = 0
          mqtt_data['bandData']['spo2'] = 0
          spo2BandData[mqtt_data['extAddress']['low']] = 0
              
      data.motionFlag = bandData['motionFlag'] 
      data.scdState = bandData['scdState']
      data.activity = bandData['activity']
      # print("\n=============================================")
      # print(bandData['walk_steps'],bandData['run_steps'] )
      # print(sensorDev)
      # print("=============================================\n")
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

      data.walk_steps = mqtt_data['bandData']['walk_steps']
      data.temp_walk_steps = temp_walk_steps
      # if sensorDev is not None:
      #   print(" sensorDev.walk_steps(db에 저장한값) = ",sensorDev.walk_steps," data.walk_steps(db에 저장할값) = ",sensorDev.walk_steps," bandData['walk_steps'](temp값) = ", bandData['walk_steps'], " mqtt_data['bandData']['walk_steps'](증가하는 화면에 보여주는 값) = ",mqtt_data['bandData']['walk_steps'])   
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

      data.run_steps = mqtt_data['bandData']['run_steps']
      data.temp_run_steps = temp_walk_steps

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
      data.rssi = mqtt_data['rssi']   
      data.datetime = datetime.datetime.now(timezone('Asia/Seoul'))
      db.session.add(data)
      db.session.commit()
      db.session.flush()

      if mqtt_data['active'] == 'true':
        if dev.connect_state == 0 :
          Bands.query.filter_by(id = dev.id).update(dict(
            connect_time=datetime.datetime.now(timezone('Asia/Seoul'))
          , connect_state = 1))
          bandlog = BandLog()
          bandlog.FK_bid = dev.id
          bandlog.type = 1
          db.session.add(bandlog)
          db.session.commit()
          db.session.flush()
         
      else :
        Bands.query.filter_by(id = dev.id).update(dict(
          disconnect_time=datetime.datetime.now(timezone('Asia/Seoul'))
        , connect_state = 0))
        bandlog = BandLog()
        bandlog.FK_bid = dev.id
        bandlog.type = 0
        db.session.add(bandlog)
        db.session.commit()
        db.session.flush()
        
      
      eventHandler(mqtt_data, dev)
      socketio.emit('efwbsync', mqtt_data, namespace='/receiver')
      print("close handle")
    except Exception as e :
      print("****** error ********")
      print(e)


def handle_gateway_state(panid):
  try:
    dev = db.session.query(Gateways).filter_by(pid=panid['panid']).first()
    if dev is not None:
      if dev.connect_state == 0:
        gatewayLog(dev, True)
        db.session.query(Gateways).\
          filter_by(id=dev.id).\
            update(dict(connect_state=1, connect_time = datetime.datetime.now(timezone('Asia/Seoul')), 
            connect_check_time=datetime.datetime.now(timezone('Asia/Seoul'))))
        db.session.commit()
        db.session.flush()
      else :
        db.session.query(Gateways).filter_by(id=dev.id).update(dict(connect_check_time=datetime.datetime.now(timezone('Asia/Seoul'))))
        db.session.commit()
        db.session.flush()
    socketio.emit('bandnum', panid, namespace='/receiver')
  except:
    pass

def handle_gateway_bandnum(panid):
  try:
    dev = db.session.query(Gateways).filter_by(pid=panid['panid']).first()
    if dev is not None:
      if dev.connect_state == 0:
        gatewayLog(dev, True)
        db.session.query(Gateways).\
          filter_by(id=dev.id).\
            update(dict(connect_state=1, connect_time = datetime.datetime.now(timezone('Asia/Seoul')), 
            connect_check_time=datetime.datetime.now(timezone('Asia/Seoul'))))
        db.session.commit()
        db.session.flush()
      else :
        db.session.query(Gateways).filter_by(id=dev.id).update(dict(connect_check_time=datetime.datetime.now(timezone('Asia/Seoul'))))
        db.session.commit()
        db.session.flush()
    socketio.emit('bandnum', panid, namespace='/receiver')
  except:
    pass

@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
  global mqtt_thread
  if message.topic == '/efwb/post/sync':

    mqtt_data = json.loads(message.payload.decode())

    extAddress = hex(int(str(mqtt_data['extAddress']['high'])+str(mqtt_data['extAddress']['low'])))
    mqtt_thread = socketio.start_background_task(handle_sync_data(mqtt_data, extAddress))

  elif message.topic == '/efwb/post/connectcheck' :
    handle_gateway_state(json.loads(message.payload))
    
  elif message.topic == '/efwb/bandnum' :
    handle_gateway_bandnum(json.loads(message.payload))


@socketio.on('connect', namespace='/receiver')
def connect():
  print("***socket connect***")
  emit('message', "socket connected")


@socketio.on('disconnect', namespace='/receiver')
def disconnect():
    print("***socket disconnect***")

@socketio.on('message', namespace='/receiver')
def handle_message(data):
    print('received message: ' + data)

@login_manager.user_loader
def load_user(id):
    user = DBManager.db.session.query(Users).get(id)
    return user
@app.route('/api/efwb/v1/login', methods=['POST'])
def login_api():
    print("login api")
    data = json.loads(request.data)
    result = ''

    if data['username'] is not None and data['password'] is not None:
        loginuser = db.session.query(Users).filter(Users.username == data["username"]).first()

        if loginuser is None:
            result = {'status': False, 'reason': 1}  # ID 없음
        else:
            if loginuser.password != password_encoder_512(data["password"]):
                result = {'status': False, 'reason': 2} # PW 틀림

            else:  # Login 성공
                loginuser.last_login_time = datetime.datetime.now()
                loginuser.token = generate_token(data['username'])
                db.session.query(Users).filter(Users.username == data["username"])\
                    .update(dict(last_login_time=loginuser.last_login_time, token=loginuser.token))

                new_access_history = AccessHistory()
                new_access_history.type = 0  # Login
                user_agent = request.environ.get('HTTP_USER_AGENT')
                new_access_history.os_ver, new_access_history.browser_ver = get_os_browser_from_useragent(user_agent)
                new_access_history.ip_addr = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
                new_access_history.token = loginuser.token
                new_access_history.user_id = loginuser.username
                new_access_history.FK_user_id = loginuser.id
                db.session.add(new_access_history)
              
                db.session.commit()
                db.session.flush()
                result = {'status': True, 'reason': 0, 'user': loginuser.serialize()}

    return make_response(jsonify(result), 200)

@app.route("/api/efwb/v1/logout", methods=["POST"])
def logout_api():
    print("logout api")
    parser = reqparse.RequestParser()
    parser.add_argument("token", type=str, location="headers")
    token = parser.parse_args()["token"]
    if token is None:
        print("token is none")
    else :
      loginuser = AccessHistory.query.filter_by(token=token).first()
    
      if loginuser is None:
          print("user is none")
      else :

        AccessHistory.query.filter_by(token=token).update(dict(token=None))
        new_access_history = AccessHistory()
        new_access_history.type = 1  # Logout
        user_agent = request.environ.get('HTTP_USER_AGENT')
        new_access_history.os_ver, new_access_history.browser_ver = get_os_browser_from_useragent(user_agent)
        new_access_history.ip_addr = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
        new_access_history.user_id = loginuser.user_id
        new_access_history.FK_user_id = loginuser.FK_user_id
        db.session.add(new_access_history)
                    
        db.session.commit()
        db.session.flush()
    
    
    return make_response({}, 200)

def generate_token(userID):
    m = hashlib.sha1()

    m.update(userID.encode('utf-8'))
    m.update(datetime.datetime.now().isoformat().encode('utf-8'))

    return m.hexdigest()

def check_token(search_params=None, **kw):
    parser = reqparse.RequestParser()
    parser.add_argument("token", type=str, location="headers")
    token = parser.parse_args()["token"]

    if token is None:
        raise ProcessingException(description="Not Authorized", code=410)

    accessHistory = AccessHistory.query.filter_by(token=token).first()
    if accessHistory is None:
        raise ProcessingException(description="Not Authorized", code=411)

    return accessHistory

def token_required(fn):
    @wraps(fn)
    def decorated(*args, **kwargs):
        parser = reqparse.RequestParser()
        parser.add_argument("token", type=str, location="headers")
        token = parser.parse_args()["token"]
        if token is None:
            raise ProcessingException(description="Not authorized", code=401)
        return fn(*args, **kwargs)
    return decorated

@app.route('/api/efwb/v1/gateway/bandnum', methods=["GET"]) 
def  gateway_bandnum_get_api():
  mqtt.publish('efwb/get/connectcheck', 'bandnum')
  return make_response(jsonify('ok'), 200)
@app.route('/api/efwb/v1/groups/add', methods=['POST'])
@token_required
def group_post_api():
    data = json.loads(request.data)

    params = ['gid','groupname', 'permission']

    for param in params:
        if param not in data:
            return make_response(jsonify('Parameters are not enough.'), 400)

    group = Groups()
    group.gid = data['gid']
    group.groupname = data['groupname']
    group.permission = data['permission']


    db.session.add(group)
    db.session.commit()
    db.session.flush()
    result = {
      "result": "OK"
    }

    return make_response(jsonify(result), 200)

@app.route('/api/efwb/v1/groups/list', methods=['GET'])
@token_required
def group_list_get_api():
  groups = Groups.query.all()
  group_list = []
  for gr in groups:
    group_list.append(gr.serialize())
  result = {
    "result": "OK",
    "groups": group_list
  }

  return make_response(jsonify(result), 200)
@app.route('/api/efwb/v1/groups/detail', methods=['POST'])
@token_required
def group_get_api():
  data = json.loads(request.data)
  params = ['gid']
  for param in params:
        if param not in data:
            return make_response(jsonify('Parameters are not enough.'), 400)
  dev = Groups.query.filter(Groups.id == data['gid']).first()
  if dev is None:
    return make_response(jsonify('Group is not found.'), 404)
  result = {
    "result": "OK",
    "groups": dev.serialize()
  }
  return make_response(jsonify(result), 200)

@app.route('/api/efwb/v1/groups/update', methods=['PATCH'])
@token_required
def group_update_api():
    data = json.loads(request.data)

    params = ['checkid','gid','groupname', 'permission']

    for param in params:
        if param not in data:
            return make_response(jsonify('Parameters are not enough.'), 400)
    
    dev = Groups.query.filter(Groups.gid == data['checkid']).first()
    
    if dev is None:
      return make_response(jsonify('User is not found.'), 404)

    Groups.query.filter(Groups.gid == data['checkid']).update(
      {'gid': data['gid'], 'groupname': data['groupname'], 
      'permission': data['permission']}
    )
    
    db.session.commit() 
    db.session.flush()   
    result = {
      "result": "OK",
    }

    return make_response(jsonify(result), 200)  

@app.route('/api/efwb/v1/groups/delete', methods=['DELETE'])
@token_required
def group_delete_api():
    data = json.loads(request.data)

    params = ['gid']

    for param in params:
        if param not in data:
            return make_response(jsonify('Parameters are not enough.'), 400)
    
    group = Groups.query.filter(Groups.gid == data['gid']).first()
    if group is None:
      return make_response(jsonify('group is not found.'), 404)

    try:
      db.session.delete(group)
      db.session.commit()  
      db.session.flush()
    except Exception as e:
      result = {
        "result": str(e),
      }
      return make_response(jsonify(result), 400) 

    result = {
      "result": "OK",
    }
    return make_response(jsonify(result), 200)     


@app.route('/api/efwb/v1/users/add', methods=['POST'])
@token_required
def user_post_api():
    data = json.loads(request.data)

    params = ['uid','username', 'name', 'password']

    for param in params:
        if param not in data:
            return make_response(jsonify('Parameters are not enough.'), 400)

    user = Users()
    user.uid = data['uid']
    user.username = data['username']
    user.password = DBManager.password_encoder_512(data['password'])
    user.name = data['name']
    db.session.add(user)
    db.session.commit()
    db.session.flush()
    result = {
      "result": "OK"
    }

    return make_response(jsonify(result), 200)
@app.route('/api/efwb/v1/users/list', methods=['GET'])
@token_required
def user_list_get_api():
  users = Users.query.all()
  user_list = []
  for ur in users:
    user_list.append(ur.serialize())
  result = {
    "result": "OK",
    "users": user_list
  }

  return make_response(jsonify(result), 200)

@app.route('/api/efwb/v1/users/detail', methods=['POST'])
@token_required
def user_detail_get_api():

    data = json.loads(request.data)

    params = ['uid']
    for param in params:
          if param not in data:
              return make_response(jsonify('Parameters are not enough.'), 400)
    dev = Users.query.filter(Users.id == data['uid']).first()
    if dev is None:
      return make_response(jsonify('User is not found.'), 404)
    result = {
      "result": "OK",
      "users": dev.serialize()
    }

    return make_response(jsonify(result), 200)

@app.route('/api/efwb/v1/users/update', methods=['PATCH'])
@token_required
def user_update_api():
    data = json.loads(request.data)

    params = ['checkid','uid','username', 'name', 'password']

    for param in params:
        if param not in data:
            return make_response(jsonify('Parameters are not enough.'), 400)
    dev = Users.query.filter(Users.uid == data['checkid']).first()
    if dev is None:
      return make_response(jsonify('User is not found.'), 404)

    Users.query.filter(Users.uid == data['checkid']).update(
      {'uid': data['uid'], 'username': data['username'], 'password': DBManager.password_encoder_512(data['password']),
      'name': data['name']}
    )
    db.session.commit()  
    db.session.flush()  
    result = {
      "result": "OK",
    }

    return make_response(jsonify(result), 200)  
@app.route('/api/efwb/v1/users/delete', methods=['DELETE'])
@token_required
def user_delete_api():
    data = json.loads(request.data)

    params = ['uid']

    for param in params:
        if param not in data:
            return make_response(jsonify('Parameters are not enough.'), 400)
    
    user = Users.query.filter(Users.uid == data['uid']).first()
    if user is None:
      return make_response(jsonify('User is not found.'), 404)

    db.session.delete(user)
    db.session.commit()    
    db.session.flush()
    result = {
      "result": "OK",
    }

    return make_response(jsonify(result), 200) 
@app.route('/api/efwb/v1/users/<username>', methods=['GET'])
@token_required
def username_check_api(username):
  dev = Users.query.filter(Users.username==username).first()

  if dev is None:
    return make_response(jsonify('User is not Found.'), 404)
  result = {
    "result":"OK",
    "data":dev.serialize()
  }
  return make_response(jsonify(result), 200)
@app.route('/api/efwb/v1/users/groupinfo/<id>', methods=['GET'])
@token_required
def user_groupinfo_api(id):
  dev = db.session.query(Groups).filter(UsersGroups.FK_gid == Groups.id).filter(UsersGroups.FK_uid==id).all()
  grouplist = []
  if dev is None:
    return make_response(jsonify('User is not Found.'), 404)

  for g in dev :
    grouplist.append(g.serialize())

  result = {
    "result":"OK",
    "data":grouplist
  }
  return make_response(jsonify(result), 200)  


def users_group_api(id):
  dev = db.session.query(UsersGroups.FK_gid).filter_by(FK_uid = id).first()
  if dev is None :
    return None
  return dev

@app.route('/api/efwb/v1/users/samegroup/<id>', methods=['GET'])
def users_samegroup_get_api(id):
  gid = users_group_api(id)
  if gid is None :
    return make_response(jsonify('User is not Found.'), 404)
  
  dev = db.session.query(Users).\
    filter(Users.id == UsersGroups.FK_uid).\
      filter(UsersGroups.FK_gid==gid.FK_gid).all()
  
  if dev is None:
    return make_response(jsonify('User is not Found.'), 404)
  userlist = []
  for u in dev :
    userlist.append(u.serialize())

  result = {
    "result":"OK",
    "data":{
      "userlist": userlist,
      "gid" : gid
    }
  }
  return make_response(jsonify(result), 200)  


@app.route('/api/efwb/v1/users/gatewayinfo/<id>', methods=['GET'])
@token_required
def user_gatewayinfo_api(id):
  dev = db.session.query(Gateways).filter(UsersGateways.FK_pid == Gateways.id).filter(UsersGateways.FK_uid==id).all()
  gatewaylist = []
  if dev is None:
    return make_response(jsonify('User is not Found.'), 404)
  
  for b in dev :
    gatewaylist.append(b.serialize())
 
  result = {
    "result":"OK",
    "data":gatewaylist
  }
  return make_response(jsonify(result), 200)  

@app.route('/api/efwb/v1/gateways/bandinfo/<id>', methods=['GET'])
@token_required
def gateway_bandinfo_api(id):
  dev = db.session.query(Bands).\
    filter(GatewaysBands.FK_bid == Bands.id).\
      filter(GatewaysBands.FK_pid==id).all()
  bandlist = []
  if dev is None:
    return make_response(jsonify('User is not Found.'), 404)

  for b in dev :
    bandlist.append(b.serialize())
 
  result = {
    "result":"OK",
    "data":bandlist
  }
  return make_response(jsonify(result), 200)

@app.route('/api/efwb/v1/gatewaysbands/num/<id>', methods=['GET'])
def gatewaysbands_num_get_api(id):
  dev = db.session.query(GatewaysBands).\
    filter(GatewaysBands.FK_pid == id).first()
  dev = db.session.query(func.count(GatewaysBands.id).label('num')).\
    filter(GatewaysBands.FK_pid == id).first()

  if dev is None:
    return make_response(jsonify('User is not Found.'), 404)

  result = {
    "result":"OK",
    "data":int(dev.num)
  }
  return make_response(jsonify(result), 200)

@app.route('/api/efwb/v1/users/bandinfo/<id>', methods=['GET'])
@token_required
def users_bandinfo_api(id):
  dev = db.session.query(Bands).\
    filter(Bands.id == UsersBands.FK_bid).\
      filter(UsersBands.FK_uid == id).all()
  bandlist = []
  if dev is None:
    return make_response(jsonify('User is not Found.'), 404)
  for b in dev :
    bandlist.append(b.serialize())
  result = {
    "result":"OK",
    "data":bandlist
  }
  return make_response(jsonify(result), 200)  

@app.route('/api/efwb/v1/bands/add', methods=['POST'])
@token_required
def band_post_api():
    data = json.loads(request.data)

    params = ['bid','alias', 'name', 'gender', 'birth']

    for param in params:
        if param not in data:
            return make_response(jsonify('Parameters are not enough.'), 400)

    bands = Bands()
    bands.bid = data['bid']
    bands.alias = data['alias']
    bands.name = data['name']
    bands.gender = data['gender']
    bands.birth = data['birth']

    db.session.add(bands)
    db.session.commit()
    db.session.flush()
    result = {
      "result": "OK"
    }

    return make_response(jsonify(result), 200)
@app.route('/api/efwb/v1/bands/list', methods=['GET'])
@token_required
def band_list_get_api():
  bands = Bands.query.all()
  band_list = []
  for bn in bands:
    band_list.append(bn.serialize())
  result = {
    "result": "OK",
    "data": band_list
  }

  return make_response(jsonify(result), 200)

@app.route('/api/efwb/v1/bands/detail', methods=['POST'])
@token_required
def band_detail_get_api():
    data = json.loads(request.data)

    params = ['id']
    for param in params:
          if param not in data:
              return make_response(jsonify('Parameters are not enough.'), 400)
    dev = Bands.query.filter(Bands.id == data['id']).first()
    if dev is None:
      return make_response(jsonify('User is not found.'), 404)
    result = {
      "result": "OK",
      "data": dev.serialize()
    }

    return make_response(jsonify(result), 200)

@app.route('/api/efwb/v1/bands/update', methods=['PATCH'])
@token_required
def band_update_api():
    data = json.loads(request.data)

    params = ['id','bid','alias', 'name', 'gender', 'birth', 'disconnect_time', 'connect_time']

    for param in params:
        if param not in data:
            return make_response(jsonify('Parameters are not enough.'), 400)
    band = Bands.query.filter(Bands.bid == data['id']).first()
    if band is None:
      return make_response(jsonify('User is not found.'), 404)

    Bands.query.filter(Bands.id == data['id']).update(
      {
            "bid": data['bid'],
            "alias": data['alias'],
            "name": data['name'],
            "gender": data['gender'],
            "birth": data['birth'],
            "disconnect_time": data['disconnect_time'],
            "connect_time":data['connect_time']

        }
    )
    db.session.commit()    
    db.session.flush()
    result = {
      "result": "OK",
    }

    return make_response(jsonify(result), 200)  

@app.route('/api/efwb/v1/bands/delete', methods=['DELETE'])
@token_required
def band_delete_api():
    data = json.loads(request.data)

    params = ['bid']

    for param in params:
        if param not in data:
            return make_response(jsonify('Parameters are not enough.'), 400)
    
    band = Bands.query.filter(Bands.bid == data['bid']).first()
    if band is None:
      return make_response(jsonify('User is not found.'), 404)

    db.session.delete(band)
    db.session.commit()    
    db.session.flush()
    result = {
      "result": "OK",
    }

    return make_response(jsonify(result), 200)  
@app.route('/api/efwb/v1/bands/gatewayinfo/<id>', methods=['GET'])
@token_required
def band_gatewayinfo_api(id):
  dev = db.session.query(Gateways).\
    filter(Gateways.id == GatewaysBands.FK_pid).\
    filter(GatewaysBands.FK_bid==id).all()
  gatewaylist = []
  if dev is None:
    return make_response(jsonify('User is not Found.'), 404)
  for u in dev :
    gatewaylist.append(u.serialize())
  result = {
    "result":"OK",
    "data":gatewaylist
  }
  return make_response(jsonify(result), 200)
@app.route('/api/efwb/v1/bands/userinfo/<id>', methods=['GET'])
@token_required
def band_userinfo_api(id):
  dev = db.session.query(Users).\
    filter(Users.id == UsersGateways.FK_uid).\
      filter(UsersGateways.FK_pid==GatewaysBands.FK_pid).\
      filter(GatewaysBands.FK_bid==id).all()
  userlist = []
  if dev is None:
    return make_response(jsonify('User is not Found.'), 404)
  for u in dev :
    userlist.append(u.serialize())
  result = {
    "result":"OK",
    "data":userlist
  }
  return make_response(jsonify(result), 200)     

@app.route('/api/efwb/v1/usersgroups/add', methods=['POST'])
@token_required
def users_groups_post_api():
    data = json.loads(request.data)

    params = ['uids','gids']
    
    for param in params:
        if param not in data:
            return make_response(jsonify('Parameters are not enough.'), 400)

    if len(data['uids'])>len(data['gids']):
      users_groups = addDBList(UsersGroups(), data['gids'], data['uids'], True, True)

    elif len(data['uids'])<len(data['gids']):
     
      users_groups = addDBList(UsersGroups(), data['uids'], data['gids'], False, True)
        
    else:
      users_groups = addDBList(UsersGroups(), data['gids'], data['uids'], True, True)
    db.session.add(users_groups)
    db.session.commit()
    db.session.flush()
    result = {
      "result": "OK"
    }

    return make_response(jsonify(result), 200)

@app.route('/api/efwb/v1/usersgroups/detail', methods=['POST'])
@token_required
def users_groups_detail_get_api():
    data = json.loads(request.data)
    users_groups_list = []
    params = ['gid', 'uid']
    
    if params[0] in data :
      dev = UsersGroups.query.filter(UsersGroups.FK_gid == data['gid']).all()
      if dev is None:
        return make_response(jsonify('UsersGroups is not found.'), 404)
      for ug in dev :
        users_groups_list.append(ug.serialize())

    elif params[1] in data :
      dev = UsersGroups.query.filter(UsersGroups.FK_uid == data['uid']).all()
      if dev is None:
        return make_response(jsonify('UsersGroups is not found.'), 404)
      for ug in dev :
        users_groups_list.append(ug.serialize())

    else :
      return make_response(jsonify('Parameters are not enough.'), 400)
    
    result = {
      "result": "OK",
      "users_groups": users_groups_list
    }

    return make_response(jsonify(result), 200)

@app.route('/api/efwb/v1/usersgroups/list', methods=['GET'])
@token_required
def users_groups_list_get_api():
  users_groups = UsersGroups.query.all()
  users_groups_list = []
  for ug in users_groups:
    users_groups_list.append(ug.serialize())
  result = {
    "result": "OK",
    "users": users_groups_list
  }

  return make_response(jsonify(result), 200)

# @app.route('/api/efwb/v1/users_groups/update', methods=['PATCH'])
# def users_groups_update_api():
#     data = json.loads(request.data)

#     params = ['checkid','bid','alias', 'name', 'gender', 'birth']

#     for param in params:
#         if param not in data:
#             return make_response(jsonify('Parameters are not enough.'), 400)
#     band = Bands.query.filter(Bands.bid == data['checkid']).first()
#     if band is None:
#       return make_response(jsonify('User is not found.'), 404)

#     Bands.query.filter(Bands.bid == data['checkid']).update(
#       {
#             "bid": data['bid'],
#             "alias": data['alias'],
#             "name": data['name'],
#             "gender": data['gender'],
#             "birth": data['birth']
#         }
#     )
#     db.session.commit()    
#     result = {
#       "result": "OK",
#     }

#     return make_response(jsonify(result), 200)  

@app.route('/api/efwb/v1/usersgroups/delete', methods=['DELETE'])
@token_required
def users_groups_delete_api():
    data = json.loads(request.data)

    params = ['uids', 'gids']
    flag = False
    for param in params:
        if param not in data:
            return make_response(jsonify('Parameters are not enough.'), 400)
    for uid in data['uids']:
      for gid in data['gids']:
        band = UsersGroups.query.filter(UsersGroups.FK_uid == uid).filter(UsersGroups.FK_gid == gid)
        if band.all() :
          flag = True
          band.delete()

    if flag == False :
      return make_response(jsonify('UsersGroups is not found.'), 404)       
    db.session.commit()    
    db.session.flush()
    result = {
      "result": "OK",
    }
    
    return make_response(jsonify(result), 200)  

@app.route('/api/efwb/v1/users_bands/add', methods=['POST'])
@token_required
def users_bands_post_api():
    data = json.loads(request.data)

    params = ['uids','bids']

    for param in params:
        if param not in data:
            return make_response(jsonify('Parameters are not enough.'), 400)

    if len(data['uids'])>len(data['bids']):
      users_table = addDBList(UsersBands, data['bids'], data['uids'], True, False)

    elif len(data['uids'])<len(data['bids']):
      users_table = addDBList(UsersBands, data['uids'], data['bids'], False, False)
        
    else:
      users_table = addDBList(UsersBands, data['bids'], data['uids'], True, False)

    db.session.add(users_table)
    db.session.commit()
    db.session.flush()
    result = {
      "result": "OK"
    }
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      
    return make_response(jsonify(result), 200)

@app.route('/api/efwb/v1/usersgateways/detail', methods=['POST'])
@token_required
def users_bands_detail_get_api():
    data = json.loads(request.data)
    users_gateways_list = []
    params = ['pid', 'uid']
    
    if params[0] in data :
      dev = UsersGateways.query.filter(UsersGateways.FK_pid == data['pid']).all()
      if dev is None:
        return make_response(jsonify('UsersGateways is not found.'), 404)
      for ub in dev :
        users_gateways_list.append(ub.serialize())

    elif params[1] in data :
      dev = UsersGateways.query.filter(UsersGateways.FK_uid == data['uid']).all()
      if dev is None:
        return make_response(jsonify('UsersGateways is not found.'), 404)
      for ub in dev :
        users_gateways_list.append(ub.serialize())

    else :
      return make_response(jsonify('Parameters are not enough.'), 400)
    
    result = {
      "result": "OK",
      "users_gateways": users_gateways_list
    }

    return make_response(jsonify(result), 200)

@app.route('/api/efwb/v1/usersgateways/list', methods=['GET'])
@token_required
def users_bands_list_get_api():
  users_gateways = UsersGateways.query.all()
  users_gateways_list = []
  for ub in users_gateways:
    users_gateways_list.append(ub.serialize())
  result = {
    "result": "OK",
    "users": users_gateways_list
  }

  return make_response(jsonify(result), 200)

# @app.route('/api/efwb/v1/users_groups/update', methods=['PATCH'])
# def users_groups_update_api():
#     data = json.loads(request.data)

#     params = ['checkid','bid','alias', 'name', 'gender', 'birth']

#     for param in params:
#         if param not in data:
#             return make_response(jsonify('Parameters are not enough.'), 400)
#     band = Bands.query.filter(Bands.bid == data['checkid']).first()
#     if band is None:
#       return make_response(jsonify('User is not found.'), 404)

#     Bands.query.filter(Bands.bid == data['checkid']).update(
#       {
#             "bid": data['bid'],
#             "alias": data['alias'],
#             "name": data['name'],
#             "gender": data['gender'],
#             "birth": data['birth']
#         }
#     )
#     db.session.commit()    
#     result = {
#       "result": "OK",
#     }

#     return make_response(jsonify(result), 200)  

@app.route('/api/efwb/v1/usersgateways/delete', methods=['DELETE'])
@token_required
def users_bands_delete_api():
    data = json.loads(request.data)

    params = ['uids', 'pids']
    flag = False
    for param in params:
        if param not in data:
            return make_response(jsonify('Parameters are not enough.'), 400)
    for uid in data['uids']:
      for pid in data['pids']:
        usersgateways = UsersGateways.query.filter(UsersGateways.FK_uid == uid).filter(UsersGateways.FK_pid == pid)
        if usersgateways.all() :
          flag = True
          usersgateways.delete()

    if flag == False :
      return make_response(jsonify('UsersGateways is not found.'), 404)       
    db.session.commit()    
    db.session.flush()
    result = {
      "result": "OK",
    }
    
    return make_response(jsonify(result), 200)  

@app.route('/api/efwb/v1/sensordata/list', methods=['GET'])
@token_required
def sensordata_list_get_api():
  sensordata = SensorData.query.all()
  sensordata_list = []
  for sd in sensordata:
    sensordata_list.append(sd.serialize())

  result = {
    "result": "OK",
    "sensordata": sensordata_list
  }

  return make_response(jsonify(result), 200)

def getAttribute(str, sensor):
  if str == 'hr':
    return sensor.hr
  elif str == 'spo2':
    return sensor.spo2

@app.route('/api/efwb/v1/sensordata/vital', methods=['POST'])
def sensordata_day_get_api():
  data = json.loads(request.data)

  params = ['bid','dataname', 'days']
  
  for param in params:
    if param not in data:
      return make_response(jsonify('Parameters are not enough.'), 400)  
  json_data = []
  day = ['월', '화', '수', '목', '금', '토', '일']
  for i in data['days'] :
    # sensordata_list = [{"label": [], "data": [] } ] 
    sensordata_list = [] 
    valuedata = db.session.query(func.avg(getAttribute(data['dataname'], SensorData)).label('y'), func.date_format(SensorData.datetime, '%H').label('x')).filter(SensorData.FK_bid == data['bid']).filter(func.date(SensorData.datetime) == i).group_by(func.hour(SensorData.datetime)).all()
    #valuedata = db.session.query(getAttribute(data['dataname'], SensorData).label('y'), SensorData.datetime.label('x')).filter(SensorData.FK_bid == data['bid']).filter(func.date(SensorData.datetime) == i).all()
    if not valuedata :
      continue
    if data['dataname'] =='spo2' :
      for b in valuedata :
        if b.y>0:
          sensordata_list.append({"x": b.x,"y": float((b.y)/10)})
        else:
          sensordata_list.append({"x": b.x,"y": float(b.y)})
    else:
      for b in valuedata :
        sensordata_list.append({"x": b.x,"y": float(b.y)})

    dev = db.session.query(func.min(getAttribute(data['dataname'], SensorData)).label('min'), func.max(getAttribute(data['dataname'], SensorData)).label('max'), func.avg(getAttribute(data['dataname'], SensorData)).label('avg')).filter(SensorData.FK_bid == data['bid']).filter(func.date(SensorData.datetime) == i).all()
    for b in dev: 
      resultJSON = {
        "minmax":str(b.min)+" - "+str(b.max), 
        "normal": float(b.avg),
      }
    dayValue = date(int(i[0:4]), int(i[5:7]), int(i[8:10])).weekday()
    dateValue = i[5:7]+"월 "+i[8:10]+"일 "+day[dayValue]
    json_data.append({"date": dateValue, "total": resultJSON,  "data": sensordata_list})

  result = {
    "result": "OK",
    "data": json_data
  }

  return make_response(jsonify(result), 200)  

@app.route('/api/efwb/v1/sensordata/activity', methods=['POST'])
def activity_day_get_api():
  data = json.loads(request.data)

  params = ['bid', 'days']
  
  for param in params:
    if param not in data:
      return make_response(jsonify('Parameters are not enough.'), 400)  

  json_data = []
  day = ['월', '화', '수', '목', '금', '토', '일']
  for i in data['days'] :
    # sensordata_list = [{"label": [], "data": [] } ] 
    sensordata_list = [[],[]] 
    valuedata = db.session.query(func.date_format(SensorData.datetime,'%H').label('date'),
  (func.max(SensorData.walk_steps)-func.min(SensorData.walk_steps)).label('walk_steps'), 
  (func.max(SensorData.run_steps)-func.min(SensorData.run_steps)).label('run_steps')).\
      filter(SensorData.FK_bid == data['bid']).\
        filter(func.date(SensorData.datetime) == i).\
          group_by(func.hour(SensorData.datetime)).all()
    #valuedata = db.session.query(getAttribute(data['dataname'], SensorData).label('y'), SensorData.datetime.label('x')).filter(SensorData.FK_bid == data['bid']).filter(func.date(SensorData.datetime) == i).all()
    if not valuedata :
      continue
    
    for b in valuedata :
      sensordata_list[0].append({"x": b.date,"y": int(b.walk_steps)})
      sensordata_list[1].append({"x": b.date,"y": int(b.run_steps)})
    
    dayValue = date(int(i[0:4]), int(i[5:7]), int(i[8:10])).weekday()
    dateValue = i[5:7]+"월 "+i[8:10]+"일 "+day[dayValue]
    json_data.append({"date": dateValue,  "data": sensordata_list})

  result = {
    "result": "OK",
    "data": json_data
  }

  return make_response(jsonify(result), 200)  

def datetimeBetween(data):
  if len(data) == 1 :
    return data[0]
  else :
    return data[len(data)-1]
@app.route('/api/efwb/v1/sensordata/fall/sum', methods=['POST'])
def sensordata_fall_sum_post_api():
  data = json.loads(request.data)
  params = ['bid', 'days' ]
  for param in params:
    if param not in data:
      return make_response(jsonify('Parameters are not enough.'), 400)  
  json_data = []
  dev = db.session.query(func.date_format(SensorData.datetime, "%Y-%m-%d").label('day'), 
  func.sum(SensorData.fall_detect).label('fall_detect')).\
    filter(SensorData.FK_bid == data['bid']).\
      filter(func.date(SensorData.datetime).between(data['days'][0], datetimeBetween(data['days']))).\
      group_by(func.date(SensorData.datetime)).all()
  for i in dev:
    json_data.append({
      'day':i.day,
      'fall_detect':int(i.fall_detect)
    })
  result = {
    "result": "OK",
    "data": json_data
  }
  return make_response(jsonify(result), 200)
@app.route('/api/efwb/v1/sensordata/activity/oneday', methods=['POST'])
def sensordata_activity_oneday_post_api():
  data = json.loads(request.data)
  params = ['bid', 'days' ]
  for param in params:
    if param not in data:
      return make_response(jsonify('Parameters are not enough.'), 400)  
  json_data = []
  dev = db.session.query(func.date_format(SensorData.datetime, "%Y-%m-%d").label('day'), 
  func.max(SensorData.walk_steps).label('walk_steps'), 
  func.max(SensorData.run_steps).label('run_steps')).\
    filter(SensorData.FK_bid == data['bid']).\
      filter(func.date(SensorData.datetime).between(data['days'][0], datetimeBetween(data['days']))).\
      group_by(func.date(SensorData.datetime)).all()
  for i in dev:
    json_data.append({
      'day':i.day,
      'walk_steps':int(i.walk_steps),
      'run_steps':int(i.run_steps),
    })
  result = {
    "result": "OK",
    "data": json_data
  }
  return make_response(jsonify(result), 200)
@app.route('/api/efwb/v1/events', methods=["POST"])
def events_post_api():
  data = json.loads(request.data)
  params = ['bid', 'days']

  for param in params:
    if param not in data:
      return make_response(jsonify('Parameters are not enough.'), 400) 
  json_data = []
  dev = []

  if len(data['days']) == 0 :
    dev = db.session.query(Events).\
    filter(Events.FK_bid==data['bid']).\
      all()
  else :
    dev = db.session.query(Events).\
      filter(Events.FK_bid==data['bid']).\
        filter(func.date(Events.datetime).\
          between(data['days'][0], datetimeBetween(data['days']))).\
            all()
  for i in dev:
    json_data.append(i.serialize())
  result = {
    "result": "OK",
    "data": json_data
  }

  return make_response(jsonify(result), 200)

@app.route('/api/efwb/v1/events/fall_detect', methods=["POST"])
def events_fall_post_api():
  data = json.loads(request.data)
  params = ['bid', 'days']

  for param in params:
    if param not in data:
      return make_response(jsonify('Parameters are not enough.'), 400) 
  json_data = []
  dev = []

  if len(data['days']) == 0 :
    dev = db.session.query(func.date_format(Events.datetime,'%Y-%m-%d').label('date'),
  func.sum(Events.value).label('data')).\
      filter(Events.FK_bid==data['bid']).\
        filter(Events.type==0).\
          group_by(func.date(Events.datetime)).all()
  else :
    dev = db.session.query(func.date_format(Events.datetime,'%Y-%m-%d').label('date'),
  func.sum(Events.value).label('data')).\
      filter(Events.FK_bid==data['bid']).\
        filter(Events.type==0).\
        filter(func.date(Events.datetime).\
          between(data['days'][0], datetimeBetween(data['days']))).\
             group_by(func.date(Events.datetime)).all()
          
  for i in dev:
    json_data.append({"date": i.date, "data": int(i.data)})
  result = {
    "result": "OK",
    "data": json_data
  }

  return make_response(jsonify(result), 200) 

@app.route('/api/efwb/v1/sensordata/activity/day', methods=['POST'])

def sensordata_activity_day_get_api():
  data = json.loads(request.data)
  params = ['bid', 'days']

  for param in params:
    if param not in data:
      return make_response(jsonify('Parameters are not enough.'), 400)  

  json_data = [] 
  valuedata = db.session.query(func.concat(func.month(SensorData.datetime), '월 ', 
  func.dayofmonth(SensorData.datetime),'일 ', case([(func.dayofweek(SensorData.datetime) == 1, '일'),
  (func.dayofweek(SensorData.datetime) == 2, '월'),
  (func.dayofweek(SensorData.datetime) == 3, '화'),
  (func.dayofweek(SensorData.datetime) == 4, '수'),
  (func.dayofweek(SensorData.datetime) == 5, '목'),
  (func.dayofweek(SensorData.datetime) == 6, '금')],
  else_= '토')).label('day'),
  func.concat(func.year(SensorData.datetime),'-',
  func.month(SensorData.datetime), '-', 
  func.dayofmonth(SensorData.datetime)).label('d'), 
  func.sum(SensorData.walk_steps).label('walk_steps'), 
  func.sum(SensorData.run_steps).label('run_steps')).\
    filter(SensorData.FK_bid == data['bid']).\
    filter(func.date(SensorData.datetime).between(data['days'][0], datetimeBetween(data['days']))).\
      group_by(func.date(SensorData.datetime)).all()

  for i in valuedata: 
    json_data.append({
      "day": i.day, 
      "d": i.d,
    "walk_steps": float(i.walk_steps), 
    "run_steps": float(i.run_steps)})
  result = {
    "result": "OK",
    "data": json_data
  }
  return make_response(jsonify(result), 200)

@app.route('/api/efwb/v1/sensordata/activity/week', methods=['POST'])

def sensordata_activity_week_get_api():
  data = json.loads(request.data)

  params = ['bid', 'date']
  
  for param in params:
    if param not in data:
      return make_response(jsonify('Parameters are not enough.'), 400)  

  json_data = []

  valuedata = db.session.query(func.date_format(SensorData.datetime,'%H').label('date'),
  func.sum(SensorData.walk_steps).label('walk_steps'), 
  func.sum(SensorData.run_steps).label('run_steps')).\
      filter(SensorData.FK_bid == data['bid']).\
        filter(func.date(SensorData.datetime) == data['date']).\
          group_by(func.hour(SensorData.datetime)).all()
    #valuedata = db.session.query(getAttribute(data['dataname'], SensorData).label('y'), SensorData.datetime.label('x')).filter(SensorData.FK_bid == data['bid']).filter(func.date(SensorData.datetime) == i).all()
  json_data = {
    "date": [],
    "walk_steps": [],
    "run_steps": []
  }  
  for b in valuedata :
    json_data['date'].append(b.date)
    json_data['walk_steps'].append(int(b.walk_steps))
    json_data['run_steps'].append(int(b.run_steps))

  result = {
    "result": "OK",
    "data": json_data
  }

  return make_response(jsonify(result), 200)

@app.route('/api/efwb/v1/sensordata/date', methods=["POST"])
def sensordata_date_post_api():
  data = json.loads(request.data)

  params = ['bid']
  
  for param in params:
    if param not in data:
      return make_response(jsonify('Parameters are not enough.'), 400)  

  json_data = []

  valuedata = db.session.query(func.date_format(SensorData.datetime, "%Y-%m-%d").label('date')).\
      filter(SensorData.FK_bid == data['bid']).\
      group_by(func.date(SensorData.datetime)).all()
    #valuedata = db.session.query(getAttribute(data['dataname'], SensorData).label('y'), SensorData.datetime.label('x')).filter(SensorData.FK_bid == data['bid']).filter(func.date(SensorData.datetime) == i).all()
  json_data = []
  for b in valuedata :
    json_data.append(b.date)

  result = {
    "result": "OK",
    "data": json_data
  }

  return make_response(jsonify(result), 200)

@app.route('/api/efwb/v1/gatewaylog/add', methods=["POST"])
@token_required
def gatewaylog_post_api():
  data = json.loads(request.data)
  params = ['pid', 'type']

  for param in params :
    if param not in data:
      return make_response(jsonify('Parameters are not enough.'), 400)
  gatewaylog = GatewayLog()
  gatewaylog.FK_pid = data['pid']
  gatewaylog.type = data['type']

  db.session.add(gatewaylog)
  db.session.commit()
  db.session.flush()
  result = {
      "result": "OK"
    }

  return make_response(jsonify(result), 200)

@app.route('/api/efwb/v1/bandlog/add', methods=["POST"])
@token_required
def bandlog_post_api():
  data = json.loads(request.data)
  params = ['bid', 'type']

  for param in params :
    if param not in data:
      return make_response(jsonify('Parameters are not enough.'), 400)
  bandlog = BandLog()
  bandlog.FK_bid = data['bid']
  bandlog.type = data['type']

  db.session.add(bandlog)
  db.session.commit()
  db.session.flush()
  result = {
      "result": "OK"
    }

  return make_response(jsonify(result), 200)  

def addDBList(table, list1, list2, lengthCheck, tableCheck):
  users_table = table
  for i in range(len(list2)):
    if lengthCheck :
      users_table.FK_uid = list2[i]
      if tableCheck:
        users_table.FK_gid = list1[0]
      else:
        users_table.FK_bid = list1[0]
      
    else :
      users_table = table
      users_table.FK_uid = list1[0]
      if tableCheck:
        users_table.FK_gid = list2[i]
      else:
        users_table.FK_bid = list1[0]
    
  return users_table
# @app.route('/api/efwb/v1/access_history/login', methods=['POST'])
# def access_history_login_post_api():

#   result = ''
#   print('access_history_login_post_api')
#   user_agent = request.environ.get('HTTP_USER_AGENT')
#   os_ver, browser_ver = get_os_browser_from_useragent(user_agent)
#   ip_addr = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
#   accesshistory = AccessHistory.query.filter_by(ip_addr = ip_addr).\
#     filter_by(os_ver = os_ver).\
#       filter_by(browser_ver = browser_ver).\
#         filter(AccessHistory.token != None).first()
#   if accesshistory is None:
#     print("accesshistory in none")
#   else: 
#     print("accesshistory exits")
#     login = Login()
#     login.FK_ah_id = accesshistory.id
    
#     db.session.add(login)
#     db.session.commit()
#     result = {'status': True, 'reason': 0, 'user': accesshistory.user.serialize()}
#   return make_response(jsonify(result), 200)

@app.route('/api/efwb/v1/access_history/reload', methods=['POST'])
def access_history_reload_post_api():
  print('access_history_reload_post_api')
  data = json.loads(request.data)
  result = ''
  if data['token'] is None:
    print("token is none")
    
  else :
    accesshistory = AccessHistory.query.filter_by(token=data['token']).first()
    if accesshistory is None:
      print("accesshistory in none")
    else: 
      print("accesshistory exits")
      result = {'status': True, 'reason': 0, 'user': accesshistory.user.serialize()}
  return make_response(jsonify(result), 200)  

# @app.route('/api/efwb/v1/access_history/unload', methods=['POST'])
# def access_history_unload_post_api():
#   print('access_history_unload_post_api')
#   parser = reqparse.RequestParser()
#   parser.add_argument("token", type=str, location="headers")
#   token = parser.parse_args()["token"]
#   result=''
#   if token is None:
#     print("token is none")
#     return make_response(jsonify(result), 200)  
#   accesshistory = AccessHistory.query.filter_by(token=token).first()
#   if accesshistory is None:
#     print("accesshistory in none")
#     return make_response(jsonify({}), 200)
#   else: 
#     print("accesshistory exits")
#     login = Login.query.filter_by(FK_user_id=accesshistory.id).order_by(Login.datetime.desc()).first
#     if login is not None:
#       db.session.delete(login)
#       db.session.commit()  
#   return make_response(jsonify({}), 200)

@app.route('/example', methods=['GET'])
def get_example():
  dev = db.session.query(func.count(SensorData.id).label('count')).\
    filter(SensorData.FK_bid==10).\
    filter(SensorData.datetime>func.date_add(func.now(), text('interval -30 second'))).\
      filter(or_(SensorData.scdState== 0, SensorData.scdState==1)).first()
  print(dev.count)
  result = {}
  return make_response(jsonify(result), 200)
@app.route('/api/efwb/v1/maps/<pid>', methods=['GET'])
def get_maps_api(pid):
  dev = Gateways.query.filter_by(id=pid).first()
  result = {}
  if dev is None :
    return make_response(result, 200)
  url = "https://maps.googleapis.com/maps/api/elevation/json?locations="+str(dev.lat)+","+str(dev.lng)+"&key=AIzaSyCzNNbWs9lVCSVExf1fWhs_l7Qv3GVus2c"

  payload={}
  headers = {}

  response = requests.request("GET", url, headers=headers, data=payload)
  result=response.text
  return make_response(result, 200)

def get_height_api(pid):
  dev = Gateways.query.filter_by(id=pid).first()
  result = {}
  if dev is None :
    return make_response(result, 200)
  url = "https://maps.googleapis.com/maps/api/elevation/json?locations="+str(dev.lat)+","+str(dev.lng)+"&key=AIzaSyCzNNbWs9lVCSVExf1fWhs_l7Qv3GVus2c"

  payload={}
  headers = {}

  response = requests.request("GET", url, headers=headers, data=payload)
  result=response.text
  print(result)

# @app.route('/api/efwb/v1/events/get', methods=['POST'])
# def get_event_api():
#   data = json.loads(request.data)
#   params = ['bid','type']

#   for param in params:
#     if param not in data:
#       return make_response(jsonify('Parameters are not enough.'), 400)
#   eventDev = Events.query.filter_by(FK_bid=data['bid']).filter_by(type=data['type']).order_by(Events.datetime.desc()).first()
#   if eventDev is None:
#       return make_response(jsonify('event is not found.'), 404)
#   print(eventDev.datetime)
#   print(datetime.datetime.now())
#   time1 = eventDev.datetime
#   time2 = datetime.datetime.now()
#   print((time2-time1).seconds)
#   return make_response(jsonify(eventDev.serialize()), 200)


# @app.route('/api/efwb/v1/events', methods=['POST'])
# def post_event_api():
#   eventDev = Events()
#   eventDev.event = 0
#   eventDev.FK_bid = 1
#   eventDev.value = 0

#   db.session.add(eventDev)
#   db.session.commit()
#   db.session.flush()
#   return make_response({}, 200)
def addDBUserBandList(db, list1, list2, check):
  for i in range(len(list2)):
    if check :
      users_bands = UsersBands()
      users_bands.FK_uid = list2[i]
      users_bands.FK_bid =  list1[0]
      db.session.add(users_bands)
    else :
      users_bands = UsersBands()
      users_bands.FK_uid = list1[0]
      users_bands.FK_bid = list2[i]
      db.session.add(users_bands)
  return db
def password_encoder_512(password):
    h = hashlib.sha512()
    h.update(password.encode('utf-8'))
    return h.hexdigest()
def get_os_browser_from_useragent(userAgent):
    os_ver = "Unknown"
    browser_ver = "Unknown"
    
    if userAgent.find("Linux") != -1:
        os_ver = "Linux"
    elif userAgent.find("Mac") != -1:
        os_ver = "MacOS"
    elif userAgent.find("X11") != -1:
        os_ver = "UNIX"
    elif userAgent.find("Win") != -1:
        os_ver = "Windows"
  
    if userAgent.find("MSIE 6") != -1:
        browser_ver = "Internet Explorer 6"
    elif userAgent.find("MSIE 7") != -1:
        browser_ver = "Internet Explorer 7"
    elif userAgent.find("MSIE 8") != -1:
        browser_ver = "Internet Explorer 8"
    elif userAgent.find("MSIE 9") != -1:
        browser_ver = "Internet Explorer 9"
    elif userAgent.find("MSIE 10") != -1:
        browser_ver = "Internet Explorer 10"
    elif userAgent.find("Trident") != -1 or userAgent.find("trident") != -1:
        browser_ver = "Internet Explorer 11"
    elif userAgent.find("Firefox") != -1:
        browser_ver = "Firefox"
    elif userAgent.find("Opera") != -1:
        browser_ver = "Opera"
    elif userAgent.find("Edge") != -1 or userAgent.find("edge") != -1 or userAgent.find("Edg") != -1:
        browser_ver = "Microsoft Edge"

    elif userAgent.find("Chrome") != -1:
        browser_ver = "Chrome"
    elif userAgent.find("Safari") != -1 or userAgent.find("safari") != -1:
        browser_ver = "Safari"

    return os_ver, browser_ver
