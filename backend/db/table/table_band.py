# -*- coding: utf-8 -*-
print ("module [backend_model.table_band.py] loaded")

from backend.db.database import DBManager
import datetime
from pytz import timezone
db = DBManager.db
class Groups(db.Model):
    __tablename__ = 'groups'

    id = db.Column('id', db.Integer, primary_key=True)
    gid = db.Column('gid', db.Integer, comment='그룹아이디')
    groupname = db.Column('groupname', db.String(24), comment='그룹이름')
    permission = db.Column('permission', db.Integer, comment='권한')
    created = db.Column('created', db.DateTime, default=datetime.datetime.now(timezone('Asia/Seoul')), comment='생성시간')
    

    def serialize(self):
        resultJSON = {
            # property (a)
            "id": self.id, 
            "gid": self.gid, 
            "groupname": self.groupname, 
            "permission": self.permission, 
            "created": self.created
        }
        return resultJSON  

class Users(db.Model):
    __tablename__ = 'users'

    id = db.Column('id', db.Integer, primary_key=True)
    created = db.Column('created', db.DateTime, default=datetime.datetime.now(timezone('Asia/Seoul')), comment='생성시간')
    uid = db.Column('uid', db.Integer, comment='사용자 아이디(숫자값)')
    username = db.Column('username', db.String(48), comment='로그인 아이디')
    password = db.Column('password', db.String(256), comment='사용자 비밀번호')
    name = db.Column('name', db.String(48), comment='사용자 이름')
    permission = db.Column('permission', db.Integer, comment='권한')

    age = db.Column('age', db.Integer, comment='사용자나이')
    gender = db.Column('gender', db.Integer, comment='성별(1:Male, 2:Female)')
    phone = db.Column('phone', db.String(30), comment='사용자 전화번호')
    email = db.Column('email', db.String(48), comment='사용자 이메일')
    token = db.Column('token', db.String(128), comment='사용자 토큰정보')
    last_login_time = db.Column('last_logon_time', db.DateTime, comment='마지막 로그인 시간')


    def serialize(self):
        resultJSON = {
            # property (a)
            "id": self.id, 
            "uid": self.uid, 
            "username": self.username, 
            "name": self.name,
            "token": self.token,
            "permission": self.permission,
            "created": self.created,
            
        }
        return resultJSON
class AccessHistory(db.Model):
    __tablename__ = 'access_history'

    id = db.Column('id', db.Integer, primary_key=True)
    update_time = db.Column('update_time', db.DateTime, default=datetime.datetime.now(timezone('Asia/Seoul')), comment='생성시간')
    user_id = db.Column('user_id', db.String(48), comment='사용자ID')
    type = db.Column('type', db.Boolean, comment='0:로그인, 1:로그아웃')
    ip_addr = db.Column('ip_addr', db.String(20), comment='사용자 접속IP')
    os_ver = db.Column('os_ver', db.String(48), comment='사용자 접속 OS버전')
    browser_ver = db.Column('browser_ver', db.String(48), comment='사용자 접속 브라우저버전')
    token = db.Column('token', db.String(128), comment='사용자 토큰정보')
    FK_user_id = db.Column('FK_user_id', db.Integer, db.ForeignKey(Users.id, ondelete='CASCADE'))
    user = db.relationship('Users')
class Login(db.Model):
    __tablename__ = 'login'
    id = db.Column('id', db.Integer, primary_key=True)
    FK_ah_id = db.Column('FK_ah_id', db.Integer, db.ForeignKey(AccessHistory.id, ondelete='CASCADE'))
    ah = db.relationship('AccessHistory')
    datetime = db.Column('update_time', db.DateTime, default=datetime.datetime.now(timezone('Asia/Seoul')), comment='접속시간')
class TokenHistory(db.Model):
    __tablename__ = 'token_hisotry'
    id = db.Column('id', db.Integer, primary_key=True)
    token = db.Column('token', db.String(128), comment='사용자 토큰정보')
    FK_user_id = db.Column('FK_user_id', db.Integer, db.ForeignKey(Users.id, ondelete='CASCADE'))
    user = db.relationship('Users')
    
