# -*- coding: utf-8 -*-
from backend.db.service.select import *
from backend.api.mqtt import *
from datetime import date, timedelta
from sqlalchemy.sql.expression import text
from sqlalchemy import func, case, or_, Interval
from backend.api.socket import *
from backend.api.crawling import *
from backend.db.service.query import *
from backend.db.table.table_band import *
from functools import wraps
from datetime import datetime
from flask_restful import reqparse
from flask_restless import ProcessingException
from flask import make_response, jsonify, request, json
from backend import app, login_manager
import requests
import hashlib
import time

print("module [backend.api_band] loaded")


count = 0
work = False


def messageReceived(methods=['GET', 'POST']):
    print('message was received!!!')


@login_manager.user_loader
def load_user(id):
    user = DBManager.db.session.query(Users).get(id)
    return user


@app.route('/api/efwb/v1/setting', methods=['GET'])
def init_setting():
    mqtt.unsubscribe_all()
    mqtt.subscribe('/efwb/post/sync')
    mqtt.subscribe('/efwb/post/async')
    mqtt.subscribe('/efwb/post/connectcheck')

    return make_response("ok", 200)


@app.route('/api/efwb/v1/thread', methods=['GET'])
def init_thread():
    # sched.start()
    return make_response("ok", 200)


@app.route('/api/efwb/v1/login', methods=['POST'])
def login_api():
    print("login api")
    data = json.loads(request.data)
    result = ''

    if data['username'] is not None and data['password'] is not None:
        loginuser = db.session.query(Users).filter(
            Users.username == data["username"]).first()

        if loginuser is None:
            result = {'status': False, 'reason': 1}  # ID 없음
        else:
            if loginuser.password != password_encoder_512(data["password"]):
                result = {'status': False, 'reason': 2}  # PW 틀림
            
            # # 추가된 조건: permission이 0이 아닌 경우 로그인 실패
            # elif loginuser.permission != 0:
            #     result = {'status': False, 'reason': 3}  # 권한 없음

            else:  # Login 성공
                loginuser.last_login_time = datetime.now()
                loginuser.token = generate_token(data['username'])
                db.session.query(Users).filter(Users.username == data["username"])\
                    .update(dict(last_login_time=loginuser.last_login_time, token=loginuser.token))

                new_access_history = AccessHistory()
                new_access_history.type = 0  # Login
                user_agent = request.environ.get('HTTP_USER_AGENT')
                new_access_history.os_ver, new_access_history.browser_ver = get_os_browser_from_useragent(
                    user_agent)
                new_access_history.ip_addr = request.environ.get(
                    'HTTP_X_REAL_IP', request.remote_addr)
                new_access_history.token = loginuser.token
                new_access_history.user_id = loginuser.username
                new_access_history.FK_user_id = loginuser.id
                db.session.add(new_access_history)

                db.session.commit()
                db.session.flush()
                
                # 응답에 전체 사용자 정보 포함
                user_data = {
                    'id': loginuser.id,
                    'uid': loginuser.uid,
                    'username': loginuser.username,
                    'name': loginuser.name,
                    'email': loginuser.email,
                    'phone': loginuser.phone,
                    'age': loginuser.age,
                    'gender': 'M' if loginuser.gender == 1 else 'F',
                    'permission': loginuser.permission,
                    'token': loginuser.token,
                    'created': loginuser.created.strftime("%Y-%m-%d %H:%M:%S") if loginuser.created else None,
                    'last_login_time': loginuser.last_login_time.strftime("%Y-%m-%d %H:%M:%S")
                }
                
                result = {
                    'status': True, 
                    'reason': 0,
                    'user': user_data
                }

    return make_response(jsonify(result), 200)


@app.route("/api/efwb/v1/logout", methods=["POST"])
def logout_api():
    print("logout api")
    parser = reqparse.RequestParser()
    parser.add_argument("token", type=str, location="headers")
    token = parser.parse_args()["token"]
    if token is None:
        print("token is none")
    else:
        loginuser = AccessHistory.query.filter_by(token=token).first()

        if loginuser is None:
            print("user is none")
        else:

            AccessHistory.query.filter_by(token=token).update(dict(token=None))
            new_access_history = AccessHistory()
            new_access_history.type = 1  # Logout
            user_agent = request.environ.get('HTTP_USER_AGENT')
            new_access_history.os_ver, new_access_history.browser_ver = get_os_browser_from_useragent(
                user_agent)
            new_access_history.ip_addr = request.environ.get(
                'HTTP_X_REAL_IP', request.remote_addr)
            new_access_history.user_id = loginuser.user_id
            new_access_history.FK_user_id = loginuser.FK_user_id
            db.session.add(new_access_history)

            db.session.commit()
            db.session.flush()

    return make_response({}, 200)


def generate_token(userID):
    m = hashlib.sha1()

    m.update(userID.encode('utf-8'))
    m.update(datetime.now().isoformat().encode('utf-8'))

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


@app.route('/api/efwb/v1/groups/add', methods=['POST'])
@token_required
def group_post_api():
    data = json.loads(request.data)

    params = ['gid', 'groupname', 'permission']

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

    params = ['checkid', 'gid', 'groupname', 'permission']

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

    params = ['uid', 'username', 'name', 'password']

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

    params = ['checkid', 'uid', 'username', 'name', 'password']

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
def get_user_detail_by_username(username):
    """사용자 상세 정보 조회 API (username 기준)"""
    try:
        # 토큰 검증
        token = request.headers.get('token')
        if not token:
            return make_response(jsonify({
                'status': False,
                'reason': 'unauthorized',
                'message': '인증 정보가 없습니다.'
            }), 401)

        # 토큰으로 사용자 확인
        access_history = AccessHistory.query.filter_by(token=token).first()
        if not access_history:
            return make_response(jsonify({
                'status': False,
                'reason': 'invalid_token',
                'message': '유효하지 않은 인증 정보입니다.'
            }), 401)

        # 기존 코드는 그대로 유지
        user = db.session.query(Users).filter(Users.username == username).first()
        
        if user is None:
            return make_response(jsonify({
                'status': False,
                'reason': 'user_not_found',
                'message': '사용자를 찾을 수 없습니다.'
            }), 404)
            
        # 사용자의 그룹 정보 조회 - 기존 쿼리 패턴 활용
        user_group = db.session.query(Groups)\
            .filter(Groups.id == UsersGroups.FK_gid)\
            .filter(UsersGroups.FK_uid == user.id)\
            .first()
            
        # 사용자의 밴드 목록 조회 - 기존 쿼리 패턴 활용
        bands = db.session.query(Bands)\
            .filter(Bands.id == UsersBands.FK_bid)\
            .filter(UsersBands.FK_uid == user.id)\
            .all()
            
        # 응답 데이터 구조화
        user_data = user.serialize()
        user_data.update({
            'email': user.email,
            'phone': user.phone,
            'age': user.age,
            'gender': 'M' if user.gender == 1 else 'F',
            'created': user.created.strftime("%Y-%m-%d %H:%M:%S") if user.created else None,
            'last_login_time': user.last_login_time.strftime("%Y-%m-%d %H:%M:%S") if user.last_login_time else None,
            'group': user_group.serialize() if user_group else None
        })
        
            
        return make_response(jsonify({
            'status': True,
            'data': user_data
        }), 200)
        
    except Exception as e:
        print(f"Error in get_user_detail_by_username: {str(e)}")
        return make_response(jsonify({
            'status': False,
            'reason': 'server_error',
            'message': str(e)
        }), 500)


