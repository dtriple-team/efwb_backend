# -*- coding: utf-8 -*-
print("module [backend.api_band] loaded")


import hashlib
import requests
from threading import Lock
from backend import app, socketio, mqtt, login_manager
from flask import make_response, jsonify, request, json
from flask_restless import ProcessingException
from flask_restful import reqparse
from datetime import datetime
from functools import wraps
from backend.db.table.table_band import *
from backend.db.service.query import *
from backend.api.crawling import *
from backend.api.socket import *
from sqlalchemy import func, case, or_, Interval
from sqlalchemy.sql.expression import text

from datetime import date, timedelta
from urllib.request import urlopen
from bs4 import BeautifulSoup

count = 0
spo2BandData = {}

gateway_thread = None
mqtt_thread = None
airpressure_thread = None
thread_lock = Lock()
example_thread = None
gw_thread = None
work = False

def setGatewayLog(gid, gpid, check):
  print("[method] setGatewayLog")
  if check:
    updateGatewaysConnect(gid, 1)
  else :
    updateGatewaysConnect(gid, 0)
    for b in selectBandsConnectGateway(gid):
      insertConnectBandLog(b.id, 0)
      updateConnectBands(b.id, 0)
    gateway={
      "panid": gpid,
      "bandnum": 0,
      "connectstate": False
    }
    socket_emit('gateway_connect', gateway)

def gatewayCheck():
  global work
  while True:
    socketio.sleep(120)
    print("gatewayCheck start")
    work = True
    try:
      gateways = selectGatewayAll()
      for g in gateways:
        time1 = g.connect_check_time.replace(tzinfo=None)
        time2 = datetime.datetime.now(timezone('Asia/Seoul')).replace(tzinfo=None)
        if (time2-time1).seconds > 120:
          if g.connect_state==1 :
              setGatewayLog(g.id, g.pid, False)
          else:
            dev = selectGatewayLog(g.id)
            if dev is None:
              setGatewayLog(g.id, g.pid, False)

    except Exception as e:
      print(e)
    work = False

def getAirpressureTask():
  global work
  while True:
    socketio.sleep(3600)
    print("getAltitud start")
    work = True
    dev = selectGatewayAll()
    for g in dev:
    
      d = datetime.datetime.now(timezone('Asia/Seoul'))
      urldate = str(d.year)+"."+str(d.month)+"."+str(d.day)+"."+str(d.hour)
      airpressure = getAirpressure(urldate, g.location)

      if airpressure != 0 :
        updateGatewaysAirpressure(g.id, airpressure)
    work = False

def gatewayCheckThread():
  global gateway_thread

  with thread_lock:
    if gateway_thread is None:
      gateway_thread = socketio.start_background_task(gatewayCheck)

def getAirpressureThread():
  global airpressure_thread

  with thread_lock:
    if airpressure_thread is None:
      airpressure_thread = socketio.start_background_task(getAirpressureTask)


def getAltitude(pressure, airpressure): # 기압 - 높이 계산 Dtriple
  try:
    p = (pressure / (airpressure * 100)); # ***분모 자리에 해면기압 정보 넣을 것!! (ex. 1018) // Dtriple
    b = 1 / 5.255
    alt = 44330 * (1 - p**b)
 
    return round(alt,2)
  except:
    pass
 
def messageReceived(methods=['GET', 'POST']):
  print('message was received!!!')

def handle_sync_data(mqtt_data, extAddress):
  # print("start handle_sync_data")
  # global spo2BandData
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
    db.session.close()
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
      socketio.emit('efwbsync', mqtt_data, namespace='/receiver', callback=messageReceived)
      print("close handle_sync_data")
    except Exception as e :
      print("****** error ********")
      print(e)

def handle_gateway_state(panid):
  print("handle_gateway_state", panid)
  try:
    dev = db.session.query(Gateways).filter_by(pid=panid['panid']).first()
    if dev is not None:
      if dev.connect_state == 0:
        setGatewayLog(dev.id, True)
        db.session.query(Gateways).\
          filter_by(id=dev.id).\
            update(dict(connect_state=1, connect_time = datetime.datetime.now(timezone('Asia/Seoul')), 
            connect_check_time=datetime.datetime.now(timezone('Asia/Seoul'))))
      else :
        db.session.query(Gateways).filter_by(id=dev.id).update(dict(connect_check_time=datetime.datetime.now(timezone('Asia/Seoul'))))
      db.session.commit()
      db.session.flush()
    socketio.emit('gateway_connect', panid, namespace='/receiver')
  except:
    pass

def handle_gateway_bandnum(panid):
  try:
    dev = db.session.query(Gateways).filter_by(pid=panid['panid']).first()
    if dev is not None:
      if dev.connect_state == 0:
        setGatewayLog(dev.id, True)
        db.session.query(Gateways).\
          filter_by(id=dev.id).\
            update(dict(connect_state=1, connect_time = datetime.datetime.now(timezone('Asia/Seoul')), 
            connect_check_time=datetime.datetime.now(timezone('Asia/Seoul'))))
      else :
        db.session.query(Gateways).filter_by(id=dev.id).update(dict(connect_check_time=datetime.datetime.now(timezone('Asia/Seoul'))))
      db.session.commit()
      db.session.flush()
    socketio.emit('gateway_connect', panid, namespace='/receiver')
  except:
    pass

