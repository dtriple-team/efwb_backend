# -*- coding: utf-8 -*-
print("module [backend.api_band] loaded")


import hashlib

from sqlalchemy.sql.elements import Null
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
from sqlalchemy import func, case
from datetime import date
spo2BandData = {}
stateBandData = {}

mqtt.subscribe('/efwb/sync')
mqtt.subscribe('/efwb/connectcheck')

@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    print("mqtt connect")

@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
  if message.topic == '/efwb/sync':
    mqtt_data = json.loads(message.payload.decode())
    try : 
      global stateBandData, spo2BandData
      
      
      if mqtt_data['extAddress']['low'] not in spo2BandData :
        spo2BandData[mqtt_data['extAddress']['low']] = 0
        stateBandData[mqtt_data['extAddress']['low']] = False
      bandData = mqtt_data['bandData']
      data = SensorData()
      data.FK_bid = mqtt_data['shortAddress']

      data.start_byte = bandData['start_byte']
      data.sample_count = bandData['sample_count']
      data.fall_detect = bandData['fall_detect']
      data.battery_level = bandData['battery_level']
      data.hrConfidence = bandData['hrConfidence']
      data.spo2Confidence = bandData['spo2Confidence']
      data.hr = bandData['hr']
      if bandData['spo2']<=1000 and bandData['spo2']>=400:
          data.spo2 = bandData['spo2']
          spo2BandData[mqtt_data['extAddress']['low']] = bandData['spo2']
          mqtt_data['bandData']['spo2'] = bandData['spo2']
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
      data.walk_steps = bandData['walk_steps']
      data.run_steps = bandData['run_steps']  
        
      data.x = bandData['x']
      data.y = bandData['y']
      data.z = bandData['z']
      data.t = bandData['t'] 
        # if bandData['h']>=0:
        #     data.h = bandData['h']
        #     historyBandData = bandData
        #     mqtt_data['bandData']['h'] = bandData['h']
        # else :
        #     if historyBandData['spo2']>1000 and historyBandData['spo2']<0:
        #         data.spo2 = 0
        #         mqtt_data['bandData']['spo2'] = 0
        #     else :
        #         data.spo2 = historyBandData['spo2']/10
        #         mqtt_data['bandData']['spo2'] = historyBandData['spo2']/10

      data.h = bandData['h']  

      data.rssi = mqtt_data['rssi']   
      
      db.session.add(data)
      db.session.commit()
      if mqtt_data['active'] == 'true':
        if stateBandData[mqtt_data['extAddress']['low']] == False :
          stateBandData[mqtt_data['extAddress']['low']] = True
          dev = Bands.query.filter(Bands.id == mqtt_data['shortAddress']).first()
          if dev is not None: 
            Bands.query.filter_by(id = dev.id).update({
              "connect_time": datetime.datetime.now(timezone('Asia/Seoul'))
            })
            db.session.commit()
      
      else :
        if stateBandData[mqtt_data['extAddress']['low']] == True :
          stateBandData[mqtt_data['extAddress']['low']] = False
          dev = Bands.query.filter(Bands.id == mqtt_data['shortAddress']).first()
          if dev is not None: 
            Bands.query.filter_by(id = dev.id).update({
              "disconnect_time": datetime.datetime.now(timezone('Asia/Seoul'))
            })
            db.session.commit()
      
      if bandData['fall_detect'] == 1 :
        dev = Bands.query.filter(Bands.id == mqtt_data['shortAddress']).first()
        if dev is not None: 
          event = {
            "type" : 0,
            "value" : 1,
            "message" : hex(dev.serialize()['bid']) + " " + dev.serialize()['name']
          }
          socketio.emit('efwbasync', event, namespace='/receiver')
      socketio.emit('efwbsync', mqtt_data, namespace='/receiver')
    except Exception as e :
      print("****** error ********")
      print(e)
  elif message.topic == '/efwb/connectcheck':
    connect_check = json.loads(message.payload.decode())
    gatewaydata = Gateways.query.filter_by(pid=connect_check['panCoord']['panId']).first()
    print(gatewaydata.alias)
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
                server_name = request.environ.get('SERVER_NAME')
                user_agent = request.environ.get('HTTP_USER_AGENT')
                new_access_history.server_name = server_name
                new_access_history.os_ver, new_access_history.browser_ver = get_os_browser_from_useragent(user_agent)
                new_access_history.ip_addr = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
                new_access_history.token = loginuser.token
                new_access_history.user_id = loginuser.username
                new_access_history.FK_user_id = loginuser.id
                db.session.add(new_access_history)
              
                db.session.commit()
                
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
        new_access_history.type = 1  # Login
        server_name = request.environ.get('SERVER_NAME')
        user_agent = request.environ.get('HTTP_USER_AGENT')
        new_access_history.server_name = server_name
        new_access_history.os_ver, new_access_history.browser_ver = get_os_browser_from_useragent(user_agent)
        new_access_history.ip_addr = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
        new_access_history.user_id = loginuser.user_id
        new_access_history.FK_user_id = loginuser.FK_user_id
        db.session.add(new_access_history)
                    
        db.session.commit()

    
    
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

    user = Users.query.filter_by(token=token).first()
    if user is None:
        raise ProcessingException(description="Not Authorized", code=411)

    return user

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

