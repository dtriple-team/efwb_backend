#!/usr/bin/python
# -*- coding: utf-8 -*-


class DevelopmentConfig():
    BIND_PORT = 8081
    WEB_URL = "http://127.0.0.1"
    SQLALCHEMY_DATABASE_URI = 'mysql://root:p@ssw0rd@127.0.0.1/efwb2'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MQTT_BROKER_URL = "mj.d-triple.com"
    MQTT_BROKER_PORT = 18831


class ProductionConfig():
    BIND_PORT = 8081
    WEB_URL = "http://210.220.151.77/"
    SQLALCHEMY_DATABASE_URI = 'mysql://dbadmin:p@ssw0rd@127.0.0.1/efwb'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MQTT_BROKER_URL = "mj.d-triple.com"
    MQTT_BROKER_PORT = 18831