@app.route('/api/efwb/v1/users/<int:user_id>', methods=['GET'])
@token_required
def get_user_detail_by_id(user_id):
    """사용자 상세 정보 조회 API (user_id 기준)"""
    try:
        user = Users.query.get(user_id)
        if not user:
            return make_response(jsonify({
                'status': False,
                'reason': 'user_not_found',
                'message': '사용자를 찾을 수 없습니다.'
            }), 404)
            
        # 사용자의 그룹 정보 조회
        user_group = db.session.query(Groups).\
            join(UsersGroups, Groups.id == UsersGroups.FK_gid).\
            filter(UsersGroups.FK_uid == user_id).first()
            
        # 응답 데이터 구조화
        user_data = user.serialize()
        user_data.update({
            'email': user.email,
            'phone': user.phone,
            'age': user.age,
            'gender': 'M' if user.gender == 1 else 'F',
            'created': user.created.strftime("%Y-%m-%d %H:%M:%S") if user.created else None,
            'last_login_time': user.last_login_time.strftime("%Y-%m-%d %H:%M:%S") if user.last_login_time else None,
            'group': user_group.serialize() if user_group else None
        })
            
        # 사용자의 밴드 목록 조회
        bands = db.session.query(Bands).\
            join(UsersBands, Bands.id == UsersBands.FK_bid).\
            filter(UsersBands.FK_uid == user_id).all()
            
        band_list = []
        for idx, band in enumerate(bands, 1):
            band_data = band.serialize()
            band_data['num'] = idx  # 번호 추가
            band_list.append(band_data)
            
        user_data['bands'] = band_list
            
        return make_response(jsonify({
            'status': True,
            'data': user_data
        }), 200)
        
    except Exception as e:
        print(f"Error in get_user_detail_by_id: {str(e)}")  # 디버깅을 위한 로그
        return make_response(jsonify({
            'status': False,
            'reason': 'server_error',
            'message': str(e)
        }), 500)


@app.route('/api/efwb/v1/users/<int:user_id>', methods=['PUT'])
@token_required
def update_user(user_id):
    """사용자 정보 수정 API"""
    data = json.loads(request.data)
    
    try:
        user = Users.query.get(user_id)
        if not user:
            return make_response(jsonify({
                'status': False,
                'reason': 'user_not_found',
                'message': 'User not found.'
            }), 404)

        # 수정 가능한 필드들
        if 'name' in data:
            user.name = data['name']
        if 'email' in data:
            # 이메일 중복 체크
            existing_email = Users.query.filter(Users.email == data['email'], Users.id != user_id).first()
            if existing_email:
                return make_response(jsonify({
                    'status': False,
                    'reason': 'duplicate_email',
                    'message': 'Email already exists.'
                }), 400)
            user.email = data['email']
        if 'phone' in data:
            user.phone = data['phone']
        if 'age' in data:
            user.age = int(data['age'])
        if 'gender' in data:
            user.gender = 1 if data['gender'] == 'M' else 2

        db.session.commit()
        
        return make_response(jsonify({
            'status': True,
            'message': 'User information updated successfully.'
        }), 200)
        
    except Exception as e:
        db.session.rollback()
        return make_response(jsonify({
            'status': False,
            'reason': 'server_error',
            'message': str(e)
        }), 500)


@app.route('/api/efwb/v1/users/groupinfo/<id>', methods=['GET'])
@token_required
def user_groupinfo_api(id):
    dev = db.session.query(Groups).filter(
        UsersGroups.FK_gid == Groups.id).filter(UsersGroups.FK_uid == id).all()
    grouplist = []
    if dev is None:
        return make_response(jsonify('User is not Found.'), 404)

    for g in dev:
        grouplist.append(g.serialize())

    result = {
        "result": "OK",
        "data": grouplist
    }
    return make_response(jsonify(result), 200)


@app.route('/api/efwb/v1/users/samegroup/bands/<id>', methods=['GET'])
def get_user_samegroup_band_api(id):
    bidList = []
    dev = db.session.query(UsersGroups.FK_gid).filter(
        UsersGroups.FK_uid == id).first()
    if dev is None:
        return make_response(jsonify('User is not Found.'), 404)
    dev = db.session.query(Bands).\
        filter(Bands.id == UsersBands.FK_bid).\
        filter(UsersBands.FK_uid == UsersGroups.FK_uid).\
        filter(UsersGroups.FK_gid == dev.FK_gid).all()

    for g in dev:
        bidList.append(g.serialize())

    result = {
        "result": "OK",
        "data": bidList
    }
    return make_response(jsonify(result), 200)


def users_group_api(id):
    dev = db.session.query(UsersGroups.FK_gid).filter_by(FK_uid=id).first()
    if dev is None:
        return None
    return dev


@app.route('/api/efwb/v1/users/samegroup/<id>', methods=['GET'])
def users_samegroup_get_api(id):
    dev = []
    gid = users_group_api(id.split('_')[0])
    if gid is None:
        return make_response(jsonify('User is not Found.'), 404)
    if int(id.split('_')[1]) == 0:
        dev = Users.query.all()
    else:
        dev = db.session.query(Users).\
            filter(Users.id == UsersGroups.FK_uid).\
            filter(UsersGroups.FK_gid == gid.FK_gid).all()

    if dev is None:
        return make_response(jsonify('User is not Found.'), 404)
    userlist = []
    for u in dev:
        userlist.append(u.serialize())

    result = {
        "result": "OK",
        "data": {
            "userlist": userlist,
            "gid": gid.FK_gid if gid else None
        }
    }
    return make_response(jsonify(result), 200)


# @app.route('/api/efwb/v1/users/gatewayinfo/<id>', methods=['GET'])
# @token_required
# def user_gatewayinfo_api(id):
#     dev = db.session.query(Gateways).filter(
#         UsersGateways.FK_pid == Gateways.id).filter(UsersGateways.FK_uid == id).all()
#     gatewaylist = []
#     if dev is None:
#         return make_response(jsonify('User is not Found.'), 404)

#     for b in dev:
#         gatewaylist.append(b.serialize())

#     result = {
#         "result": "OK",
#         "data": gatewaylist
#     }
#     return make_response(jsonify(result), 200)


# @app.route('/api/efwb/v1/gateways/bandinfo/<id>', methods=['GET'])
# @token_required
# def gateway_bandinfo_api(id):
#     dev = db.session.query(Bands).\
#         filter(GatewaysBands.FK_bid == Bands.id).\
#         filter(GatewaysBands.FK_pid == id).all()
#     bandlist = []
#     if dev is None:
#         return make_response(jsonify('User is not Found.'), 404)

#     for b in dev:
#         bandlist.append(b.serialize())

#     result = {
#         "result": "OK",
#         "data": bandlist
#     }
#     return make_response(jsonify(result), 200)


# @app.route('/api/efwb/v1/gatewaysbands/num/<id>', methods=['GET'])
# def gatewaysbands_num_get_api(id):
#     dev = db.session.query(GatewaysBands).\
#         filter(GatewaysBands.FK_pid == id).first()
#     dev = db.session.query(func.count(GatewaysBands.id).label('num')).\
#         filter(GatewaysBands.FK_pid == id).first()

#     if dev is None:
#         return make_response(jsonify('User is not Found.'), 404)

#     result = {
#         "result": "OK",
#         "data": int(dev.num)
#     }
#     return make_response(jsonify(result), 200)


