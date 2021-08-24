#!/usr/bin/python
# -*- coding: utf-8 -*-
print ("module [backend_model.database] loaded")
from datetime import datetime, timedelta

from sqlalchemy.sql.expression import true
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
import random
import hashlib
from sqlalchemy import or_,and_
import os
import json
import uuid


from flask_sqlalchemy import SQLAlchemy


class DBManager:
    db = None

    @staticmethod
    def init(app):
        # print "-- DBManager init()"
        db = SQLAlchemy(app)
        DBManager.db = db

    @staticmethod
    def init_db():
        print("-- DBManager init_db()")
        db = DBManager.db
        db.drop_all()
        db.create_all()
        DBManager.insert_dummy_data()

    @staticmethod
    def clear_db():
        print("-- DBManager clear_db()")
        DBManager.db.drop_all()

    @staticmethod
    def insert_dummy_data():
        print ('insert_dummy_data')

        DBManager.insert_dummy_group_table()
        DBManager.insert_dummy_user_table()
        DBManager.insert_dummy_users_groups()
        DBManager.insert_dummy_bands()
        DBManager.insert_dummy_users_bands()
        #DBManager.insert_dummy_sensor_data()
        #DBManager.insert_dummy_event_data()
    def password_encoder(password):
        pass1 = hashlib.sha1(password).digest()
        pass2 = hashlib.sha1(pass1).hexdigest()
        hashed_pw = "*" + pass2.upper()
        return hashed_pw

    def get_random_date():
        end = datetime.utcnow()
        start = end + timedelta(days=-60)

        random_date = start + timedelta(
            # Get a random amount of seconds between `start` and `end`
            seconds=random.randint(0, int((end - start).total_seconds())),
        )

        return random_date

    def password_encoder_512(password):
        h = hashlib.sha512()
        h.update(password.encode('utf-8'))
        return h.hexdigest()

    def get_random_ip():
        ip_list = [u'28.23.43.1', u'40.12.33.11', u'100.123.234.11', u'61.34.22.44', u'56.34.56.77', u'123.234.222.55']

        return ip_list[random.randrange(0, 6)]

    def insert_dummy_user_table():
        print("insert_dummy_user_table")
        from backend.db.table_band import user_table

        user = user_table()
        user.uid = 1000
        user.username = "worud3310"
        user.password = DBManager.password_encoder_512("1234")
        user.name = "하재경"
        DBManager.db.session.add(user)
        DBManager.db.session.commit()

    def insert_dummy_group_table():
        print("insert_dummy_group_table")
        from backend.db.table_band import group_table

        group = group_table()
        group.gid = 1000
        group.groupname = "hello"
        group.permission = 0


        DBManager.db.session.add(group)

        group = group_table()
        group.gid = 2000
        group.groupname = "hello"
        group.permission = 0


        DBManager.db.session.add(group)
        DBManager.db.session.commit()

    def insert_dummy_users_groups():
        print("insert_dummy_users_groups")
        from backend.db.table_band import UsersGroups
        users_groups = UsersGroups()
        users_groups.FK_uid = 1
        users_groups.FK_gid = 1

        DBManager.db.session.add(users_groups)
        users_groups = UsersGroups()
        users_groups.FK_uid = 1
        users_groups.FK_gid = 2

        DBManager.db.session.add(users_groups)
        DBManager.db.session.commit()

    def insert_dummy_bands():
        print("insert_dummy_bands")
        from backend.db.table_band import Bands
        bands = Bands()
        bands.bid = 1
        bands.alias = "P1"
        bands.name = "하재경"
        bands.gender = 1
        bands.birth = "1997-09-01"
        
        DBManager.db.session.add(bands)

        bands = Bands()
        bands.bid = 2
        bands.alias = "P2"
        bands.name = "주강대"
        bands.gender = 0
        bands.birth = "1997-09-01"
        
        DBManager.db.session.add(bands)

        bands = Bands()
        bands.bid = 3
        bands.alias = "P3"
        bands.name = "박홍범"
        bands.gender = 0
        bands.birth = "1997-09-01"
        
        DBManager.db.session.add(bands)

        bands = Bands()
        bands.bid = 4
        bands.alias = "P4"
        bands.name = "홍준호"
        bands.gender = 0
        bands.birth = "1997-09-01"
        
        DBManager.db.session.add(bands)

        bands = Bands()
        bands.bid = 5
        bands.alias = "P5"
        bands.name = "강예린"
        bands.gender = 1
        bands.birth = "1997-09-01"
        
        DBManager.db.session.add(bands)

        bands = Bands()
        bands.bid = 6
        bands.alias = "P6"
        bands.name = "조우석"
        bands.gender = 0
        bands.birth = "1997-09-01"
        
        DBManager.db.session.add(bands)

        bands = Bands()
        bands.bid = 7
        bands.alias = "P7"
        bands.name = "신현식"
        bands.gender = 0
        bands.birth = "1997-09-01"
        
        DBManager.db.session.add(bands)

        bands = Bands()
        bands.bid = 8
        bands.alias = "P8"
        bands.name = "서주원"
        bands.gender = 0
        bands.birth = "1997-09-01"
        
        DBManager.db.session.add(bands)

        bands = Bands()
        bands.bid = 9
        bands.alias = "P9"
        bands.name = "라춘식"
        bands.gender = 0
        bands.birth = "1997-09-01"
        
        DBManager.db.session.add(bands)

        bands = Bands()
        bands.bid = 10
        bands.alias = "P10"
        bands.name = "라이언"
        bands.gender = 0
        bands.birth = "1997-09-01"
        
        DBManager.db.session.add(bands)
        DBManager.db.session.commit()

    def insert_dummy_users_bands():
        print("insert_dummy_users_bands")
        from backend.db.table_band import UsersBands
        users_bands = UsersBands()
        users_bands.FK_bid = 1
        users_bands.FK_uid = 1

        DBManager.db.session.add(users_bands)
        users_bands = UsersBands()
        users_bands.FK_bid = 2
        users_bands.FK_uid = 1

        DBManager.db.session.add(users_bands)
        DBManager.db.session.commit()

    def insert_dummy_sensor_data():
        print("insert_dummy_sensor_data")
        from backend.db.table_band import SensorData 
        data = SensorData()
        data.FK_bid = 1
        data.start_byte = 1
        data.sample_count = 1
        data.fall_detect = 1
        data.battery_level = 1
        data.hrConfidence = 1
        data.spo2Confidence = 1
        data.hr = 50
        data.spo2 = 50

        data.motionFlag = True
        data.scdState = 0
        data.activity = 1
        data.walk_steps = 50
        data.run_steps = 50
       

        data.x = 80
        data.y = 80
        data.z = 80
        data.t = 80
        data.h = 80

        data.rssi = -32

        DBManager.db.session.add(data)

        data = SensorData()
        data.FK_bid = 1
        data.start_byte = 1
        data.sample_count = 1
        data.fall_detect = 1
        data.battery_level = 1
        data.hrConfidence = 1
        data.spo2Confidence = 1
        data.hr = 50
        data.spo2 = 50
        
        data.motionFlag = True
        data.scdState = 0
        data.activity = 1
        data.walk_steps = 50
        data.run_steps = 50
       

        data.x = 80
        data.y = 80
        data.z = 80
        data.t = 80
        data.h = 80

        data.rssi = -32     
        DBManager.db.session.add(data)

        data = SensorData()
        data.datetime = '2021-08-18 1:00'
        data.FK_bid = 1
        data.start_byte = 1
        data.sample_count = 1
        data.fall_detect = 1
        data.battery_level = 1
        data.hrConfidence = 1
        data.spo2Confidence = 1
        data.hr = 50
        data.spo2 = 50
        
        data.motionFlag = True
        data.scdState = 0
        data.activity = 1
        data.walk_steps = 50
        data.run_steps = 50
       

        data.x = 80
        data.y = 80
        data.z = 80
        data.t = 80
        data.h = 80

        data.rssi = -32     
        DBManager.db.session.add(data)

        data = SensorData()
        data.datetime = '2021-08-18 1:30'
        data.FK_bid = 1
        data.start_byte = 1
        data.sample_count = 1
        data.fall_detect = 1
        data.battery_level = 1
        data.hrConfidence = 1
        data.spo2Confidence = 1
        data.hr = 75
        data.spo2 = 50
        
        data.motionFlag = True
        data.scdState = 0
        data.activity = 1
        data.walk_steps = 50
        data.run_steps = 50
       

        data.x = 80
        data.y = 80
        data.z = 80
        data.t = 80
        data.h = 80

        data.rssi = -32     
        DBManager.db.session.add(data)

        data = SensorData()
        data.datetime = '2021-08-18 2:00'
        data.FK_bid = 1
        data.start_byte = 1
        data.sample_count = 1
        data.fall_detect = 1
        data.battery_level = 1
        data.hrConfidence = 1
        data.spo2Confidence = 1
        data.hr = 50
        data.spo2 = 50
        
        data.motionFlag = True
        data.scdState = 0
        data.activity = 1
        data.walk_steps = 50
        data.run_steps = 50
       

        data.x = 80
        data.y = 80
        data.z = 80
        data.t = 80
        data.h = 80

        data.rssi = -32     
        DBManager.db.session.add(data)
        DBManager.db.session.commit()
        
    def insert_dummy_event_data():
        from backend.db.table_band import Events
        event = Events()
        event.FK_bid = 1
        event.event = 0
        event.value = -70
        DBManager.db.session.add(event)
        event = Events()
        event.FK_bid = 1
        event.event = 1
        event.value = 70
        DBManager.db.session.add(event)
        event = Events()
        event.FK_bid = 1
        event.event = 2
        event.value = 0
        DBManager.db.session.add(event)      
        event = Events()
        event.FK_bid = 1
        event.event = 3
        event.value = 0
        DBManager.db.session.add(event)   
        event = Events()
        event.FK_bid = 1
        event.event = 4
        event.value = 0
        DBManager.db.session.add(event)  

        from backend.db.table_band import Events
        event = Events()
        event.FK_bid = 2
        event.event = 0
        event.value = -30
        DBManager.db.session.add(event)
        event = Events()
        event.FK_bid = 2
        event.event = 1
        event.value = 50
        DBManager.db.session.add(event)
        event = Events()
        event.FK_bid = 2
        event.event = 2
        event.value = 0
        DBManager.db.session.add(event)      
        event = Events()
        event.FK_bid = 2
        event.event = 3
        event.value = 0
        DBManager.db.session.add(event)  
        event = Events()
        event.FK_bid = 2
        event.event = 4
        event.value = 3
        DBManager.db.session.add(event)          
        DBManager.db.session.commit()