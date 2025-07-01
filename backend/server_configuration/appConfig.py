#!/usr/bin/python
# -*- coding: utf-8 -*-
import uuid

class DevelopmentConfig():
    BIND_PORT = 8080
    SQLALCHEMY_DATABASE_URI = 'mysql://root:1234@127.0.0.1:3307/naas'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MQTT_BROKER_URL = "3.37.65.94"
    MQTT_BROKER_PORT = 18831
    MQTT_CLEAN_SESSION = False
    
from urllib.parse import quote_plus

password = quote_plus('p@ssw0rd')
class ProductionConfig():
    BIND_PORT = 5000
    SQLALCHEMY_DATABASE_URI = f'mysql://dbadmin:{password}@127.0.0.1/naas'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MQTT_BROKER_URL = '3.37.65.94'
    MQTT_BROKER_PORT = 18831
    MQTT_USERNAME = 'admin_user'
    MQTT_PASSWORD = 'Psalms23##cross'
    MQTT_CLIENT_ID = 'admin_app_' + str(uuid.uuid4())
    MQTT_CLEAN_SESSION = False