@app.route('/api/efwb/v1/bands/permission', methods=['POST'])
def check_band_permission_user():
    data = json.loads(request.data)
    params = ['uid', 'bid', 'permission']
    for param in params:
        if param not in data:
            return make_response(jsonify('Parameters are not enough.'), 400)
    dev = []
    if data['permission'] == 0:
        dev = db.session.query(Bands).filter(Bands.bid == data['bid']).first()
    else:

        if data['permission'] == 1:
            group = selectSameGroupOfUser(data['uid'])
            if group is None:
                return make_response(jsonify('Group is not Found.'), 404)

            dev = db.session.query(Bands).\
                filter(Bands.bid == data['bid']).\
                filter(Bands.id == UsersBands.FK_bid).\
                filter(UsersBands.FK_uid == UsersGroups.FK_uid).\
                filter(UsersGroups.FK_gid == group.id).first()

        elif data['permission'] == 2:
            group = selectSameGroupOfUser(data['uid'])
            if group is None:
                return make_response(jsonify('Group is not Found.'), 404)

            dev = db.session.query(Bands).\
                filter(Bands.bid == data['bid']).\
                filter(Bands.id == UsersBands.FK_bid).\
                filter(UsersBands.FK_uid == UsersGroups.FK_uid).\
                filter(UsersGroups.FK_gid == group.id).first()

        elif data['permission'] == 3:
            group = selectSameGroupOfUser(data['uid'])
            if group is None:
                return make_response(jsonify('Group is not Found.'), 404)

            dev = db.session.query(Bands).\
                filter(Bands.bid == data['bid']).\
                filter(Bands.id == UsersBands.FK_bid).\
                filter(UsersBands.FK_uid == UsersGroups.FK_uid).\
                filter(UsersGroups.FK_gid == group.id).first()

    if dev is None:
        result = {
            "result": "OK",
            "data": dev
        }
    else:
        result = {
            "result": "OK",
            "data": dev.serialize()
        }
    return make_response(jsonify(result), 200)


