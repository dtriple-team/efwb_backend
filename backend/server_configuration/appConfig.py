#!/usr/bin/python
# -*- coding: utf-8 -*-


class DevelopmentConfig():
    BIND_PORT = 8080
    SQLALCHEMY_DATABASE_URI = 'mysql://root:p@ssw0rd@127.0.0.1/efwb2'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MQTT_BROKER_URL = "t-vsm.com"
    MQTT_BROKER_PORT = 18831


class ProductionConfig():
    SQLALCHEMY_DATABASE_URI = 'mysql://dbadmin:p@ssw0rd@127.0.0.1/efwb3'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MQTT_BROKER_URL = "t-vsm.com"
    MQTT_BROKER_PORT = 18831