@app.route('/api/efwb/v1/users/gatewayinfo/<id>', methods=['GET'])
@token_required
def user_gatewayinfo_api(id):
  dev = db.session.query(Gateways).filter(UsersGateways.FK_pid == Gateways.id).filter(UsersGateways.FK_uid==id).all()
  gatewaylist = []
  if dev is None:
    return make_response(jsonify('User is not Found.'), 404)
  print(dev)
  for b in dev :
    gatewaylist.append(b.serialize())
  print(gatewaylist)
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
  print(dev)
  for b in dev :
    bandlist.append(b.serialize())
  print(bandlist)
  result = {
    "result":"OK",
    "data":bandlist
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

    params = ['bid']
    for param in params:
          if param not in data:
              return make_response(jsonify('Parameters are not enough.'), 400)
    dev = Bands.query.filter(Bands.bid == data['bid']).first()
    if dev is None:
      return make_response(jsonify('User is not found.'), 404)
    result = {
      "result": "OK",
      "users": dev.serialize()
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
      commit_db = addDBList(db, data['gids'], data['uids'], True)

    elif len(data['uids'])<len(data['gids']):
      print('gid 등록')
      commit_db = addDBList(db, data['uids'], data['gids'], False)
        
    else:
      commit_db = addDBList(db, data['gids'], data['uids'], True)

    commit_db.session.commit()
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
      commit_db = addDBUserBandList(db, data['bids'], data['uids'], True)

    elif len(data['uids'])<len(data['bids']):
      commit_db = addDBUserBandList(db, data['uids'], data['bids'], False)
        
    else:
      commit_db = addDBUserBandList(db, data['bids'], data['uids'], True)

    commit_db.session.commit()
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
@token_required
def sensordata_day_get_api():


  data = json.loads(request.data)

  params = ['bid','dataname', 'days']
  
  for param in params:
    if param not in data:
      return make_response(jsonify('Parameters are not enough.'), 400)  
  json_data = []
  day = ['월', '화', '수', '목', '금', '토', '일']
  for i in data['days'] :
    sensordata_list = {"label": [], "data": [] }  
    valuedata = db.session.query(func.avg(getAttribute(data['dataname'], SensorData)).label('y'), func.date_format(SensorData.datetime, '%H').label('x')).filter(SensorData.FK_bid == data['bid']).filter(func.date(SensorData.datetime) == i).group_by(func.hour(SensorData.datetime)).all()
    #valuedata = db.session.query(getAttribute(data['dataname'], SensorData).label('y'), SensorData.datetime.label('x')).filter(SensorData.FK_bid == data['bid']).filter(func.date(SensorData.datetime) == i).all()
    if not valuedata :
      continue
    
    for b in valuedata :
      sensordata_list['label'].append(b.x)
      sensordata_list['data'].append(float(b.y))

    dev = db.session.query(func.min(getAttribute(data['dataname'], SensorData)).label('min'), func.max(getAttribute(data['dataname'], SensorData)).label('max'), func.avg(getAttribute(data['dataname'], SensorData)).label('avg')).filter(SensorData.FK_bid == data['bid']).filter(func.date(SensorData.datetime) == i).all()
    for b in dev: 
      resultJSON = {
        "minmax":str(b.min)+" - "+str(b.max), 
        "normal": float(b.avg),
      }
    dayValue = date(int(i[0:4]), int(i[5:7]), int(i[8:10])).weekday()
    dateValue = i[6:7]+"월 "+i[8:10]+"일 "+day[dayValue]
    json_data.append({"date": dateValue, "total": resultJSON,  "value": sensordata_list})

   
    
  result = {
    "result": "OK",
    "data": json_data
  }

  return make_response(jsonify(result), 200)  

@app.route('/api/efwb/v1/sensordata/activity/day', methods=['POST'])
@token_required
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
    filter(func.date(SensorData.datetime).between(data['days'][0], data['days'][1])).\
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
@token_required
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
@token_required
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
  result = {
      "result": "OK"
    }

  return make_response(jsonify(result), 200)  

def addDBList(db, list1, list2, check):
  for i in range(len(list2)):
    if check :
      users_groups = UsersGroups()
      users_groups.FK_uid = list2[i]
      users_groups.FK_gid = list1[0]
      db.session.add(users_groups)
    else :
      users_groups = UsersGroups()
      users_groups.FK_uid = list1[0]
      users_groups.FK_gid = list2[i]
      db.session.add(users_groups)
    
  return db
@app.route('/api/efwb/v1/access_history/login', methods=['POST'])
def access_history_login_post_api():

  result = ''
  print('access_history_login_post_api')
  server_name = request.environ.get('SERVER_NAME')
  user_agent = request.environ.get('HTTP_USER_AGENT')
  os_ver, browser_ver = get_os_browser_from_useragent(user_agent)
  ip_addr = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
  accesshistory = AccessHistory.query.filter_by(ip_addr = ip_addr).\
    filter_by(server_name = server_name).\
      filter_by(os_ver = os_ver).\
        filter_by(browser_ver = browser_ver).\
          filter(AccessHistory.token != None).first()
  if accesshistory is None:
    print("accesshistory in none")
  else: 
    print("accesshistory exits")
    login = Login()
    login.FK_ah_id = accesshistory.id
    
    db.session.add(login)
    db.session.commit()
    result = {'status': True, 'reason': 0, 'user': accesshistory.user.serialize()}
  return make_response(jsonify(result), 200)

@app.route('/api/efwb/v1/access_history/reload', methods=['POST'])
def access_history_reload_post_api():
  print('access_history_reload_post_api')
  data = json.loads(request.data)
  parser = reqparse.RequestParser()
  parser.add_argument("token", type=str, location="headers")
  token = parser.parse_args()["token"]
  result = ''
  print(data)
  print(token)
  if data['token'] is None:
    print("token is none")
    return make_response(jsonify(result), 200)  
  accesshistory = AccessHistory.query.filter_by(token=data['token']).first()
  if accesshistory is None:
    print("accesshistory in none")
    return make_response(jsonify(result), 200)  
  else: 
    print("accesshistory exits")
    result = {'status': True, 'reason': 0, 'user': accesshistory.user.serialize()}
  return make_response(jsonify(result), 200)  

@app.route('/api/efwb/v1/access_history/unload', methods=['POST'])
def access_history_unload_post_api():
  print('access_history_unload_post_api')
  parser = reqparse.RequestParser()
  parser.add_argument("token", type=str, location="headers")
  token = parser.parse_args()["token"]
  result=''
  if token is None:
    print("token is none")
    return make_response(jsonify(result), 200)  
  accesshistory = AccessHistory.query.filter_by(token=token).first()
  if accesshistory is None:
    print("accesshistory in none")
    return make_response(jsonify({}), 200)
  else: 
    print("accesshistory exits")
    login = Login.query.filter_by(FK_user_id=accesshistory.id).order_by(Login.datetime.desc()).first
    if login is not None:
      db.session.delete(login)
      db.session.commit()  
  return make_response(jsonify({}), 200)
def addDBUserBandList(db, list1, list2, check):
  for i in range(len(list2)):
    if check :
      users_bands = UsersBands()
      users_bands.FK_uid = list2[i]
      users_bands.FK_bid = list1[0]
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
    print(userAgent)
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