@app.route('/api/efwb/v1/users/bandlist', methods=['POST'])
def get_users_bandlist():
    data = json.loads(request.data)
    params = ['uid', 'permission']
    for param in params:
        if param not in data:
            return make_response(jsonify('Parameters are not enough.'), 400)
    dev = []
    bandList = []

    if data['permission'] == 0:
        dev = db.session.query(Bands).all()
    else:

        if data['permission'] == 1:
            group = selectSameGroupOfUser(data['uid'])
            if group is None:
                return make_response(jsonify('Group is not Found.'), 404)

            dev = db.session.query(Bands).\
                filter(Bands.id == UsersBands.FK_bid).\
                filter(UsersBands.FK_uid == UsersGroups.FK_uid).\
                filter(UsersGroups.FK_gid == group.id).all()

        elif data['permission'] == 2:
            dev = db.session.query(Bands).\
                filter(Bands.id == UsersBands.FK_bid).\
                filter(UsersBands.FK_uid == data['uid']).all()

        elif data['permission'] == 3:
            dev = db.session.query(Bands).\
                filter(Bands.id == UsersBands.FK_bid).\
                filter(UsersBands.FK_uid == data['uid']).all()
    for b in dev:
        bandList.append(b.serialize())

    result = {
        "result": "OK",
        "data": bandList
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
    for b in dev:
        bandlist.append(b.serialize())
    result = {
        "result": "OK",
        "data": bandlist
    }
    return make_response(jsonify(result), 200)


@app.route('/api/efwb/v1/bands/add', methods=['POST'])
@token_required
def band_post_api():
    data = json.loads(request.data)

    params = ['bid', 'alias', 'name', 'gender', 'birth']

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

    params = ['id', 'bid', 'alias', 'name', 'gender',
              'birth', 'disconnect_time', 'connect_time']

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
            "connect_time": data['connect_time']

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


# @app.route('/api/efwb/v1/bands/gatewayinfo/<id>', methods=['GET'])
# @token_required
# def band_gatewayinfo_api(id):
#     dev = db.session.query(Gateways).\
#         filter(Gateways.id == GatewaysBands.FK_pid).\
#         filter(GatewaysBands.FK_bid == id).all()
#     gatewaylist = []
#     if dev is None:
#         return make_response(jsonify('User is not Found.'), 404)
#     for u in dev:
#         gatewaylist.append(u.serialize())
#     result = {
#         "result": "OK",
#         "data": gatewaylist
#     }
#     return make_response(jsonify(result), 200)


# @app.route('/api/efwb/v1/bands/userinfo/<id>', methods=['GET'])
# @token_required
# def band_userinfo_api(id):
#     dev = db.session.query(Users).\
#         filter(Users.id == UsersGateways.FK_uid).\
#         filter(UsersGateways.FK_pid == GatewaysBands.FK_pid).\
#         filter(GatewaysBands.FK_bid == id).all()
#     userlist = []
#     if dev is None:
#         return make_response(jsonify('User is not Found.'), 404)
#     for u in dev:
#         userlist.append(u.serialize())
#     result = {
#         "result": "OK",
#         "data": userlist
#     }
#     return make_response(jsonify(result), 200)


@app.route('/api/efwb/v1/usersgroups/add', methods=['POST'])
@token_required
def users_groups_post_api():
    data = json.loads(request.data)

    params = ['uids', 'gids']

    for param in params:
        if param not in data:
            return make_response(jsonify('Parameters are not enough.'), 400)

    if len(data['uids']) > len(data['gids']):
        users_groups = addDBList(
            UsersGroups(), data['gids'], data['uids'], True, True)

    elif len(data['uids']) < len(data['gids']):

        users_groups = addDBList(
            UsersGroups(), data['uids'], data['gids'], False, True)

    else:
        users_groups = addDBList(
            UsersGroups(), data['gids'], data['uids'], True, True)
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

    if params[0] in data:
        dev = UsersGroups.query.filter(UsersGroups.FK_gid == data['gid']).all()
        if dev is None:
            return make_response(jsonify('UsersGroups is not found.'), 404)
        for ug in dev:
            users_groups_list.append(ug.serialize())

    elif params[1] in data:
        dev = UsersGroups.query.filter(UsersGroups.FK_uid == data['uid']).all()
        if dev is None:
            return make_response(jsonify('UsersGroups is not found.'), 404)
        for ug in dev:
            users_groups_list.append(ug.serialize())

    else:
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
            band = UsersGroups.query.filter(
                UsersGroups.FK_uid == uid).filter(UsersGroups.FK_gid == gid)
            if band.all():
                flag = True
                band.delete()

    if flag == False:
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

    params = ['uids', 'bids']

    for param in params:
        if param not in data:
            return make_response(jsonify('Parameters are not enough.'), 400)

    if len(data['uids']) > len(data['bids']):
        users_table = addDBList(
            UsersBands, data['bids'], data['uids'], True, False)

    elif len(data['uids']) < len(data['bids']):
        users_table = addDBList(
            UsersBands, data['uids'], data['bids'], False, False)

    else:
        users_table = addDBList(
            UsersBands, data['bids'], data['uids'], True, False)

    db.session.add(users_table)
    db.session.commit()
    db.session.flush()
    result = {
        "result": "OK"
    }

    return make_response(jsonify(result), 200)


# @app.route('/api/efwb/v1/usersgateways/detail', methods=['POST'])
# @token_required
# def users_bands_detail_get_api():
#     data = json.loads(request.data)
#     users_gateways_list = []
#     params = ['pid', 'uid']

#     if params[0] in data:
#         dev = UsersGateways.query.filter(
#             UsersGateways.FK_pid == data['pid']).all()
#         if dev is None:
#             return make_response(jsonify('UsersGateways is not found.'), 404)
#         for ub in dev:
#             users_gateways_list.append(ub.serialize())

#     elif params[1] in data:
#         dev = UsersGateways.query.filter(
#             UsersGateways.FK_uid == data['uid']).all()
#         if dev is None:
#             return make_response(jsonify('UsersGateways is not found.'), 404)
#         for ub in dev:
#             users_gateways_list.append(ub.serialize())

#     else:
#         return make_response(jsonify('Parameters are not enough.'), 400)

#     result = {
#         "result": "OK",
#         "users_gateways": users_gateways_list
#     }

#     return make_response(jsonify(result), 200)


# @app.route('/api/efwb/v1/usersgateways/list', methods=['GET'])
# @token_required
# def users_bands_list_get_api():
#     users_gateways = UsersGateways.query.all()
#     users_gateways_list = []
#     for ub in users_gateways:
#         users_gateways_list.append(ub.serialize())
#     result = {
#         "result": "OK",
#         "users": users_gateways_list
#     }

#     return make_response(jsonify(result), 200)


# @app.route('/api/efwb/v1/users/gwlist', methods=['POST'])
# def get_users_gwlist():
#     data = json.loads(request.data)
#     params = ['uid', 'permission']
#     for param in params:
#         if param not in data:
#             return make_response(jsonify('Parameters are not enough.'), 400)

#     dev = []
#     gwList = []
#     if data['permission'] == 0:
#         dev = db.session.query(Gateways).all()

#     else:
#         if data['permission'] == 1:
#             group = selectSameGroupOfUser(data['uid'])
#             if group is None:
#                 return make_response(jsonify('Group is not Found.'), 404)
#             dev = db.session.query(Gateways).distinct(Gateways.id).\
#                 filter(Gateways.id == GatewaysBands.FK_pid).\
#                 filter(GatewaysBands.FK_bid == UsersBands.FK_bid).\
#                 filter(UsersBands.FK_uid == UsersGroups.FK_uid).\
#                 filter(UsersGroups.FK_gid == group.id).all()

#         elif data['permission'] == 2:
#             dev = db.session.query(Gateways).distinct(Gateways.id).\
#                 filter(Gateways.id == GatewaysBands.FK_pid).\
#                 filter(GatewaysBands.FK_bid == UsersBands.FK_bid).\
#                 filter(UsersBands.FK_uid == data['uid']).all()

#         elif data['permission'] == 3:
#             dev = db.session.query(Gateways).distinct(Gateways.id).\
#                 filter(Gateways.id == GatewaysBands.FK_pid).\
#                 filter(GatewaysBands.FK_bid == UsersBands.FK_bid).\
#                 filter(UsersBands.FK_uid == data['uid']).all()
#     for b in dev:
#         gwList.append(b.serialize())
#     result = {
#         "result": "OK",
#         "data": gwList
#     }
#     return make_response(jsonify(result), 200)


# @app.route('/api/efwb/v1/usersgateways/check', methods=['POST'])
# def users_gateways_check_api():
#     data = json.loads(request.data)
#     params = ['uid', 'pid', 'permission']
#     gateways = None
#     for param in params:
#         if param not in data:
#             return make_response(jsonify('Parameters are not enough.'), 400)

#     if data['permission'] == 1:
#         group = selectSameGroupOfUser(data['uid'])
#         gateways = db.session.query(Gateways.pid).distinct(Gateways.id).\
#             filter(Gateways.pid == data['pid']).\
#             filter(Gateways.id == GatewaysBands.FK_pid).\
#             filter(GatewaysBands.FK_bid == UsersBands.FK_bid).\
#             filter(UsersBands.FK_uid == UsersGroups.FK_uid).\
#             filter(UsersGroups.FK_gid == group.id).first()

#     elif data['permission'] == 2:
#         gateways = db.session.query(Gateways.pid).distinct(Gateways.id).\
#             filter(Gateways.pid == data['pid']).\
#             filter(Gateways.id == GatewaysBands.FK_pid).\
#             filter(GatewaysBands.FK_bid == UsersBands.FK_bid).\
#             filter(UsersBands.FK_uid == data['uid']).first()

#     return make_response(jsonify({"data": gateways}), 200)


# @app.route('/api/efwb/v1/usersgateways/delete', methods=['DELETE'])
# @token_required
# def users_bands_delete_api():
#     data = json.loads(request.data)

#     params = ['uids', 'pids']
#     flag = False
#     for param in params:
#         if param not in data:
#             return make_response(jsonify('Parameters are not enough.'), 400)
#     for uid in data['uids']:
#         for pid in data['pids']:
#             usersgateways = UsersGateways.query.filter(
#                 UsersGateways.FK_uid == uid).filter(UsersGateways.FK_pid == pid)
#             if usersgateways.all():
#                 flag = True
#                 usersgateways.delete()

#     if flag == False:
#         return make_response(jsonify('UsersGateways is not found.'), 404)
#     db.session.commit()
#     db.session.flush()
#     result = {
#         "result": "OK",
#     }

#     return make_response(jsonify(result), 200)


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


@app.route('/api/efwb/v1/sensordata/oneday', methods=['POST'])
def sensordata_oneday_get_api():
    data = json.loads(request.data)
    params = ['bid', 'date']
    for param in params:
        if param not in data:
            return make_response(jsonify('Parameters are not enough.'), 400)

    # day = ['월', '화', '수', '목', '금', '토', '일']
    sensordata_list = None
    # dayValue = ""
    # dateValue = ""
    valuedata = db.session.query(func.avg(SensorData.hr).label('hr'),
                                 func.avg(SensorData.spo2).label('spo2'),
                                 (func.max(SensorData.walk_steps) -
                                  func.min(SensorData.walk_steps)).label('walk_steps'),
                                 (func.max(SensorData.run_steps) -
                                  func.min(SensorData.run_steps)).label('run_steps'),
                                 func.date_format(SensorData.datetime, '%H').
                                 label('x')).filter(SensorData.FK_bid == data['bid']).\
        filter(func.date(SensorData.datetime) == data['date'][0]).\
        group_by(func.hour(SensorData.datetime)).all()
    #valuedata = db.session.query(getAttribute(data['dataname'], SensorData).label('y'), SensorData.datetime.label('x')).filter(SensorData.FK_bid == data['bid']).filter(func.date(SensorData.datetime) == i).all()
    if valuedata:
        sensordata_list = [[], [], [], []]
        # dayValue = date(int(data['date'][0][0:4]), int(data['date'][0][5:7]), int(data['date'][0][8:10])).weekday()
        # dateValue =data['date'][0][5:7]+"월 "+data['date'][0][8:10]+"일 "+day[dayValue]
    for b in valuedata:
        sensordata_list[0].append({"x": b.x, "y": float(b.hr)})
        sensordata_list[1].append({"x": b.x, "y": float(b.spo2/10)})
        sensordata_list[2].append({"x": b.x, "y": int(b.walk_steps)})
        sensordata_list[3].append({"x": b.x, "y": int(b.run_steps)})

    result = {
        "result": "OK",
        "data": sensordata_list
    }
    return make_response(jsonify(result), 200)


@app.route('/api/efwb/v1/sensordata/activity/dashboard', methods=['GET'])
def dashboard_activity_get_api():
    json_data = []
    walk_dev = db.session.query((SensorData.FK_bid).label("bid"), (func.max(SensorData.walk_steps).label("walk"))).\
        filter(func.date(SensorData.datetime) == "2022-04-15").\
        group_by(SensorData.FK_bid).all()
    activity_dev = db.session.query((SensorData.FK_bid).label("bid"), func.ifnull(((func.count(SensorData.activity))*2/60), 0).label("activity")).\
        filter(func.date(SensorData.datetime) == "2022-04-15").filter(SensorData.activity > 0).\
        group_by(SensorData.FK_bid).all()
    list = [[], [], []]
    for d in range(len(walk_dev)):
        list[0].append(walk_dev[d].bid)
        list[1].append(int(walk_dev[d].walk))
        list[2].append(int(activity_dev[d].activity))

    result = {
        "result": "OK",
        "data": {"bid": list[0], "walk": list[1], "activity": list[2]}
    }
    print(result)
    return make_response(jsonify(result), 200)


@app.route('/api/efwb/v1/sensordata/range', methods=['POST'])
def sensordata_range_get_api():
    data = json.loads(request.data)
    params = ['bid', 'days', 'dataname']
    for param in params:
        if param not in data:
            return make_response(jsonify('Parameters are not enough.'), 400)

    day = ['월', '화', '수', '목', '금', '토', '일']
    if data['dataname'] == 'walk_steps':
        json_data = []
        valuedata = db.session.query((func.max(SensorData.walk_steps)-func.min(SensorData.walk_steps)).label('walk_steps'),
                                     (func.max(SensorData.run_steps) -
                                      func.min(SensorData.run_steps)).label('run_steps'),
                                     func.date_format(SensorData.datetime, '%Y-%m-%d %H').label('x')).\
            filter(SensorData.FK_bid == data['bid']).\
            filter(func.date(SensorData.datetime).between(data['days'][0], datetimeBetween(data['days']))).\
            group_by(func.date_format(SensorData.datetime, '%Y-%m-%d %H')).all()
        #valuedata = db.session.query(getAttribute(data['dataname'], SensorData).label('y'), SensorData.datetime.label('x')).filter(SensorData.FK_bid == data['bid']).filter(func.date(SensorData.datetime) == i).all()

        for d in data['days']:
            sensordata_list = [[], []]
            check = False
            for b in valuedata:
                if d == b.x[0:10]:
                    check = True
                    sensordata_list[0].append(
                        {"x": b.x[11:len(b.x)], "y": float(b.walk_steps)})
                    sensordata_list[1].append(
                        {"x": b.x[11:len(b.x)], "y": float(b.run_steps)})
            if(check):
                dayValue = date(int(d[0:4]), int(d[5:7]),
                                int(d[8:10])).weekday()
                dateValue = d[5:7]+"월 "+d[8:10]+"일 "+day[dayValue]
                json_data.append({"date": dateValue,  "data": sensordata_list})

        result = {
            "result": "OK",
            "data": json_data
        }
        return make_response(jsonify(result), 200)
    else:
        json_data = []
        valuedata = db.session.query(func.avg(getAttribute(data['dataname'], SensorData)).label('y'),
                                     func.date_format(SensorData.datetime, '%Y-%m-%d %H').
                                     label('x')).filter(SensorData.FK_bid == data['bid']).\
            filter(func.date(SensorData.datetime).between(data['days'][0], datetimeBetween(data['days']))).\
            group_by(func.date_format(SensorData.datetime, '%Y-%m-%d %H')).all()
        #valuedata = db.session.query(getAttribute(data['dataname'], SensorData).label('y'), SensorData.datetime.label('x')).filter(SensorData.FK_bid == data['bid']).filter(func.date(SensorData.datetime) == i).all()
        for d in data['days']:
            sensordata_list = []
            check = False
            for b in valuedata:
                if d == b.x[0:10]:
                    check = True
                    if data['dataname'] == 'spo2':
                        sensordata_list.append(
                            {"x":  b.x[11:len(b.x)], "y": float(b.y/10)})
                    else:
                        sensordata_list.append(
                            {"x":  b.x[11:len(b.x)], "y": float(b.y)})
            if(check):
                dayValue = date(int(d[0:4]), int(d[5:7]),
                                int(d[8:10])).weekday()
                dateValue = d[5:7]+"월 "+d[8:10]+"일 "+day[dayValue]
                json_data.append({"date": dateValue,  "data": sensordata_list})

        result = {
            "result": "OK",
            "data": json_data
        }
        return make_response(jsonify(result), 200)


def datetimeBetween(data):
    if len(data) == 1:
        return data[0]
    else:
        return data[len(data)-1]


# @app.route('/api/efwb/v1/sensordata/fall/sum', methods=['POST'])
# def sensordata_fall_sum_post_api():
#     data = json.loads(request.data)
#     params = ['bid', 'days']
#     for param in params:
#         if param not in data:
#             return make_response(jsonify('Parameters are not enough.'), 400)
#     json_data = []
#     dev = db.session.query(func.date_format(SensorData.datetime, "%Y-%m-%d").label('day'),
#                            func.sum(SensorData.fall_detect).label('fall_detect')).\
#         filter(SensorData.FK_bid == data['bid']).\
#         filter(func.date(SensorData.datetime).between(data['days'][0], datetimeBetween(data['days']))).\
#         group_by(func.date(SensorData.datetime)).all()
#     for i in dev:
#         json_data.append({
#             'day': i.day,
#             'fall_detect': int(i.fall_detect)
#         })
#     result = {
#         "result": "OK",
#         "data": json_data
#     }
#     return make_response(jsonify(result), 200)


@app.route('/api/efwb/v1/sensordata/activity/oneday', methods=['POST'])
def sensordata_activity_oneday_post_api():
    data = json.loads(request.data)
    params = ['bid', 'days']
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
            'day': i.day,
            'walk_steps': int(i.walk_steps),
            'run_steps': int(i.run_steps),
        })
    result = {
        "result": "OK",
        "data": json_data
    }
    return make_response(jsonify(result), 200)


