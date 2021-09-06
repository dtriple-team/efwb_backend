# -*- coding: utf-8 -*-
print("module [backend.api_band] loaded")

from threading import Lock
from backend import app, socketio, mqtt
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
historyBandData = {}

mqtt.subscribe('/efwb/sync')
@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    print("mqtt connect")

@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
  mqtt_data = json.loads(message.payload.decode())
  try : 
    global historyBandData
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
        historyBandData[mqtt_data['extAddress']['low']] = bandData['spo2']
        mqtt_data['bandData']['spo2'] = bandData['spo2']
    else :
      if mqtt_data['extAddress']['low'] in historyBandData :
        if  historyBandData[mqtt_data['extAddress']['low']]<=1000 and historyBandData[mqtt_data['extAddress']['low']]>=400:
            data.spo2 = historyBandData[mqtt_data['extAddress']['low']]
            mqtt_data['bandData']['spo2'] = historyBandData[mqtt_data['extAddress']['low']]
        else :
            data.spo2 = 0
            mqtt_data['bandData']['spo2'] = 0
            historyBandData[mqtt_data['extAddress']['low']] = 0
      else :
        data.spo2 = 0
        mqtt_data['bandData']['spo2'] = 0
        historyBandData[mqtt_data['extAddress']['low']] = 0
    
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
    
    DBManager.db.session.add(data)
    DBManager.db.session.commit()
    if bandData['fall_detect'] == 1 :
      dev = Bands.query.filter(Bands.bid == mqtt_data['shortAddress']).first()
      if dev is not None: 
        event = {
          "type" : 0,
          "value" : 1,
          "message" : hex(dev.serialize()['bid']) + " " + dev.serialize()['name']
        }
        socketio.emit('efwbasync', event, namespace='/receiver')
    socketio.emit('efwbsync', mqtt_data, namespace='/receiver')
  except Exception as e :
    print(e)

@socketio.on('connect', namespace='/receiver')
def connect():
   
  print("***socket connected***")
  emit('message', "socket connected")


@socketio.on('disconnect', namespace='/receiver')
def disconnect():
    print('Disconnected')


@app.route('/api/efwb/v1/group_table/add', methods=['POST'])
def group_post_api():
    data = json.loads(request.data)

    params = ['gid','groupname', 'permission']

    for param in params:
        if param not in data:
            return make_response(jsonify('Parameters are not enough.'), 400)

    group = group_table()
    group.gid = data['gid']
    group.groupname = data['groupname']
    group.permission = data['permission']


    db.session.add(group)
    db.session.commit()

    result = {
      "result": "OK"
    }

    return make_response(jsonify(result), 200)

@app.route('/api/efwb/v1/group_table/list', methods=['GET'])
def group_list_get_api():
  groups = group_table.query.all()
  group_list = []
  for gr in groups:
    group_list.append(gr.serialize())
  result = {
    "result": "OK",
    "groups": group_list
  }

  return make_response(jsonify(result), 200)
@app.route('/api/efwb/v1/group_table/detail', methods=['POST'])
def group_get_api():
  data = json.loads(request.data)
  params = ['gid']
  for param in params:
        if param not in data:
            return make_response(jsonify('Parameters are not enough.'), 400)
  dev = group_table.query.filter(group_table.id == data['gid']).first()
  if dev is None:
    return make_response(jsonify('Group is not found.'), 404)
  result = {
    "result": "OK",
    "groups": dev.serialize()
  }
  return make_response(jsonify(result), 200)

@app.route('/api/efwb/v1/group_table/update', methods=['PATCH'])
def group_update_api():
    data = json.loads(request.data)

    params = ['checkid','gid','groupname', 'permission']

    for param in params:
        if param not in data:
            return make_response(jsonify('Parameters are not enough.'), 400)
    
    dev = group_table.query.filter(group_table.gid == data['checkid']).first()
    
    if dev is None:
      return make_response(jsonify('User is not found.'), 404)

    group_table.query.filter(group_table.gid == data['checkid']).update(
      {'gid': data['gid'], 'groupname': data['groupname'], 
      'permission': data['permission']}
    )
    
    db.session.commit()    
    result = {
      "result": "OK",
    }

    return make_response(jsonify(result), 200)  

