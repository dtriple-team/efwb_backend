# -*- coding: utf-8 -*-
print ("module [backend_model.table_band.py] loaded")

from backend.db.database import DBManager
import datetime
from pytz import timezone
db = DBManager.db
class group_table(db.Model):
    __tablename__ = 'group_table'

    id = db.Column('id', db.Integer, primary_key=True)
    gid = db.Column('gid', db.Integer, comment='그룹아이디')
    groupname = db.Column('groupname', db.String(24), comment='그룹이름')
    permission = db.Column('permission', db.Integer, comment='권한')
    created = db.Column('created', db.DateTime, default=datetime.datetime.now, comment='생성시간')
    

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

class user_table(db.Model):
    __tablename__ = 'user_table'

    id = db.Column('id', db.Integer, primary_key=True)
    created = db.Column('created', db.DateTime, default=datetime.datetime.now, comment='생성시간')
    uid = db.Column('uid', db.Integer, comment='사용자 아이디(숫자값)')
    username = db.Column('username', db.String(48), comment='로그인 아이디')
    password = db.Column('password', db.String(256), comment='사용자 비밀번호')
    name = db.Column('name', db.String(48), comment='사용자 이름')

    age = db.Column('age', db.Integer, comment='사용자나이')
    gender = db.Column('gender', db.Integer, comment='성별(1:Male, 2:Female)')
    phone = db.Column('phone', db.String(30), comment='사용자 전화번호')
    email = db.Column('email', db.String(48), comment='사용자 이메일')
    token = db.Column('token', db.String(128), comment='사용자 토큰정보')
    last_logon_time = db.Column('last_logon_time', db.DateTime, comment='마지막 로그인 시간')


    def serialize(self):
        resultJSON = {
            # property (a)
            "id": self.id, 
            "uid": self.uid, 
            "username": self.username, 
            "name": self.name
        }
        return resultJSON

class UsersGroups(db.Model):
    __tablename__ = 'users_groups'

    id = db.Column('id', db.Integer, primary_key=True)
    FK_uid = db.Column('uid', db.Integer, db.ForeignKey(user_table.id))
    user = db.relationship('user_table')
    FK_gid = db.Column('gid', db.Integer, db.ForeignKey(group_table.id))    
    usergroup = db.relationship('group_table', backref='users_groups', cascade="delete")

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
    bid = db.Column('bid', db.Integer, comment='밴드 아이디')
    created = db.Column('created', db.DateTime, default=datetime.datetime.now(timezone('Asia/Seoul')), comment='생성시간')
    alias = db.Column('alias', db.String(48), comment='밴드 별명')
    name = db.Column('name', db.String(48), comment='착용자 이름')
    gender = db.Column('gender', db.Integer, comment='착용자 성별')
    birth = db.Column('birth', db.DateTime, comment='착용자 생년월일')

    def serialize(self):
        resultJSON = {
            # property (a)
            "id": self.id, 
            "bid": self.bid, 
            "created": self.created,
            "alias": self.alias,  
            "name": self.name, 
            "gender": self.gender,
            "birth": self.birth
        }
        return resultJSON 
class UsersBands(db.Model):
    __tablename__ = 'users_bands'

    id = db.Column('id', db.Integer, primary_key=True)
    FK_bid = db.Column('FK_bid', db.Integer, db.ForeignKey(Bands.id)) 
    band = db.relationship('Bands', cascade="all, delete")
    FK_uid = db.Column('FK_uid', db.Integer, db.ForeignKey(user_table.id)) 
    user = db.relationship('user_table', cascade="all, delete")

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
    datetime = db.Column('datetime', db.DateTime, default=datetime.datetime.now, comment='datetime')
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

            "x":self.x,
            "y":self.y,
            "z":self.z,
            "h":self.h,
            "t":self.t,
            "h":self.h,
            "rssi":self.rssi
        }
        return resultJSON 
   
class Activity(db.Model):
    __tablename__ = 'activity'

    id = db.Column('id', db.Integer, primary_key=True)
    datetime = db.Column('datetime', db.Integer, default=datetime.datetime.now, comment='datetime')
    FK_bid = db.Column('FK_bid', db.Integer, db.ForeignKey(Bands.id)) 
    band = db.relationship('Bands')


class BMP280(db.Model):
    __tablename__ = 'bmp280'

    id = db.Column('id', db.Integer, primary_key=True)
    datetime = db.Column('datetime', db.Integer, default=datetime.datetime.now, comment='datetime')
    FK_bid = db.Column('FK_bid', db.Integer, db.ForeignKey(Bands.id)) 
    band = db.relationship('Bands')

    pressure = db.Column('pressure', db.Float, comment='기압측정값')

class Events(db.Model):
    __tablename__ = 'events'

    id = db.Column('id', db.Integer, primary_key=True)
    datetime = db.Column('datetime', db.DateTime, default=datetime.datetime.now, comment='datetime')
    FK_bid = db.Column('FK_bid', db.Integer, db.ForeignKey(Bands.id)) 
    band = db.relationship('Bands')

    event = db.Column('event', db.Integer, comment='이벤트번호')
    value = db.Column('value', db.Integer, comment='이벤트값')    