@app.route('/api/efwb/v1/events', methods=["POST"])
def events_post_api():
    data = json.loads(request.data)
    params = ['bid', 'days', 'uid']

    for param in params:
        if param not in data:
            return make_response(jsonify('Parameters are not enough.'), 400)
            
    json_data = []
    dev = []
    
    # Events와 Bands 테이블을 조인하여 밴드 이름도 함께 조회
    if len(data['days']) == 0:  # 전체 이벤트에서
        if data['uid'] != -1:  
            dev = db.session.query(Events, Bands.name.label('band_name')).\
                join(Bands, Events.FK_bid == Bands.id).\
                filter(Events.FK_bid == UsersBands.FK_bid).\
                filter(UsersBands.FK_uid == data['uid']).all()

        elif data['bid'] != -1:  
            dev = db.session.query(Events, Bands.name.label('band_name')).\
                join(Bands, Events.FK_bid == Bands.id).\
                filter(Events.FK_bid == data['bid']).all()

        else:  
            dev = db.session.query(Events, Bands.name.label('band_name')).\
                join(Bands, Events.FK_bid == Bands.id).all()

    else:  # 정해진 날짜에서
        if data['uid'] != -1:  
            dev = db.session.query(Events, Bands.name.label('band_name')).\
                join(Bands, Events.FK_bid == Bands.id).\
                filter(Events.FK_bid == UsersBands.FK_bid).\
                filter(UsersBands.FK_uid == data['uid']).\
                filter(func.date(Events.datetime).between(data['days'][0], datetimeBetween(data['days']))).all()

        elif data['bid'] != -1:  
            dev = db.session.query(Events, Bands.name.label('band_name')).\
                join(Bands, Events.FK_bid == Bands.id).\
                filter(Events.FK_bid == data['bid']).\
                filter(func.date(Events.datetime).between(data['days'][0], datetimeBetween(data['days']))).all()

        else:  
            dev = db.session.query(Events, Bands.name.label('band_name')).\
                join(Bands, Events.FK_bid == Bands.id).\
                filter(func.date(Events.datetime).between(data['days'][0], datetimeBetween(data['days']))).all()

    for event, band_name in dev:
        event_data = event.serialize()
        event_data['band_name'] = band_name  # 밴드 이름 추가
        json_data.append(event_data)
        
    result = {
        "result": "OK",
        "data": json_data
    }

    return make_response(jsonify(result), 200)