@app.route('/api/efwb/v1/group_table/delete', methods=['DELETE'])
def group_delete_api():
    data = json.loads(request.data)

    params = ['gid']

    for param in params:
        if param not in data:
            return make_response(jsonify('Parameters are not enough.'), 400)
    
    group = group_table.query.filter(group_table.gid == data['gid']).first()
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


@app.route('/api/efwb/v1/user_table/add', methods=['POST'])
def user_post_api():
    data = json.loads(request.data)

    params = ['uid','username', 'name', 'password']

    for param in params:
        if param not in data:
            return make_response(jsonify('Parameters are not enough.'), 400)

    user = user_table()
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
@app.route('/api/efwb/v1/user_table/list', methods=['GET'])
def user_list_get_api():
  users = user_table.query.all()
  user_list = []
  for ur in users:
    user_list.append(ur.serialize())
  result = {
    "result": "OK",
    "users": user_list
  }

  return make_response(jsonify(result), 200)

@app.route('/api/efwb/v1/user_table/detail', methods=['POST'])
def user_detail_get_api():

    data = json.loads(request.data)

    params = ['uid']
    for param in params:
          if param not in data:
              return make_response(jsonify('Parameters are not enough.'), 400)
    dev = user_table.query.filter(user_table.id == data['uid']).first()
    if dev is None:
      return make_response(jsonify('User is not found.'), 404)
    result = {
      "result": "OK",
      "users": dev.serialize()
    }

    return make_response(jsonify(result), 200)

@app.route('/api/efwb/v1/user_table/update', methods=['PATCH'])
def user_update_api():
    data = json.loads(request.data)

    params = ['checkid','uid','username', 'name', 'password']

    for param in params:
        if param not in data:
            return make_response(jsonify('Parameters are not enough.'), 400)
    dev = user_table.query.filter(user_table.uid == data['checkid']).first()
    if dev is None:
      return make_response(jsonify('User is not found.'), 404)

    user_table.query.filter(user_table.uid == data['checkid']).update(
      {'uid': data['uid'], 'username': data['username'], 'password': DBManager.password_encoder_512(data['password']),
      'name': data['name']}
    )
    db.session.commit()    
    result = {
      "result": "OK",
    }

    return make_response(jsonify(result), 200)  
@app.route('/api/efwb/v1/user_table/delete', methods=['DELETE'])
def user_delete_api():
    data = json.loads(request.data)

    params = ['uid']

    for param in params:
        if param not in data:
            return make_response(jsonify('Parameters are not enough.'), 400)
    
    user = user_table.query.filter(user_table.uid == data['uid']).first()
    if user is None:
      return make_response(jsonify('User is not found.'), 404)

    db.session.delete(user)
    db.session.commit()    
    result = {
      "result": "OK",
    }

    return make_response(jsonify(result), 200) 
@app.route('/api/efwb/v1/user_table/<username>', methods=['GET'])
def username_check_api(username):
  dev = user_table.query.filter(user_table.username==username).first()

  if dev is None:
    return make_response(jsonify('User is not Found.'), 404)
  result = {
    "result":"OK",
    "data":dev.serialize()
  }
  return make_response(jsonify(result), 200)
@app.route('/api/efwb/v1/user_table/groupinfo/<id>', methods=['GET'])
def user_groupdinfo_api(id):
  dev = db.session.query(group_table).filter(UsersGroups.FK_gid == group_table.id).filter(UsersGroups.FK_uid==id).all()
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

@app.route('/api/efwb/v1/user_table/bandinfo/<id>', methods=['GET'])
def user_bandinfo_api(id):
  dev = db.session.query(Bands).filter(UsersBands.FK_bid == Bands.id).filter(UsersBands.FK_uid==id).all()
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

@app.route('/api/efwb/v1/bands/add', methods=['POST'])
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
def band_update_api():
    data = json.loads(request.data)

    params = ['checkid','bid','alias', 'name', 'gender', 'birth']

    for param in params:
        if param not in data:
            return make_response(jsonify('Parameters are not enough.'), 400)
    band = Bands.query.filter(Bands.bid == data['checkid']).first()
    if band is None:
      return make_response(jsonify('User is not found.'), 404)

    Bands.query.filter(Bands.bid == data['checkid']).update(
      {
            "bid": data['bid'],
            "alias": data['alias'],
            "name": data['name'],
            "gender": data['gender'],
            "birth": data['birth']
        }
    )
    db.session.commit()    
    result = {
      "result": "OK",
    }

    return make_response(jsonify(result), 200)  