@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
  global mqtt_thread
  global gw_thread, work
  if message.topic == '/efwb/post/sync':
    if work==False :
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
     
  elif message.topic == '/efwb/bandnum' :
     handle_gateway_bandnum(json.loads(message.payload))
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
  global work
  work = True
  print("======================vital sign===============")
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
    valuedata = db.session.query(func.avg(getAttribute(data['dataname'], 
    SensorData)).label('y'), func.date_format(SensorData.datetime, '%H').\
      label('x')).filter(SensorData.FK_bid == data['bid']).\
        filter(func.date(SensorData.datetime) == i).\
          group_by(func.hour(SensorData.datetime)).all()
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

    # dev = db.session.query(func.min(getAttribute(data['dataname'], SensorData)).label('min'), func.max(getAttribute(data['dataname'], SensorData)).label('max'), func.avg(getAttribute(data['dataname'], SensorData)).label('avg')).filter(SensorData.FK_bid == data['bid']).filter(func.date(SensorData.datetime) == i).all()
    # for b in dev: 
    #   resultJSON = {
    #     "minmax":str(b.min)+" - "+str(b.max), 
    #     "normal": float(b.avg),
    #   }
    dayValue = date(int(i[0:4]), int(i[5:7]), int(i[8:10])).weekday()
    dateValue = i[5:7]+"월 "+i[8:10]+"일 "+day[dayValue]
    json_data.append({"date": dateValue,  "data": sensordata_list})

  result = {
    "result": "OK",
    "data": json_data
  }
  work = False
  return make_response(jsonify(result), 200)  

@app.route('/api/efwb/v1/sensordata/activity', methods=['POST'])
def activity_day_get_api():
  global work
  work = True
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
  work = False
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
  global work
  work = True
  data = json.loads(request.data)
  params = ['bid', 'days']

  for param in params:
    if param not in data:
      return make_response(jsonify('Parameters are not enough.'), 400) 
  json_data = []
  dev = []
  print(data)
  if len(data['days']) == 0 :
    if data['bid'] != -1 :
      dev = db.session.query(Events).\
      distinct(Events.datetime, Events.type).\
        filter(Events.FK_bid==data['bid']).\
          group_by(Events.datetime, Events.type).\
            all()
    else :
      dev = db.session.query(Events).\
      distinct(Events.datetime, Events.type).\
        group_by(Events.datetime, Events.type).\
          all()
  else :
    if data['bid'] != -1:
      dev = db.session.query(Events).\
        distinct(Events.datetime, Events.type).\
        filter(Events.FK_bid==data['bid']).\
          filter(func.date(Events.datetime).\
            between(data['days'][0], datetimeBetween(data['days']))).\
              group_by(Events.datetime, Events.type).all()
    else:
      
      dev = db.session.query(Events).\
        distinct(Events.datetime, Events.type).\
          filter(func.date(Events.datetime).\
            between(data['days'][0], datetimeBetween(data['days']))).\
              group_by(Events.datetime, Events.type).all()

  for i in dev:
    json_data.append(i.serialize())
  result = {
    "result": "OK",
    "data": json_data
  }

  work = False
  return make_response(jsonify(result), 200)
@app.route('/api/efwb/v1/events/fall_detect/all', methods=["POST"])
def events_all_fall_post_api():
  global work
  work = True
  data = json.loads(request.data)
  params = ['uid']

  for param in params:
    if param not in data:
      return make_response(jsonify('Parameters are not enough.'), 400) 
  json_data = []
  dev = []
  time = datetime.datetime.now()
  for d in range(6, -1, -1):
    dateti = time + timedelta(days=-d)
    dev = db.session.query(func.date_format(dateti, '%m/%d').label('day'),
    func.ifnull(func.sum(Events.value), 0).label('fall')).\
      filter(Users.id == data['uid']).\
        filter(Users.id == UsersGateways.FK_uid).\
          filter(UsersGateways.FK_pid == GatewaysBands.FK_pid).\
            filter(GatewaysBands.FK_bid == Events.FK_bid).\
              filter(Events.type==0).\
                filter(func.date_format(Events.datetime,'%Y-%m-%d') == func.date_format(dateti,'%Y-%m-%d')).first()
    json_data.append({"x": dev.day, "y": int(dev.fall)})
  work = False
  return make_response(jsonify(json_data), 200) 
  
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
    distinct(Events.datetime).\
      filter(Events.FK_bid==data['bid']).\
        filter(Events.type==0).\
          group_by(func.date(Events.datetime)).all()
  else :
    dev = db.session.query(func.date_format(Events.datetime,'%Y-%m-%d').label('date'),
  func.sum(Events.value).label('data')).\
    distinct(Events.datetime).\
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
@app.route('/api/example', methods=["GET"])
def example():
  d = datetime.datetime.now(timezone('Asia/Seoul'))
  urldate = str(d.year)+"."+str(d.month)+"."+str(d.day)+"."+str(d.hour)
  html = requests.get("https://web.kma.go.kr/weather/observation/currentweather.jsp?auto_man=m&stn=0&type=t99&reg=100&tm="+urldate+"%3A00&x=25&y=1")  

  bsObject = BeautifulSoup(html.text, "html.parser") 
  temp = bsObject.find("table", {"class": "table_develop3"})
  trtemp = temp.find_all('tr')
  atemp = temp.find_all('a')
  for a in range(len(atemp)):
    if atemp[a].text == "대구":
      break
  tdtemp = trtemp[a+2].find_all('td')

  print(tdtemp[len(tdtemp)-1].text)
@app.route('/api/efwb/v1/weather/<where>', methods=["GET"])
def get_weather_api(where):
  global work
  work = True
  result=getWeather(where)
  work = False
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
