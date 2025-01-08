#!/usr/bin/python
# -*- coding: utf-8 -*-


class DevelopmentConfig():
    BIND_PORT = 8080
    SQLALCHEMY_DATABASE_URI = 'mysql://root:p@ssw0rd@127.0.0.1/efwb2'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MQTT_BROKER_URL = "3.37.65.94"
    MQTT_BROKER_PORT = 18831
    SMS_ID = "stscs"
    SMS_PASSWORD = "rhrorakswhr"

from urllib.parse import quote_plus 
password = quote_plus('p@ssw0rd')
class ProductionConfig():
    BIND_PORT = 8080
    SQLALCHEMY_DATABASE_URI = f'mysql://dbadmin:{password}@127.0.0.1/efwb3'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MQTT_BROKER_URL = "3.37.65.94"
    MQTT_BROKER_PORT = 18831
    MQTT_CLIENT_ID = 'client_app_' + str(uuid.uuid4()) 
    SMS_ID = "stscs"
    SMS_PASSWORD = "rhrorakswhr"