@app.route('/api/efwb/v1/events/fall_detect/all', methods=["POST"])
def events_all_fall_post_api():
    data = json.loads(request.data)
    params = ['uid', 'date', 'format', 'permission']

    for param in params:
        if param not in data:
            return make_response(jsonify('Parameters are not enough.'), 400)
    json_data = []
    dev = []

    if data['permission'] == 0:
        dev = selectFallDetectDate(data['date'], data['format'])
    elif data['permission'] == 1:
        dev = selectFallDetectDateStaff(
            data['uid'], data['date'], data['format'])
    elif data['permission'] == 2:
        dev = selectFallDetectDateManager(
            data['uid'], data['date'], data['format'])
    elif data['permission'] == 3:
        dev = selectFallDetectDateUser(
            data['uid'], data['date'], data['format'])

    for d in dev:
        json_data.append({"x": d.day, "y": int(d.fall)})
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

    if len(data['days']) == 0:
        dev = db.session.query(func.date_format(Events.datetime, '%Y-%m-%d').label('date'),
                               func.sum(Events.value).label('data')).\
            distinct(Events.datetime).\
            filter(Events.FK_bid == data['bid']).\
            filter(Events.type == 0).\
            group_by(func.date(Events.datetime)).all()
    else:
        dev = db.session.query(func.date_format(Events.datetime, '%Y-%m-%d').label('date'),
                               func.sum(Events.value).label('data')).\
            distinct(Events.datetime).\
            filter(Events.FK_bid == data['bid']).\
            filter(Events.type == 0).\
            filter(func.date(Events.datetime).
                   between(data['days'][0], datetimeBetween(data['days']))).\
            group_by(func.date(Events.datetime)).all()

    for i in dev:
        json_data.append({"date": i.date, "data": int(i.data)})
    result = {
        "result": "OK",
        "data": json_data
    }

    return make_response(jsonify(result), 200)


# @app.route('/api/efwb/v1/gatewaylog/add', methods=["POST"])
# @token_required
# def gatewaylog_post_api():
#     data = json.loads(request.data)
#     params = ['pid', 'type']

#     for param in params:
#         if param not in data:
#             return make_response(jsonify('Parameters are not enough.'), 400)
#     gatewaylog = GatewayLog()
#     gatewaylog.FK_pid = data['pid']
#     gatewaylog.type = data['type']

#     db.session.add(gatewaylog)
#     db.session.commit()
#     db.session.flush()
#     result = {
#         "result": "OK"
#     }

#     return make_response(jsonify(result), 200)


@app.route('/api/efwb/v1/bandlog/add', methods=["POST"])
@token_required
def bandlog_post_api():
    data = json.loads(request.data)
    params = ['bid', 'type']

    for param in params:
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


@app.route('/api/efwb/v1/weather', methods=["GET"])
def get_weather_api():
    global work

    # 최대 20번 재시도 (0.5초 간격, 총 10초 대기)
    retry_count = 0
    while WeatherState.location is None and retry_count < 20:
        time.sleep(0.5)
        retry_count += 1

    # 20번 재시도 후에도 WeatherState.location이 None이면 서울시로 설정
    if WeatherState.location is None:
        WeatherState.location = "서울시"

    work = True
    try:
        result = get_weather(WeatherState.location, 36.10871500, 128.38469500)
        return make_response(jsonify(result), 200)
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)
    finally:
        work = False


# @app.route('/api/efwb/v1/nervestim/prescription', methods=["POST"])
# def post_prescription_api():
#     data = json.loads(request.data)
#     params = ['bid', 'frequency', 'strength', 'duration']

#     for param in params:
#         if param not in data:
#             return make_response(jsonify('Parameters are not enough.'), 400)

#     dev = db.session.query(NerveStimulations).\
#         filter(NerveStimulations.FK_bid == data["bid"]).first()
#     if dev is not None:
#         db.session.query(NerveStimulations).filter_by(FK_bid=data["bid"]).\
#             update(dict(status=0, frequency=data["frequency"],
#                    strength=data["strength"], duration=data["duration"]))
#         db.session.commit()

#     else:
#         nervestim = NerveStimulations()
#         nervestim.FK_bid = data["bid"]
#         nervestim.start_time = datetime.now()
#         nervestim.status = 0
#         nervestim.frequency = data["frequency"]
#         nervestim.strength = data["strength"]
#         nervestim.duration = data["duration"]

#         db.session.add(nervestim)
#         db.session.commit()
#     prescription_history = PrescriptionHistory()
#     prescription_history.FK_bid = data["bid"]
#     prescription_history.datetime = datetime.now()
#     prescription_history.frequency = data["frequency"]
#     prescription_history.strength = data["strength"]
#     prescription_history.duration = data["duration"]
#     db.session.add(prescription_history)
#     db.session.commit()
#     return make_response(jsonify({"result": "OK"}), 200)


# @app.route('/api/efwb/v1/nervestim', methods=["POST"])
# def post_nervestim_api():
#     data = json.loads(request.data)
#     params = ['bid', 'status', 'frequency', 'strength', 'duration']
#     for param in params:
#         if param not in data:
#             print(param)
#             return make_response(jsonify('Parameters are not enough.'), 400)
#     dev = db.session.query(NerveStimulations).\
#         filter(NerveStimulations.FK_bid == data["bid"]).first()
#     if dev is not None:
#         db.session.query(NerveStimulations).filter_by(FK_bid=data["bid"]).\
#             update(dict(status=data["status"], frequency=data["frequency"],
#                    strength=data["strength"], duration=data["duration"], start_time=datetime.now()))
#         db.session.commit()

#     else:
#         nervestim = NerveStimulations()
#         nervestim.FK_bid = data["bid"]
#         nervestim.start_time = datetime.now()
#         nervestim.status = data["status"]
#         nervestim.frequency = data["frequency"]
#         nervestim.strength = data["strength"]
#         nervestim.duration = data["duration"]

#         db.session.add(nervestim)
#         db.session.commit()

#     return make_response(jsonify({"result": "OK"}), 200)


# @app.route('/api/efwb/v1/nervestim/<bid>', methods=["GET"])
# def get_nervestim_bid_api(bid):
#     dev = db.session.query(NerveStimulations).\
#         filter(NerveStimulations.FK_bid == bid).first()
#     result = {
#         "result": "OK",
#         "data": None
#     }
#     if dev is not None:
#         result["data"] = dev.serialize()

#     return make_response(jsonify(result), 200)


# @app.route('/api/efwb/v1/nervestime_history/<bid>', methods=["GET"])
# def get_nervestime_history_bid_api(bid):
#     dev = db.session.query(PrescriptionHistory).\
#         filter(PrescriptionHistory.FK_bid == bid).all()
#     result = {
#         "result": "OK",
#         "data": None
#     }
#     if len(dev) != 0:
#         result["data"] = []
#         for d in dev:
#             result["data"].append(d.serialize())

#     return make_response(jsonify(result), 200)


def addDBList(table, list1, list2, lengthCheck, tableCheck):
    users_table = table
    for i in range(len(list2)):
        if lengthCheck:
            users_table.FK_uid = list2[i]
            if tableCheck:
                users_table.FK_gid = list1[0]
            else:
                users_table.FK_bid = list1[0]

        else:
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

    else:
        accesshistory = AccessHistory.query.filter_by(
            token=data['token']).first()
        if accesshistory is None:
            print("accesshistory in none")
        else:
            print("accesshistory exits")
            result = {'status': True, 'reason': 0,
                      'user': accesshistory.user.serialize()}
    return make_response(jsonify(result), 200)


