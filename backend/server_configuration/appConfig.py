#!/usr/bin/python
# -*- coding: utf-8 -*-


class DevelopmentConfig():
    BIND_PORT = 8080
    WEB_URL = "http://127.0.0.1"
    SQLALCHEMY_DATABASE_URI = 'mysql://root:p@ssw0rd@127.0.0.1/efwb2'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MQTT_BROKER_URL = "localhost"
    MQTT_BROKER_PORT = 1883


class ProductionConfig():
    BIND_PORT = 8080
    WEB_URL = "http://13.125.45.228/"
    SQLALCHEMY_DATABASE_URI = 'mysql://root:Dtriple11!!@127.0.0.1/efwb'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MQTT_BROKER_URL = "13.125.45.228"
    MQTT_BROKER_PORT = 1883