class UsersGroups(db.Model):
    __tablename__ = 'usersgroups'

    id = db.Column('id', db.Integer, primary_key=True)
    FK_uid = db.Column('FK_uid', db.Integer, db.ForeignKey(Users.id))
    user = db.relationship('Users')
    FK_gid = db.Column('FK_gid', db.Integer, db.ForeignKey(Groups.id , ondelete='CASCADE'))    
    group = db.relationship('Groups', backref='usersgroups')

    def serialize(self):
        resultJSON = {
            # property (a)
            "id": self.id, 
            "uid": self.FK_uid,
            "gid": self.FK_gid
        }
        return resultJSON 

class Bands(db.Model):
    __tablename__ = 'bands'

    id = db.Column('id', db.Integer, primary_key=True)
    bid = db.Column('bid', db.String(48), comment='밴드 아이디')
    created = db.Column('created', db.DateTime, default=datetime.datetime.now(timezone('Asia/Seoul')), comment='생성시간')
    alias = db.Column('alias', db.String(48), comment='밴드 별명')
    name = db.Column('name', db.String(48), comment='착용자 이름')
    gender = db.Column('gender', db.Integer, comment='착용자 성별')
    birth = db.Column('birth', db.DateTime, comment='착용자 생년월일')
    disconnect_time = db.Column('disconnect_time', db.DateTime,  comment='마지막 연결 종료 시간')
    connect_time = db.Column('connect_time', db.DateTime,   comment='마지막 연결 시간')
    connect_state = db.Column('connect_state', db.Integer, default = 0, comment='밴드 상태 0 : off, 1 : on')
    
    def serialize(self):
        resultJSON = {
            # property (a)
            "id": self.id, 
            "bid": self.bid, 
            "created": self.created,
            "alias": self.alias,  
            "name": self.name, 
            "gender": self.gender,
            "birth": self.birth,
            "disconnect_time": self.disconnect_time,
            "connect_time": self.connect_time,
            "connect_state": self.connect_state
        }
        return resultJSON 

class Gateways(db.Model):
    __tablename__ = 'gateways'
    id = db.Column('id', db.Integer, primary_key=True)
    pid = db.Column('pid', db.String(12), comment='게이트웨이 팬 아이디')
    alias = db.Column('alias', db.String(20), comment='게이트웨이 별칭')
    created = db.Column('created', db.DateTime, default=datetime.datetime.now(timezone('Asia/Seoul')), comment="생성 시간")
    ip = db.Column('ip', db.String(20), comment='아이피 주소')
    location = db.Column('location', db.String(12), comment='위치')
    airpressure = db.Column('airpressure', db.Float, comment="고도")
    disconnect_time = db.Column('disconnect_time', db.DateTime,  default=datetime.datetime.now(timezone('Asia/Seoul')), comment='마지막 연결 종료 시간')
    connect_time = db.Column('connect_time', db.DateTime,   default=datetime.datetime.now(timezone('Asia/Seoul')), comment='마지막 연결 시간')
    connect_check_time = db.Column('connect_check_time', db.DateTime,   default=datetime.datetime.now(timezone('Asia/Seoul')), comment='연결 체크 시간')
    connect_state = db.Column('connect_state', db.Integer,  default=0, comment='연결 상태' )
    thread_check_time = db.Column('thread_check_time', db.DateTime, default=datetime.datetime.now(timezone('Asia/Seoul')), comment='thread 체크 시간')
    def serialize(self):
        resultJSON = {
            # property (a)
            "id": self.id, 
            "pid": self.pid, 
            "alias": self.alias,
            "created": self.created,
            "ip":self.ip,
            "location": self.location,
            "airpressure": self.airpressure,
            "disconnect_time": self.disconnect_time,
            "connect_time": self.connect_time,
            "connect_state": self.connect_state,
            "thread_check_time": self.thread_check_time
        }
        return resultJSON 
class GatewayLog(db.Model):
    __tablename__ = 'gatewaylog'
    id = db.Column('id', db.Integer, primary_key=True)
    FK_pid = db.Column('FK_pid', db.Integer, db.ForeignKey(Gateways.id , ondelete='CASCADE'))
    gateway = db.relationship('Gateways')
    type = db.Column('type', db.Integer, comment="0 : disconnect 1 : ping connect 2 : server connect 3 : server disconect")
    datetime = db.Column('datetime', db.DateTime, default=datetime.datetime.now(timezone('Asia/Seoul')), comment='시간')
    def serialize(self):
        resultJSON = {
            "id": self.id,
            "pid": self.FK_pid,
            "gateway": self.gateway,
            "type": self.type,
            "datetime": self.datetime
        }
        return resultJSON