def addDBUserBandList(db, list1, list2, check):
    for i in range(len(list2)):
        if check:
            users_bands = UsersBands()
            users_bands.FK_uid = list2[i]
            users_bands.FK_bid = list1[0]
            db.session.add(users_bands)
        else:
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


@app.route('/api/efwb/v1/connection-status', methods=['GET'])
def get_bands_connection_status():
    """
    모든 밴드의 연결 상태를 조회하는 API
    Returns:
        - bid
        - name
        - connect_state
        - connect_time
        - disconnect_time
    """
    try:
        bands = db.session.query(Bands).all()
        result = []
        
        for band in bands:
            band_status = {
                'bid': band.bid,
                'name': band.name,
                'connect_state': band.connect_state,
                'connect_time': band.connect_time.strftime("%Y-%m-%d %H:%M:%S") if band.connect_time else None,
                'disconnect_time': band.disconnect_time.strftime("%Y-%m-%d %H:%M:%S") if band.disconnect_time else None
            }
            result.append(band_status)
            
        return jsonify({
            'status': 'success',
            'data': result
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': '밴드 연결 상태 조회 중 오류가 발생했습니다.'
        }), 500

@app.route('/api/efwb/v1/connection-status/<bid>', methods=['GET'])
def get_band_connection_status(bid):
    """
    특정 밴드의 연결 상태를 조회하는 API
    Args:
        bid: 밴드 ID
    """
    try:
        band = db.session.query(Bands).filter_by(bid=bid).first()
        
        if not band:
            return jsonify({
                'status': 'error',
                'message': '해당 밴드를 찾을 수 없습니다.'
            }), 404
            
        band_status = {
            'bid': band.bid,
            'name': band.name,
            'connect_state': band.connect_state,
            'connect_time': band.connect_time.strftime("%Y-%m-%d %H:%M:%S") if band.connect_time else None,
            'disconnect_time': band.disconnect_time.strftime("%Y-%m-%d %H:%M:%S") if band.disconnect_time else None
        }
        
        return jsonify({
            'status': 'success',
            'data': band_status
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': '밴드 연결 상태 조회 중 오류가 발생했습니다.'
        }), 500 
        
@app.route('/api/efwb/v1/connected-locations', methods=['GET'])
def get_connected_band_locations():
    """현재 연결된 밴드들의 위치 정보를 조회"""
    app_logger.info("연결된 밴드들의 위치 정보 조회 시작")
    try:
        connected_bands = db.session.query(Bands).filter(
            Bands.connect_state == 1
        ).all()
        
        result = []
        for band in connected_bands:
            result.append({
                "id": band.id,
                "bid": band.bid,
                "latitude": float(band.latitude) if band.latitude else None,
                "longitude": float(band.longitude) if band.longitude else None,
                "name": band.name
            })
        app_logger.info(f"총 {len(result)}개의 연결된 밴드 위치 정보 조회 완료")
        return make_response(jsonify({
            'status': 'success',
            'data': result
        }), 200)
        
    except Exception as e:
        app_logger.error(f"연결된 밴드 위치 조회 중 에러 발생: {str(e)}")
        return make_response(jsonify({
            'status': 'error',
            'message': str(e)
        }), 500)

@app.route('/api/efwb/v1/signup', methods=['POST'])
def signup_api():
    """회원가입 API"""
    data = json.loads(request.data)
    
    try:
        # 필수 파라미터 체크
        required_params = ['username', 'password', 'name', 'phone', 'age', 'gender', 'email']
        for param in required_params:
            if param not in data:
                return make_response(jsonify({
                    'status': False,
                    'reason': 'missing_parameters',
                    'message': 'Parameters are not enough.'
                }), 400)

        # 아이디 중복 체크
        existing_user = Users.query.filter(Users.username == data['username']).first()
        if existing_user:
            return make_response(jsonify({
                'status': False,
                'reason': 'duplicate_username',
                'message': 'Username already exists.'
            }), 400)
            
        # 이메일 중복 체크 
        existing_email = Users.query.filter(Users.email == data['email']).first()
        if existing_email:
            return make_response(jsonify({
                'status': False,
                'reason': 'duplicate_email', 
                'message': 'Email already exists.'
            }), 400)

        # 새 사용자 생성
        new_user = Users()
        new_user.username = data['username']
        new_user.password = password_encoder_512(data['password'])
        new_user.name = data['name']
        new_user.phone = data['phone']
        new_user.age = int(data['age'])
        new_user.gender = 1 if data['gender'] == 'M' else 2
        new_user.email = data['email']
        new_user.permission = 2  # 일반 권한
        
        # uid는 현재 최대 uid + 1로 설정
        max_uid = db.session.query(func.max(Users.uid)).scalar()
        new_user.uid = (max_uid or 0) + 1

        # DB에 저장
        db.session.add(new_user)
        db.session.flush()  # new_user.id 값을 얻기 위해 flush
        
        # general 그룹 찾기 (gid=3000)
        general_group = Groups.query.filter_by(gid=3000).first()
        if not general_group:
            return make_response(jsonify({
                'status': False,
                'reason': 'group_not_found',
                'message': 'Default group (dtriple) not found.'
            }), 500)
        
        # UsersGroups 테이블에 연결 정보 추가
        user_group = UsersGroups()
        user_group.FK_uid = new_user.id
        user_group.FK_gid = general_group.id
        db.session.add(user_group)
        
        db.session.commit()

        return make_response(jsonify({
            'status': True,
            'message': 'User registered successfully and added to dtriple group.'
        }), 200)
        
    except Exception as e:
        db.session.rollback()
        return make_response(jsonify({
            'status': False,
            'reason': 'server_error',
            'message': str(e)
        }), 500)

@app.route('/api/efwb/v1/users/update-profile', methods=['PUT'])
@token_required
def update_user_profile():
    """사용자 프로필 정보 수정 API"""
    try:
        # 토큰 검증 및 사용자 확인
        token = request.headers.get('token')
        if not token:
            return make_response(jsonify({
                'status': False,
                'reason': 'unauthorized',
                'message': '인증 정보가 없습니다.'
            }), 401)

        access_history = AccessHistory.query.filter_by(token=token).first()
        if not access_history:
            return make_response(jsonify({
                'status': False,
                'reason': 'invalid_token',
                'message': '유효하지 않은 인증 정보입니다.'
            }), 401)

        data = json.loads(request.data)
        user = Users.query.get(access_history.FK_user_id)
        
        if not user:
            return make_response(jsonify({
                'status': False,
                'reason': 'user_not_found',
                'message': '사용자를 찾을 수 없습니다.'
            }), 404)

        # 수정 가능한 필드들 업데이트
        if 'name' in data:
            user.name = data['name']
        if 'email' in data:
            # 이메일 중복 체크
            existing_email = Users.query.filter(
                Users.email == data['email'], 
                Users.id != user.id
            ).first()
            if existing_email:
                return make_response(jsonify({
                    'status': False,
                    'reason': 'duplicate_email',
                    'message': '이미 사용 중인 이메일입니다.'
                }), 400)
            user.email = data['email']
        if 'phone' in data:
            user.phone = data['phone']
        if 'age' in data:
            user.age = int(data['age'])
        if 'gender' in data:
            user.gender = 1 if data['gender'].upper() == 'M' else 2
        if 'password' in data and data['password']:
            # 현재 비밀번호 확인
            if 'current_password' not in data:
                return make_response(jsonify({
                    'status': False,
                    'reason': 'missing_current_password',
                    'message': '현재 비밀번호를 입력해주세요.'
                }), 400)
                
            if user.password != password_encoder_512(data['current_password']):
                return make_response(jsonify({
                    'status': False,
                    'reason': 'invalid_password',
                    'message': '현재 비밀번호가 일치하지 않습니다.'
                }), 400)
                
            user.password = password_encoder_512(data['password'])

        db.session.commit()

        # 업데이트된 사용자 정보 반환
        updated_user = {
            'id': user.id,
            'username': user.username,
            'name': user.name,
            'email': user.email,
            'phone': user.phone,
            'age': user.age,
            'gender': 'M' if user.gender == 1 else 'F',
            'permission': user.permission,
            'last_login_time': user.last_login_time.strftime("%Y-%m-%d %H:%M:%S") if user.last_login_time else None
        }
        
        return make_response(jsonify({
            'status': True,
            'message': '프로필이 성공적으로 수정되었습니다.',
            'user': updated_user
        }), 200)
        
    except Exception as e:
        db.session.rollback()
        return make_response(jsonify({
            'status': False,
            'reason': 'server_error',
            'message': str(e)
        }), 500)
        