@app.route('/api/efwb/v1/bands/delete', methods=['DELETE'])
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
@app.route('/api/efwb/v1/bands/userinfo/<id>', methods=['GET'])
def band_userinfo_api(id):
  dev = db.session.query(user_table).filter(UsersBands.FK_uid == user_table.id).filter(UsersBands.FK_bid==id).all()
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
@app.route('/api/efwb/v1/users_groups/add', methods=['POST'])
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

@app.route('/api/efwb/v1/users_groups/detail', methods=['POST'])
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

@app.route('/api/efwb/v1/users_groups/list', methods=['GET'])
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

@app.route('/api/efwb/v1/users_groups/delete', methods=['DELETE'])
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

@app.route('/api/efwb/v1/users_bands/detail', methods=['POST'])
def users_bands_detail_get_api():
    data = json.loads(request.data)
    users_bands_list = []
    params = ['bid', 'uid']
    
    if params[0] in data :
      dev = UsersBands.query.filter(UsersBands.FK_bid == data['bid']).all()
      if dev is None:
        return make_response(jsonify('UsersGroups is not found.'), 404)
      for ub in dev :
        users_bands_list.append(ub.serialize())

    elif params[1] in data :
      dev = UsersBands.query.filter(UsersBands.FK_uid == data['uid']).all()
      if dev is None:
        return make_response(jsonify('UsersGroups is not found.'), 404)
      for ub in dev :
        users_bands_list.append(ub.serialize())

    else :
      return make_response(jsonify('Parameters are not enough.'), 400)
    
    result = {
      "result": "OK",
      "users_bands": users_bands_list
    }

    return make_response(jsonify(result), 200)

@app.route('/api/efwb/v1/users_bands/list', methods=['GET'])
def users_bands_list_get_api():
  users_bands = UsersBands.query.all()
  users_bands_list = []
  for ub in users_bands:
    users_bands_list.append(ub.serialize())
  result = {
    "result": "OK",
    "users": users_bands_list
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

@app.route('/api/efwb/v1/users_bands/delete', methods=['DELETE'])
def users_bands_delete_api():
    data = json.loads(request.data)

    params = ['uids', 'bids']
    flag = False
    for param in params:
        if param not in data:
            return make_response(jsonify('Parameters are not enough.'), 400)
    for uid in data['uids']:
      for bid in data['bids']:
        band = UsersBands.query.filter(UsersBands.FK_uid == uid).filter(UsersBands.FK_bid == bid)
        if band.all() :
          flag = True
          band.delete()

    if flag == False :
      return make_response(jsonify('UsersBands is not found.'), 404)       
    db.session.commit()    
    result = {
      "result": "OK",
    }
    
    return make_response(jsonify(result), 200)  

@app.route('/api/efwb/v1/sensordata/list', methods=['GET'])
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
<<<<<<< HEAD
    sensordata_list = []  
    valuedata = db.session.query(func.avg(getAttribute(data['dataname'], SensorData)).label('y'), func.date_format(SensorData.datetime, '%Y-%m-%d %H:00').label('x')).filter(SensorData.FK_bid == data['bid']).filter(func.date(SensorData.datetime) == i).group_by(func.hour(SensorData.datetime)).all()
    #valuedata = db.session.query(SensorData.hr.label('y'), SensorData.datetime.label('x')).filter(SensorData.FK_bid == data['bid']).filter(func.date(SensorData.datetime) == i).all()
=======
    sensordata_list = {"label": [], "data": [] }  
    valuedata = db.session.query(func.avg(getAttribute(data['dataname'], SensorData)).label('y'), func.date_format(SensorData.datetime, '%H').label('x')).filter(SensorData.FK_bid == data['bid']).filter(func.date(SensorData.datetime) == i).group_by(func.hour(SensorData.datetime)).all()
    #valuedata = db.session.query(getAttribute(data['dataname'], SensorData).label('y'), SensorData.datetime.label('x')).filter(SensorData.FK_bid == data['bid']).filter(func.date(SensorData.datetime) == i).all()
>>>>>>> 6c9ed98f0a8745d5b18fb164f2e799929995da63
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