class BandLog(db.Model):
    __tablename__ = 'bandlog'
    id = db.Column('id', db.Integer, primary_key=True)
    FK_bid = db.Column('FK_bid', db.Integer, db.ForeignKey(Bands.id, ondelete='CASCADE'))
    band = db.relationship('Bands')
    type = db.Column('type', db.Integer, comment="1 : connect 2 : disconnect")
    datetime = db.Column('datetime', db.DateTime, default=datetime.datetime.now(timezone('Asia/Seoul')), comment='시간')
    def serialize(self):
        resultJSON = {
            "id": self.id,
            "pid": self.FK_bid,
            "gateway": self.band,
            "type": self.type,
            "datetime": self.datetime
        }
        return resultJSON
class UsersGateways(db.Model):
    __tablename__ = 'usersgateways'

    id = db.Column('id', db.Integer, primary_key=True)
    FK_uid = db.Column('FK_uid', db.Integer, db.ForeignKey(Users.id, ondelete='CASCADE')) 
    user = db.relationship('Users')
    FK_pid = db.Column('FK_pid', db.Integer, db.ForeignKey(Gateways.id , ondelete='CASCADE')) 
    gateway = db.relationship('Gateways')
    def serialize(self):
        resultJSON = {
            # property (a)
            "id": self.id, 
            "uid": self.FK_uid,
            "pid": self.FK_pid
        }
        return resultJSON 

class GatewaysBands(db.Model):
    __tablename__ = 'gatewaysbands'

    id = db.Column('id', db.Integer, primary_key=True)
    FK_pid = db.Column('FK_pid', db.Integer, db.ForeignKey(Gateways.id, ondelete='CASCADE')) 
    gateway = db.relationship('Gateways')
    FK_bid = db.Column('FK_bid', db.Integer, db.ForeignKey(Bands.id, ondelete='CASCADE')) 
    band = db.relationship('Bands')
    def serialize(self):
        resultJSON = {
            # property (a)
            "id": self.id, 
            "bid": self.FK_bid,
            "pid": self.FK_pid
        }
        return resultJSON

class UsersBands(db.Model):
    __tablename__ = 'users_bands'

    id = db.Column('id', db.Integer, primary_key=True)
    FK_uid = db.Column('FK_uid', db.Integer, db.ForeignKey(Users.id, ondelete='CASCADE')) 
    users = db.relationship('Users')
    FK_bid = db.Column('FK_bid', db.Integer, db.ForeignKey(Bands.id, ondelete='CASCADE')) 
    bands = db.relationship('Bands')
    def serialize(self):
        resultJSON = {
            # property (a)
            "id": self.id, 
            "uid": self.FK_uid,
            "bid": self.FK_bid
        }
        return resultJSON 