@app.route('/api/efwb/v1/users/<int:user_id>/bands', methods=['POST'])
@token_required
def match_band(user_id):
    """사용자와 밴드 매칭 API"""
    try:
        data = json.loads(request.data)
        
        # 필수 파라미터 체크
        required_params = ['name', 'bandId', 'alias']
        for param in required_params:
            if param not in data:
                return make_response(jsonify({
                    'status': False,
                    'message': 'Parameters are not enough.'
                }), 400)
                
        # 사용자 존재 확인
        user = Users.query.get(user_id)
        if not user:
            return make_response(jsonify({
                'status': False,
                'message': 'User not found.'
            }), 404)
            
        # 밴드 존재 확인
        band = Bands.query.filter_by(bid=data['bandId']).first()
        if not band:
            return make_response(jsonify({
                'status': False,
                'message': 'Band not found.'
            }), 404)
            
        # 이미 매칭된 밴드인지 확인
        existing_match = UsersBands.query.filter_by(
            FK_uid=user_id,
            FK_bid=band.id
        ).first()
        
        if existing_match:
            return make_response(jsonify({
                'status': False,
                'message': 'Band is already matched with this user.'
            }), 400)
            
        # 밴드 정보 업데이트
        band.name = data['name']
        band.alias = data['alias']
        
        # 사용자-밴드 매칭 생성
        new_match = UsersBands()
        new_match.FK_uid = user_id
        new_match.FK_bid = band.id
        
        db.session.add(new_match)
        db.session.commit()
        
        return make_response(jsonify({
            'status': True,
            'message': 'Band matched successfully.',
            'data': {
                'bandId': band.bid,
                'name': band.name,
                'alias': band.alias
            }
        }), 200)
        
    except Exception as e:
        db.session.rollback()
        return make_response(jsonify({
            'status': False,
            'message': str(e)
        }), 500)

@app.route('/api/efwb/v1/users/<int:user_id>/band-matching/<string:band_id>', methods=['DELETE'])
@token_required
def unmatch_band(user_id, band_id):
    """사용자와 밴드 매칭 해제 API"""
    try:
        # 사용자 존재 확인
        user = Users.query.get(user_id)
        if not user:
            return make_response(jsonify({
                'status': False,
                'message': 'User not found.'
            }), 404)
            
        # 밴드 존재 확인
        band = Bands.query.filter_by(bid=band_id).first()
        if not band:
            return make_response(jsonify({
                'status': False,
                'message': 'Band not found.'
            }), 404)
            
        # 매칭 정보 확인
        match = UsersBands.query.filter_by(
            FK_uid=user_id,
            FK_bid=band.id  # band.id는 Bands 테이블의 PK
        ).first()
        
        if not match:
            return make_response(jsonify({
                'status': False,
                'message': 'Band matching not found.'
            }), 404)
            
        # 매칭 관계만 삭제
        db.session.delete(match)
        db.session.commit()
        
        return make_response(jsonify({
            'status': True,
            'message': 'Band matching removed successfully.'
        }), 200)
        
    except Exception as e:
        db.session.rollback()
        return make_response(jsonify({
            'status': False,
            'message': str(e)
        }), 500)
        
@app.route('/api/efwb/v1/bands/sensor-data/<bid>', methods=['GET'])
@token_required
def get_band_sensor_data(bid):
    """특정 밴드의 최신 센서 데이터를 조회하는 API"""
    try:
        # 먼저 Band 테이블에서 bid로 band의 id를 조회
        band = db.session.query(Bands).filter(Bands.bid == bid).first()
        
        if not band:
            return make_response(jsonify({
                'status': False,
                'message': '밴드를 찾을 수 없습니다.',
                'data': {
                    'battery_level': '-',
                    # 'hrConfidence': '-',
                    # 'spo2Confidence': '-',
                    'hr': '-',
                    'spo2': '-',
                    'activity': '-',
                    'walk_steps': '-',
                    'run_steps': '-',
                    'latitude': None,
                    'longitude': None
                }
            }), 404)
            
        # band.id를 사용하여 최신 센서 데이터 조회
        latest_sensor_data = db.session.query(SensorData)\
            .filter(SensorData.FK_bid == band.id)\
            .order_by(SensorData.datetime.desc())\
            .first()
            
        if not latest_sensor_data:
            return make_response(jsonify({
                'status': False,
                'message': '센서 데이터가 없습니다.',
                'data': {
                    'battery_level': '-',
                    # 'hrConfidence': '-',
                    # 'spo2Confidence': '-',
                    'hr': '-',
                    'spo2': '-',
                    'activity': '-',
                    'walk_steps': '-',
                    'run_steps': '-',
                    'latitude': float(band.latitude) if band.latitude else None,
                    'longitude': float(band.longitude) if band.longitude else None
                }
            }), 404)
            
        # 응답 데이터 구성
        sensor_data = {
            'battery_level': latest_sensor_data.battery_level if latest_sensor_data.battery_level is not None else '-',
            # 'hrConfidence': latest_sensor_data.hrConfidence if latest_sensor_data.hrConfidence is not None else '-',
            # 'spo2Confidence': latest_sensor_data.spo2Confidence if latest_sensor_data.spo2Confidence is not None else '-',
            'hr': latest_sensor_data.hr if latest_sensor_data.hr is not None else '-',
            'spo2': latest_sensor_data.spo2 if latest_sensor_data.spo2 is not None else '-',
            'motionFlag': latest_sensor_data.motionFlag if latest_sensor_data.motionFlag is not None else '-',
            'scdState': latest_sensor_data.scdState if latest_sensor_data.scdState is not None else '-',
            'activity': latest_sensor_data.activity if latest_sensor_data.activity is not None else '-',
            'walk_steps': latest_sensor_data.walk_steps if latest_sensor_data.walk_steps is not None else '-',
            'run_steps': latest_sensor_data.run_steps if latest_sensor_data.run_steps is not None else '-',
            'latitude': float(band.latitude) if band.latitude else None,
            'longitude': float(band.longitude) if band.longitude else None,
        }
        
        return make_response(jsonify({
            'status': True,
            'message': '센서 데이터 조회 성공',
            'data': sensor_data
        }), 200)
        
    except Exception as e:
        app_logger.error(f"센서 데이터 조회 중 에러 발생: {str(e)}")
        return make_response(jsonify({
            'status': False,
            'message': '센서 데이터 조회 중 오류가 발생했습니다.',
            'error': str(e)
        }), 500)