class SensorData(db.Model):
    __tablename__ = 'sensordata'

    id = db.Column('id', db.Integer, primary_key=True)
    datetime = db.Column('datetime', db.DateTime, default=datetime.datetime.now(timezone('Asia/Seoul')), comment='datetime')
    FK_bid = db.Column('FK_bid', db.Integer, db.ForeignKey(Bands.id)) 
    band = db.relationship('Bands')
    start_byte = db.Column('start_byte', db.Integer)
    sample_count = db.Column('sample_count', db.Integer)
    fall_detect = db.Column('fall_detect', db.Integer)
    battery_level = db.Column('battery_level', db.Integer)
    hrConfidence = db.Column('hrConfidence', db.Integer)
    spo2Confidence = db.Column('spo2Confidence', db.Integer)
    hr = db.Column('hr', db.Integer, comment='심박수')
    spo2 = db.Column('spo2', db.Integer, comment='산소포화도')
    #spo2state = db.Column('spo2state', db.Integer, comment='산소포화도 측정 상태')
    # spo2signal = db.Column('spo2signal', db.Boolean, comment='산소포화도 시그널 퀄리티')
    # spo2lowpi = db.Column('spo2lowpi', db.Boolean, comment='산소포화도 low pi')
    motionFlag = db.Column('motionFlag', db.Integer, comment='움직임 여부')
    scdState = db.Column('scdState', db.Integer, comment='착용 상태')
    activity = db.Column('activity', db.Integer, comment='활동상태')
    walk_steps = db.Column('walk_steps', db.Integer, comment='걷기')
    run_steps = db.Column('run_steps', db.Integer, comment='달리기')
    temp_walk_steps = db.Column('temp_walk_steps', db.Integer, default=0, comment='임시걷기')
    temp_run_steps = db.Column('temp_run_steps', db.Integer, default=0, comment='임시달리기')
    x = db.Column('x', db.Integer, comment='x')
    y = db.Column('y', db.Integer, comment='y')
    z = db.Column('z', db.Integer, comment='z')
    t = db.Column('t', db.Integer, comment='t')
    h = db.Column('h', db.Integer, comment='h')
    
    rssi = db.Column('rssi', db.Integer, comment='수신 감도')

    def serialize(self):
        resultJSON = {
            # property (a)
            "id": self.id, 
            "datetime": self.datetime,
            "bid": self.FK_bid,
            "start_byte": self.start_byte,
            "sample_count":self.sample_count,
            "fall_detect":self.fall_detect,
            "battery_level":self.battery_level,
            "hrConfidence":self.hrConfidence,
            "spo2Confidence":self.spo2Confidence,
            "hr": self.hr,
            "spo2":self.spo2,
            "motionFlag":self.motionFlag,
            "scdState":self.scdState,
            "activity":self.activity,
            "walk_steps":self.walk_steps,
            "run_steps":self.run_steps,
            "temp_walk_steps":self.walk_steps,
            "temp_run_steps":self.run_steps,
            "x":self.x,
            "y":self.y,
            "z":self.z,
            "h":self.h,
            "t":self.t,
            "h":self.h,
            "rssi":self.rssi
        }
        return resultJSON 
   
class WalkRunCount(db.Model):
    __tablename__ = 'walkruncount'

    id = db.Column('id', db.Integer, primary_key=True)
    datetime = db.Column('datetime', db.DateTime, default=datetime.datetime.now(timezone('Asia/Seoul')), comment='datetime')
    FK_bid = db.Column('FK_bid', db.Integer, db.ForeignKey(Bands.id)) 
    band = db.relationship('Bands')
    walk_steps = db.Column('walk_steps', db.Integer, comment='걷기')
    run_steps = db.Column('run_steps', db.Integer, comment='달리기')
    temp_walk_steps = db.Column('temp_walk_steps', db.Integer, default=0, comment='임시걷기')
    temp_run_steps = db.Column('temp_run_steps', db.Integer, default=0, comment='임시달리기')
    def serialize(self):
        resultJSON = {
            # property (a)
            "id": self.id, 
            "datetime": self.datetime,
            "bid": self.FK_bid,
            "walk_steps": self.walk_steps,
            "run_steps": self.run_steps,
            "temp_walk_steps": self.temp_walk_steps,
            "temp_run_steps": self.temp_run_steps,
        }
        return resultJSON 

class BMP280(db.Model):
    __tablename__ = 'bmp280'

    id = db.Column('id', db.Integer, primary_key=True)
    datetime = db.Column('datetime', db.Integer, default=datetime.datetime.now, comment='datetime')
    FK_bid = db.Column('FK_bid', db.Integer, db.ForeignKey(Bands.id)) 
    band = db.relationship('Bands')

    pressure = db.Column('pressure', db.Float, comment='기압측정값')
class Server(db.Model):
    __tablename__ = "server"
    id = db.Column('id', db.Integer, primary_key=True)
    start = db.Column('start', db.Integer, default=0)
class Events(db.Model):
    __tablename__ = 'events'

    id = db.Column('id', db.Integer, primary_key=True)
    datetime = db.Column('datetime', db.DateTime, default=datetime.datetime.now(timezone('Asia/Seoul')), comment='datetime')
    FK_bid = db.Column('FK_bid', db.Integer, db.ForeignKey(Bands.id)) 
    band = db.relationship('Bands')

    type = db.Column('type', db.Integer, comment='이벤트번호')
    value = db.Column('value', db.Integer, comment='이벤트값')    
    def serialize(self):
        resultJSON = {
            # property (a)
            "id": self.id, 
            "datetime": self.datetime,
            "bid": self.FK_bid,
            "bandid": self.band.bid,
            "type": self.type,
            "value": self.value,
        }
        return resultJSON 